import sqlite3
import json
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Initializes the SQLite database and extensions."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            
            # Enable WAL mode for robustness
            cursor.execute("PRAGMA journal_mode=WAL;")
            
            # Integrity Check
            try:
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                if result[0] != "ok":
                    raise sqlite3.DatabaseError(f"Integrity check failed: {result[0]}")
            except sqlite3.DatabaseError as e:
                raise e # Re-raise to be caught by outer block
                
        except sqlite3.Error as e:
            logger.critical(f"Database corruption detected during init: {e}")
            if self.conn:
                self.conn.close()
            
            # Try to restore from backup first
            logger.info("Attempting to restore from backup...")
            if self.restore_from_backup():
                logger.info("Successfully restored from backup. Retrying connection...")
                try:
                    self.conn = sqlite3.connect(self.db_path)
                    self.conn.row_factory = sqlite3.Row
                    cursor = self.conn.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    logger.info("Database restored and connected successfully")
                except sqlite3.Error as restore_error:
                    logger.error(f"Restored database is also corrupted: {restore_error}")
                    # Fall through to backup and fresh start
                    if self.conn:
                        self.conn.close()
                    self._backup_corrupted_and_start_fresh()
            else:
                logger.warning("No backup available or restore failed. Starting fresh.")
                self._backup_corrupted_and_start_fresh()

        try:
            cursor = self.conn.cursor()
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Create standard table for text data
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _backup_corrupted_and_start_fresh(self):
        """Backup corrupted database and start fresh."""
        import shutil
        import time
        
        if os.path.exists(self.db_path):
            backup_path = f"{self.db_path}.corrupted.{int(time.time())}"
            shutil.move(self.db_path, backup_path)
            logger.info(f"Moved corrupted database to {backup_path}. Starting fresh.")
        
        # Create new DB
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")

    def is_relevant_memory(self, content: str, metadata: Dict[str, Any] = None) -> (bool, str):
        """Check if memory content is relevant and worth storing.
        
        Args:
            content: Memory content to check
            metadata: Memory metadata
            
        Returns:
            Tuple (is_relevant, reason)
        """
        if not content or len(content.strip()) < 10:
            return False, "Too short (<10 chars)"
        
        content_lower = content.lower()
        
        # Filter Discord debug spam
        discord_spam = [
            'websocket event',
            'keeping shard',
            'dispatching event',
            'socket_event_type',
            'discord.gateway',
            'discord.http',
            'discord.client'
        ]
        if any(spam in content_lower for spam in discord_spam):
            return False, "Discord debug spam"
        
        # Filter error messages and LLM failures
        error_patterns = [
            'llm not available',
            'empty response from ai',
            'error:' if len(content) < 100 else None,  # Allow longer error explanations
            'failed to',
            'exception:',
            'traceback',
            'requested tokens',
            'exceed context window'
        ]
        if any(pattern and pattern in content_lower for pattern in error_patterns):
            return False, "Error message pattern"
        
        # Filter boredom spam
        if 'boredom:' in content_lower and 'context:' in content_lower:
            return False, "Boredom loop spam"
        
        # Filter repetitive tool execution logs (keep only if has meaningful result)
        if content_lower.startswith('tool') and 'executed' in content_lower:
            if 'result:' not in content_lower or len(content) < 50:
                return False, "Tool execution without result"
        
        # Always allow user teachings and high-importance memories
        if metadata:
            mem_type = metadata.get('type', '')
            importance = metadata.get('importance', '')
            
            # 1. Explicitly ignore internal decision processes
            if mem_type == 'autonomous_decision':
                return False, "Autonomous decision (internal)"
            
            # 2. Ignore routine tool executions unless high importance
            if mem_type == 'tool_execution' and importance != 'high':
                return False, "Routine tool execution"
            
            # 3. Allow specific useful types
            allowed_types = ['learning', 'user_teaching', 'important_fact', 'qa_result', 'activity_knowledge']
            
            if mem_type in allowed_types or importance == 'high':
                return True, "Allowed type/importance"
            
            # Fallthrough for unknown metadata types - lenient but noted
            
        return True, "Passed basic filters"
    
    def add_memory(self, content: str, metadata: Dict[str, Any] = None, embedding: List[float] = None):
        """Adds a new memory to the store with advanced relevance filtering and scoring."""
        
        # Helper for memory.log
        def log_to_file(status: str, reason: str):
            try:
                with open("memory.log", "a", encoding="utf-8") as f:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] INPUT: {content} | META: {metadata}\n")
                    f.write(f"           STATUS: {status} ({reason})\n")
            except Exception as e:
                logger.error(f"Failed to write to memory.log: {e}")

        # Import config
        import config_settings
        config = getattr(config_settings, 'MEMORY_CONFIG', {})
        
        # Get config values with defaults
        MIN_SCORE = config.get('MIN_SCORE_TO_SAVE', 70)
        ERROR_PENALTY = config.get('ERROR_PENALTY', -20)
        KEYWORDS = config.get('KEYWORDS', [])
        KEYWORD_BONUS = config.get('KEYWORD_BONUS', 10)
        BLACKLIST = config.get('BLACKLIST', [])
        UNIQUENESS_BONUS = config.get('UNIQUENESS_BONUS', 30)
        UNIQUENESS_THRESHOLD = config.get('UNIQUENESS_THRESHOLD', 0.90)
        
        # Basic relevance check (keep existing logic)
        is_relevant, relevance_reason = self.is_relevant_memory(content, metadata)
        if not is_relevant:
            logger.debug(f"Skipped irrelevant memory: {content[:50]}...")
            log_to_file("REJECTED", f"{relevance_reason}")
            return None
        
        # === ADVANCED SCORING SYSTEM ===
        score = 0
        content_lower = content.lower()
        
        # 1. BLACKLIST CHECK (immediate reject)
        for blacklisted in BLACKLIST:
            if blacklisted.lower() in content_lower:
                logger.debug(f"Memory rejected (blacklist): contains '{blacklisted}' - {content[:50]}...")
                log_to_file("REJECTED", f"Blacklist match: {blacklisted}")
                return None
        
        # 2. ERROR DETECTION
        error_words = ['error', 'exception', 'failed', 'traceback']
        if any(word in content_lower for word in error_words):
            score += ERROR_PENALTY
            logger.debug(f"Error detected, applying penalty: {ERROR_PENALTY} pts")
        
        # 3. KEYWORD MATCHING
        keyword_matches = 0
        for keyword in KEYWORDS:
            if keyword.lower() in content_lower:
                keyword_matches += 1
                score += KEYWORD_BONUS
        
        if keyword_matches > 0:
            logger.debug(f"Keywords matched: {keyword_matches}, bonus: {keyword_matches * KEYWORD_BONUS} pts")
        
        # 4. UNIQUENESS CHECK
        # Use existing search_relevant_memories to check similarity
        try:
            similar_memories = self.search_relevant_memories(content, limit=1)
            
            if similar_memories:
                # Check if too similar (high score = very similar)
                # Since our search returns scored results, we need to calculate similarity
                # For simplicity, if we found matches, assume some similarity
                # In a real implementation, you'd calculate cosine similarity
                is_unique = True  # Assume unique unless proven otherwise
                
                for mem in similar_memories:
                    # Simple heuristic: if search found it with high keyword overlap, it's similar
                    similar_content = mem.get('content', '').lower()
                    
                    # Count matching words
                    content_words = set(content_lower.split())
                    similar_words = set(similar_content.split())
                    
                    if len(content_words) > 0:
                        overlap = len(content_words.intersection(similar_words)) / len(content_words)
                        
                        if overlap > UNIQUENESS_THRESHOLD:
                            is_unique = False
                            logger.debug(f"Similar memory found (overlap: {overlap:.2%}), not unique")
                            break
                
                if is_unique:
                    score += UNIQUENESS_BONUS
                    logger.debug(f"Content is unique, bonus: {UNIQUENESS_BONUS} pts")
            else:
                # No similar memories found, definitely unique
                score += UNIQUENESS_BONUS
                logger.debug(f"No similar memories, content is unique, bonus: {UNIQUENESS_BONUS} pts")
                
        except Exception as e:
            logger.error(f"Uniqueness check failed: {e}")
            # On error, give benefit of doubt
            score += UNIQUENESS_BONUS
        
        # 5. FINAL DECISION
        logger.info(f"Memory scoring complete: {score} pts (threshold: {MIN_SCORE})")
        
        if score < MIN_SCORE:
            logger.info(f"Memory rejected (low score {score} < {MIN_SCORE}): {content[:50]}...")
            log_to_file("REJECTED", f"Low Score: {score}/{MIN_SCORE}")
            return None
        
        # Score is sufficient, proceed with saving
        logger.info(f"Memory accepted (score: {score}), saving...")
        
        # Truncate very long content (keep first 500 chars)
        if len(content) > 500:
            original_len = len(content)
            content = content[:500] + "..."
            logger.debug(f"Truncated memory from {original_len} to 500 chars")
        
        try:
            cursor = self.conn.cursor()
            meta_json = json.dumps(metadata) if metadata else "{}"
            
            cursor.execute(
                "INSERT INTO memories (content, metadata) VALUES (?, ?)",
                (content, meta_json)
            )
            memory_id = cursor.lastrowid
            
            # TODO: Insert embedding into vector table if extension is loaded
            # if embedding:
            #     cursor.execute("INSERT INTO vss_memories(rowid, vector) VALUES (?, ?)", (memory_id, json.dumps(embedding)))
            
            self.conn.commit()
            logger.info(f"Added memory ID {memory_id} (score: {score}): {content[:50]}...")
            log_to_file("SAVED", f"ID: {memory_id}, Score: {score}")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            log_to_file("ERROR", f"DB Exception: {e}")
            return None

    def create_backup(self) -> bool:
        """Creates a backup of the database in the backup/ folder."""
        try:
            import shutil
            import time
            import glob
            
            # Check database integrity before backup
            if not os.path.exists(self.db_path):
                logger.warning(f"Database file not found: {self.db_path}")
                return False
            
            try:
                cursor = self.conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                if result[0] != "ok":
                    logger.error(f"Database integrity check failed: {result[0]}. Skipping backup.")
                    return False
            except sqlite3.Error as e:
                logger.error(f"Database integrity check failed: {e}. Skipping backup.")
                return False
            
            # Ensure backup directory exists
            backup_dir = "backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = int(time.time())
            backup_path = os.path.join(backup_dir, f"agent_memory_{timestamp}.db")
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            
            # Clean up old backups (keep only 10 most recent)
            backups = sorted(glob.glob(os.path.join(backup_dir, "agent_memory_*.db")))
            if len(backups) > 10:
                # Delete oldest backups
                for old_backup in backups[:-10]:
                    os.remove(old_backup)
                    logger.info(f"Deleted old backup: {old_backup}")
            
            return True
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_from_backup(self) -> bool:
        """Restores database from the most recent backup."""
        try:
            import shutil
            import glob
            
            backup_dir = "backup"
            if not os.path.exists(backup_dir):
                logger.warning("No backup directory found")
                return False
            
            # Find all backups
            backups = sorted(glob.glob(os.path.join(backup_dir, "agent_memory_*.db")))
            if not backups:
                logger.warning("No backups found")
                return False
            
            # Get most recent backup
            latest_backup = backups[-1]
            logger.info(f"Restoring from backup: {latest_backup}")
            
            # Copy backup to main location
            shutil.copy2(latest_backup, self.db_path)
            logger.info(f"Database restored from backup: {latest_backup}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def search_memory(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for similar memories."""
        # TODO: Implement vector search using sqlite-vss
        # For now, return empty list or implement basic keyword search
        logger.warning("Vector search not yet implemented (waiting for extension).")
        return []
    
    def get_relevant_memories(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Alias for search_relevant_memories to prevent AttributeError."""
        return self.search_relevant_memories(*args, **kwargs)

    def search_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for relevant memories based on keyword matching.
        
        Args:
            query: Search query string
            limit: Maximum number of memories to return
            
        Returns:
            List of most relevant memories sorted by relevance score
        """
        if not self.conn:
            logger.error("Database connection not initialized")
            return []
        
        try:
            # Get all memories
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, content, metadata, created_at 
                FROM memories 
                ORDER BY created_at DESC 
                LIMIT 500
            """)
            
            all_memories = []
            for row in cursor.fetchall():
                all_memories.append({
                    'id': row[0],
                    'content': row[1],
                    'metadata': json.loads(row[2]) if row[2] else {},
                    'created_at': row[3]
                })
            
            if not all_memories:
                return []
            
            # Calculate relevance scores using keyword matching
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            scored_memories = []
            for memory in all_memories:
                content_lower = memory['content'].lower()
                
                # Calculate score based on:
                # 1. Number of matching words
                # 2. Exact phrase match (bonus)
                # 3. Word proximity (bonus if words appear close together)
                
                score = 0
                
                # Count matching words
                content_words = set(content_lower.split())
                matching_words = query_words.intersection(content_words)
                score += len(matching_words) * 2
                
                # Bonus for exact phrase match
                if query_lower in content_lower:
                    score += 10
                
                # Bonus for partial phrase matches
                for word in query_words:
                    if len(word) > 3 and word in content_lower:
                        score += 1
                
                # If score > 0, add to results
                if score > 0:
                    scored_memories.append((score, memory))
            
            # Sort by score (descending) and return top results
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            return [mem for score, mem in scored_memories[:limit]]
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the most recent memories."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to retrieve recent memories: {e}")
            return []
    
    def count_memories_by_type(self, memory_type: str) -> int:
        """Count memories by their metadata type."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM memories WHERE json_extract(metadata, '$.type') = ?",
                (memory_type,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Failed to count memories by type: {e}")
            return 0

    def delete_boredom_memories(self) -> int:
        """Deletes memories related to boredom."""
        try:
            cursor = self.conn.cursor()
            # Delete where content contains "Boredom:" or metadata contains "boredom"
            cursor.execute(
                "DELETE FROM memories WHERE content LIKE '%Boredom:%' OR json_extract(metadata, '$.type') = 'boredom'"
            )
            deleted_count = cursor.rowcount
            self.conn.commit()
            logger.info(f"Deleted {deleted_count} boredom-related memories.")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete boredom memories: {e}")
            return 0
    
    def delete_error_memories(self) -> int:
        """Deletes memories with errors like 'LLM not available' and similar unwanted content."""
        try:
            cursor = self.conn.cursor()
            # Delete memories containing error messages
            error_patterns = [
                '%LLM not available%',
                '%not available%',
                '%failed to%',
                '%error%',
                '%Error%',
                '%ERROR%'
            ]
            
            total_deleted = 0
            for pattern in error_patterns:
                cursor.execute("DELETE FROM memories WHERE content LIKE ?", (pattern,))
                total_deleted += cursor.rowcount
            
            self.conn.commit()
            logger.info(f"Deleted {total_deleted} error-related memories.")
            return total_deleted
        except Exception as e:
            logger.error(f"Failed to delete error memories: {e}")
            return 0
    
    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
