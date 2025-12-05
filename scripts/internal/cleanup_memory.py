import sqlite3
import argparse
import time
import logging
import sys
import os
import json
from difflib import SequenceMatcher

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "agent_memory.db"

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def cleanup_memory(dry_run=False, min_score=50, duplicate_threshold=0.95):
    if not os.path.exists(DB_PATH):
        logger.error(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {
        "total": 0,
        "low_score": 0,
        "duplicates": 0,
        "errors": 0,
        "deleted": 0
    }
    
    try:
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM memories")
        stats["total"] = cursor.fetchone()[0]
        logger.info(f"Total memories before cleanup: {stats['total']}")
        
        # 1. Remove low score memories
        logger.info(f"Scanning for low score memories (< {min_score})...")
        # Note: 'score' column might not exist in all schemas, check if it exists
        cursor.execute("PRAGMA table_info(memories)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'score' in columns:
            cursor.execute("SELECT id, content, score FROM memories WHERE score < ?", (min_score,))
            low_score_memories = cursor.fetchall()
            stats["low_score"] = len(low_score_memories)
            
            if low_score_memories:
                ids_to_delete = [m[0] for m in low_score_memories]
                if not dry_run:
                    cursor.execute(f"DELETE FROM memories WHERE id IN ({','.join(['?']*len(ids_to_delete))})", ids_to_delete)
                    logger.info(f"Deleted {len(ids_to_delete)} low score memories.")
                else:
                    logger.info(f"[DRY RUN] Would delete {len(ids_to_delete)} low score memories.")
        else:
            logger.warning("'score' column not found in memories table. Skipping low score cleanup.")
        
        # 2. Remove error-only memories (simple heuristic)
        logger.info("Scanning for error-only memories...")
        cursor.execute("SELECT id, content FROM memories WHERE content LIKE '%Error:%' OR content LIKE '%Exception:%'")
        error_memories = cursor.fetchall()
        
        # Filter for short error messages that likely have no value
        ids_to_delete = []
        for mid, content in error_memories:
            if len(content) < 200 and ("Error" in content or "Exception" in content):
                ids_to_delete.append(mid)
        
        stats["errors"] = len(ids_to_delete)
        if ids_to_delete:
            if not dry_run:
                cursor.execute(f"DELETE FROM memories WHERE id IN ({','.join(['?']*len(ids_to_delete))})", ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} error memories.")
            else:
                logger.info(f"[DRY RUN] Would delete {len(ids_to_delete)} error memories.")

        # 3. Remove duplicates (expensive operation!)
        logger.info(f"Scanning for duplicates (> {duplicate_threshold*100}% similarity)...")
        
        duplicate_ids = []
        
        # Fast check for exact duplicates first
        cursor.execute("SELECT content, COUNT(*) as cnt FROM memories GROUP BY content HAVING cnt > 1")
        exact_duplicates = cursor.fetchall()
        
        for row in exact_duplicates:
            content = row[0]
            cursor.execute("SELECT id FROM memories WHERE content = ? ORDER BY id DESC", (content,))
            ids = [r[0] for r in cursor.fetchall()]
            duplicate_ids.extend(ids[1:]) # Keep newest, delete rest
            
        stats["duplicates"] = len(duplicate_ids)
        
        if duplicate_ids:
            if not dry_run:
                cursor.execute(f"DELETE FROM memories WHERE id IN ({','.join(['?']*len(duplicate_ids))})", duplicate_ids)
                logger.info(f"Deleted {len(duplicate_ids)} exact duplicates.")
            else:
                logger.info(f"[DRY RUN] Would delete {len(duplicate_ids)} exact duplicates.")
        
        # Commit
        if not dry_run:
            conn.commit()
            # Vacuum to reclaim space
            logger.info("Vacuuming database...")
            cursor.execute("VACUUM")
            logger.info("Database vacuumed.")
            
        # Final count
        cursor.execute("SELECT COUNT(*) FROM memories")
        final_count = cursor.fetchone()[0]
        stats["deleted"] = stats["total"] - final_count if not dry_run else (stats["low_score"] + stats["errors"] + stats["duplicates"])
        
        logger.info("="*30)
        logger.info("CLEANUP SUMMARY")
        logger.info("="*30)
        logger.info(f"Total Memories: {stats['total']}")
        logger.info(f"Low Score:      {stats['low_score']}")
        logger.info(f"Errors:         {stats['errors']}")
        logger.info(f"Duplicates:     {stats['duplicates']}")
        logger.info("-" * 30)
        logger.info(f"TOTAL DELETED:  {stats['deleted']}")
        logger.info(f"Final Count:    {final_count if not dry_run else stats['total']}")
        logger.info("="*30)

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup agent memory database.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate cleanup without deleting.")
    parser.add_argument("--min-score", type=int, default=50, help="Minimum score to keep (default: 50).")
    parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold for duplicates (default: 0.95).")
    
    args = parser.parse_args()
    
    cleanup_memory(args.dry_run, args.min_score, args.threshold)
