"""
Interactive Memory Manager for AI Agent
Allows viewing and cleaning agent memory database
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the project root directory (two levels up from scripts/internal/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "agent_memory.db")

class MemoryManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"[OK] Connected to database: {self.db_path}\n")
            return True
        except Exception as e:
            print(f"[X] Failed to connect to database: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("\n[OK] Database connection closed")
    
    def show_statistics(self):
        """Show memory statistics"""
        cursor = self.conn.cursor()
        
        # Total memories
        cursor.execute("SELECT COUNT(*) as total FROM memories")
        total = cursor.fetchone()['total']
        
        # By type
        cursor.execute("""
            SELECT json_extract(metadata, '$.type') as type, COUNT(*) as count 
            FROM memories 
            GROUP BY type 
            ORDER BY count DESC
        """)
        types = cursor.fetchall()
        
        # Error memories
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE content LIKE '%Error:%' 
               OR content LIKE '%LLM not available%'
               OR content LIKE '%Failed%'
               OR content LIKE '%failed to%'
        """)
        errors = cursor.fetchone()[0]
        
        # Boredom memories
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE content LIKE '%Boredom:%' 
               OR json_extract(metadata, '$.type') = 'boredom'
        """)
        boredom = cursor.fetchone()[0]
        
        print("=" * 60)
        print("MEMORY STATISTICS")
        print("=" * 60)
        print(f"Total memories: {total}")
        print(f"Error memories: {errors}")
        print(f"Boredom memories: {boredom}")
        print("\nMemories by type:")
        for row in types:
            type_name = row['type'] if row['type'] else '(no type)'
            print(f"  - {type_name}: {row['count']}")
        print("=" * 60)
    
    def show_errors(self, limit=20):
        """Show error memories"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, metadata, created_at 
            FROM memories 
            WHERE content LIKE '%Error:%' 
               OR content LIKE '%LLM not available%'
               OR content LIKE '%Failed%'
               OR content LIKE '%failed to%'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        errors = cursor.fetchall()
        
        if not errors:
            print("\n[OK] No error memories found!")
            return
        
        print(f"\n{'='*60}")
        print(f"ERROR MEMORIES (showing {len(errors)} of {limit} max)")
        print("="*60)
        
        for row in errors:
            print(f"\nID: {row['id']}")
            print(f"Created: {row['created_at']}")
            print(f"Content: {row['content'][:200]}...")
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            print(f"Type: {metadata.get('type', 'N/A')}")
            print("-" * 60)
    
    def show_by_type(self, memory_type, limit=20):
        """Show memories by type"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, metadata, created_at 
            FROM memories 
            WHERE json_extract(metadata, '$.type') = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (memory_type, limit))
        
        memories = cursor.fetchall()
        
        if not memories:
            print(f"\n[OK] No memories found with type '{memory_type}'")
            return
        
        print(f"\n{'='*60}")
        print(f"MEMORIES OF TYPE '{memory_type}' (showing {len(memories)} of {limit} max)")
        print("="*60)
        
        for row in memories:
            print(f"\nID: {row['id']}")
            print(f"Created: {row['created_at']}")
            print(f"Content: {row['content'][:200]}...")
            print("-" * 60)
    
    def show_memory(self, memory_id):
        """Show full memory by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        memory = cursor.fetchone()
        
        if not memory:
            print(f"\n[X] Memory with ID {memory_id} not found")
            return
        
        print(f"\n{'='*60}")
        print(f"MEMORY ID: {memory['id']}")
        print("="*60)
        print(f"Created: {memory['created_at']}")
        print(f"\nContent:\n{memory['content']}")
        print(f"\nMetadata:\n{json.dumps(json.loads(memory['metadata']) if memory['metadata'] else {}, indent=2)}")
        print("="*60)
    
    def delete_errors(self):
        """Delete all error memories"""
        cursor = self.conn.cursor()
        
        # Count first
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE content LIKE '%Error:%' 
               OR content LIKE '%LLM not available%'
               OR content LIKE '%Failed%'
               OR content LIKE '%failed to%'
               OR content LIKE '%not available%'
               OR content LIKE '%ERROR%'
        """)
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n[OK] No error memories to delete")
            return
        
        print(f"\n[!] Found {count} error memories")
        confirm = input("Delete all error memories? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute("""
                DELETE FROM memories 
                WHERE content LIKE '%Error:%' 
                   OR content LIKE '%LLM not available%'
                   OR content LIKE '%Failed%'
                   OR content LIKE '%failed to%'
                   OR content LIKE '%not available%'
                   OR content LIKE '%ERROR%'
            """)
            self.conn.commit()
            print(f"[OK] Deleted {cursor.rowcount} error memories")
        else:
            print("[X] Deletion cancelled")
    
    def delete_boredom(self):
        """Delete boredom memories"""
        cursor = self.conn.cursor()
        
        # Count first
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE content LIKE '%Boredom:%' 
               OR json_extract(metadata, '$.type') = 'boredom'
        """)
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n[OK] No boredom memories to delete")
            return
        
        print(f"\n[!] Found {count} boredom memories")
        confirm = input("Delete all boredom memories? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute("""
                DELETE FROM memories 
                WHERE content LIKE '%Boredom:%' 
                   OR json_extract(metadata, '$.type') = 'boredom'
            """)
            self.conn.commit()
            print(f"[OK] Deleted {cursor.rowcount} boredom memories")
        else:
            print("[X] Deletion cancelled")
    
    def delete_by_type(self, memory_type):
        """Delete memories by type"""
        cursor = self.conn.cursor()
        
        # Count first
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE json_extract(metadata, '$.type') = ?
        """, (memory_type,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"\n[OK] No memories with type '{memory_type}' to delete")
            return
        
        print(f"\n[!] Found {count} memories with type '{memory_type}'")
        confirm = input(f"Delete all '{memory_type}' memories? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute("""
                DELETE FROM memories 
                WHERE json_extract(metadata, '$.type') = ?
            """, (memory_type,))
            self.conn.commit()
            print(f"[OK] Deleted {cursor.rowcount} memories")
        else:
            print("[X] Deletion cancelled")
    
    def delete_by_id(self, memory_id):
        """Delete memory by ID"""
        cursor = self.conn.cursor()
        
        # Show memory first
        self.show_memory(memory_id)
        
        confirm = input(f"\nDelete memory ID {memory_id}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self.conn.commit()
            if cursor.rowcount > 0:
                print(f"[OK] Deleted memory ID {memory_id}")
            else:
                print(f"[X] Memory ID {memory_id} not found")
        else:
            print("[X] Deletion cancelled")
    
    def delete_duplicates(self):
        """Delete duplicate memories (same content)"""
        cursor = self.conn.cursor()
        
        # Find duplicates
        cursor.execute("""
            SELECT content, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM memories
            GROUP BY content
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("\n[OK] No duplicate memories found")
            return
        
        total_dupes = sum(row['count'] - 1 for row in duplicates)
        print(f"\n[!] Found {len(duplicates)} sets of duplicates ({total_dupes} duplicate records)")
        
        for row in duplicates:
            ids = row['ids'].split(',')
            print(f"\nContent: {row['content'][:100]}...")
            print(f"IDs: {', '.join(ids)} ({row['count']} copies)")
        
        confirm = input(f"\nDelete {total_dupes} duplicate memories (keeping oldest)? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            deleted = 0
            for row in duplicates:
                ids = row['ids'].split(',')
                # Keep first (oldest), delete rest
                for id_to_delete in ids[1:]:
                    cursor.execute("DELETE FROM memories WHERE id = ?", (id_to_delete,))
                    deleted += cursor.rowcount
            
            self.conn.commit()
            print(f"[OK] Deleted {deleted} duplicate memories")
        else:
            print("[X] Deletion cancelled")
    
    def search_content(self, search_term, limit=20):
        """Search memories by content"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, content, metadata, created_at 
            FROM memories 
            WHERE content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (f'%{search_term}%', limit))
        
        results = cursor.fetchall()
        
        if not results:
            print(f"\n[OK] No memories found containing '{search_term}'")
            return
        
        print(f"\n{'='*60}")
        print(f"SEARCH RESULTS for '{search_term}' (showing {len(results)} of {limit} max)")
        print("="*60)
        
        for row in results:
            print(f"\nID: {row['id']}")
            print(f"Created: {row['created_at']}")
            print(f"Content: {row['content'][:200]}...")
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            print(f"Type: {metadata.get('type', 'N/A')}")
            print("-" * 60)

def main():
    """Main interactive menu"""
    manager = MemoryManager()
    
    if not manager.connect():
        return
    
    try:
        while True:
            print("\n" + "="*60)
            print("AGENT MEMORY MANAGER")
            print("="*60)
            print("1.  Show statistics")
            print("2.  Show error memories")
            print("3.  Show memories by type")
            print("4.  Show memory by ID")
            print("5.  Search memories")
            print("6.  Delete error memories")
            print("7.  Delete boredom memories")
            print("8.  Delete memories by type")
            print("9.  Delete memory by ID")
            print("10. Delete duplicate memories")
            print("0.  Exit")
            print("="*60)
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                manager.show_statistics()
            
            elif choice == '2':
                limit = input("How many to show? (default 20): ").strip()
                limit = int(limit) if limit else 20
                manager.show_errors(limit)
            
            elif choice == '3':
                memory_type = input("Enter memory type: ").strip()
                limit = input("How many to show? (default 20): ").strip()
                limit = int(limit) if limit else 20
                manager.show_by_type(memory_type, limit)
            
            elif choice == '4':
                memory_id = input("Enter memory ID: ").strip()
                if memory_id.isdigit():
                    manager.show_memory(int(memory_id))
                else:
                    print("[X] Invalid ID")
            
            elif choice == '5':
                search_term = input("Enter search term: ").strip()
                limit = input("How many to show? (default 20): ").strip()
                limit = int(limit) if limit else 20
                manager.search_content(search_term, limit)
            
            elif choice == '6':
                manager.delete_errors()
            
            elif choice == '7':
                manager.delete_boredom()
            
            elif choice == '8':
                memory_type = input("Enter memory type to delete: ").strip()
                manager.delete_by_type(memory_type)
            
            elif choice == '9':
                memory_id = input("Enter memory ID to delete: ").strip()
                if memory_id.isdigit():
                    manager.delete_by_id(int(memory_id))
                else:
                    print("[X] Invalid ID")
            
            elif choice == '10':
                manager.delete_duplicates()
            
            elif choice == '0':
                print("\nExiting...")
                break
            
            else:
                print("[X] Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        manager.close()

if __name__ == "__main__":
    main()
