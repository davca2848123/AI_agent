#!/usr/bin/env python3
"""
Memory Cleanup Script
Analyzuje a čistí databázi memories od nerelevantních záznamů.
Použití: python3 scripts/cleanup_memory.py [--dry-run] [--backup]
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

# Filter patterns (stejné jako v memory.py)
DISCORD_SPAM = [
    'websocket event',
    'keeping shard',
    'dispatching event',
    'socket_event_type',
    'discord.gateway',
    'discord.http',
    'discord.client'
]

ERROR_PATTERNS = [
    'llm not available',
    'empty response from ai',
    'failed to',
    'exception:',
    'traceback',
    'requested tokens',
    'exceed context window'
]

BOREDOM_SPAM = ['boredom:', 'context:']

def should_delete(content: str, metadata: dict) -> tuple[bool, str]:
    """Určí zda memory smazat a z jakého důvodu."""
    
    if not content or len(content.strip()) < 10:
        return True, "too_short"
    
    content_lower = content.lower()
    
    # Check metadata importance first
    mem_type = metadata.get('type', '')
    importance = metadata.get('importance', '')
    
    # Never delete important memories
    if mem_type in ['user_teaching', 'learning'] or importance == 'high':
        return False, "important"
    
    # Discord spam
    if any(spam in content_lower for spam in DISCORD_SPAM):
        return True, "discord_spam"
    
    # Error messages
    if any(pattern in content_lower for pattern in ERROR_PATTERNS):
        return True, "error_log"
    
    # Boredom spam
    if all(pattern in content_lower for pattern in BOREDOM_SPAM):
        return True, "boredom_spam"
    
    # Repetitive tool logs without results
    if content_lower.startswith('tool') and 'executed' in content_lower:
        if 'result:' not in content_lower or len(content) < 50:
            return True, "empty_tool_log"
    
    return False, "keep"

def should_truncate(content: str) -> bool:
    """Určí zda memory zkrátit."""
    return len(content) > 500

def analyze_database(db_path: str = "agent_memory.db"):
    """Analyzuje databázi a vrátí statistiky."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, content, metadata FROM memories")
    rows = cursor.fetchall()
    
    stats = {
        'total': len(rows),
        'to_delete': 0,
        'to_truncate': 0,
        'keep': 0,
        'delete_reasons': {},
        'avg_length': 0,
        'max_length': 0
    }
    
    total_length = 0
    
    for row in rows:
        mem_id, content, meta_json = row
        metadata = json.loads(meta_json) if meta_json else {}
        
        should_del, reason = should_delete(content, metadata)
        
        if should_del:
            stats['to_delete'] += 1
            stats['delete_reasons'][reason] = stats['delete_reasons'].get(reason, 0) + 1
        else:
            if should_truncate(content):
                stats['to_truncate'] += 1
            stats['keep'] += 1
        
        total_length += len(content)
        stats['max_length'] = max(stats['max_length'], len(content))
    
    stats['avg_length'] = total_length / len(rows) if rows else 0
    
    conn.close()
    return stats

def cleanup_database(db_path: str = "agent_memory.db", dry_run: bool = False):
    """Vyčistímemorií databázi."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, content, metadata FROM memories")
    rows = cursor.fetchall()
    
    deleted = 0
    truncated = 0
    
    for row in rows:
        mem_id, content, meta_json = row
        metadata = json.loads(meta_json) if meta_json else {}
        
        should_del, reason = should_delete(content, metadata)
        
        if should_del:
            if not dry_run:
                cursor.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
            deleted += 1
            print(f"[DELETE] ID {mem_id}: {reason} - {content[:60]}...")
            
        elif should_truncate(content):
            new_content = content[:500] + "..."
            if not dry_run:
                cursor.execute("UPDATE memories SET content = ? WHERE id = ?", (new_content, mem_id))
            truncated += 1
            print(f"[TRUNCATE] ID {mem_id}: {len(content)} → 500 chars")
    
    if not dry_run:
        conn.commit()
    
    conn.close()
    
    return deleted, truncated

def create_backup(db_path: str = "agent_memory.db"):
    """Vytvoří zálohu databáze."""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"agent_memory_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def main():
    """Hlavní funkce."""
    
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    do_backup = '--backup' in sys.argv
    db_path = "agent_memory.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("MEMORY DATABASE CLEANUP SCRIPT")
    print("=" * 60)
    print()
    
    # Analyze first
    print("📊 Analyzing database...")
    stats = analyze_database(db_path)
    
    print(f"\n📈 Statistics:")
    print(f"  Total memories: {stats['total']}")
    print(f"  To delete: {stats['to_delete']} ({stats['to_delete']/stats['total']*100:.1f}%)")
    print(f"  To truncate: {stats['to_truncate']}")
    print(f"  To keep: {stats['keep']}")
    print(f"  Avg length: {stats['avg_length']:.0f} chars")
    print(f"  Max length: {stats['max_length']} chars")
    
    print(f"\n🗑️  Delete reasons:")
    for reason, count in stats['delete_reasons'].items():
        print(f"  {reason}: {count}")
    
    print()
    
    # Confirm
    if not dry_run:
        if do_backup:
            create_backup(db_path)
        
        print(f"⚠️  This will DELETE {stats['to_delete']} memories and TRUNCATE {stats['to_truncate']}.")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            sys.exit(0)
    else:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    # Execute cleanup
    print("\n🧹 Cleaning up...")
    deleted, truncated = cleanup_database(db_path, dry_run=dry_run)
    
    print()
    print("=" * 60)
    print("✅ CLEANUP COMPLETE")
    print("=" * 60)
    print(f"Deleted: {deleted} memories")
    print(f"Truncated: {truncated} memories")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTED'}")
    
    if dry_run:
        print("\nℹ️  Run without --dry-run to actually apply changes")
        print("ℹ️  Use --backup to create a backup before cleanup")

if __name__ == "__main__":
    main()
