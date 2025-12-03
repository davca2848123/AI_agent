# Paměťový Systém (Memory System)

> VectorStore a správa vzpomínek agenta

## 📋 Přehled

Agent používá SQLite databázi s FTS5 (Full-Text Search) pro ukládání a vyhledávání vzpomínek.

---

## VectorStore Class

### 🔧 Inicializace

```python
from agent.memory import VectorStore

memory = VectorStore(db_path="agent_memory.db")
```

### 📊 Databázové Schema

```sql
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON
    timestamp REAL,
    embedding TEXT  -- JSON array (not currently used)
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
USING fts5(content, content=memories, content_rowid=id);
```

---

## Přidávání Vzpomínek

### 🔧 add_memory()

```python
memory.add_memory(
    content="Learned to use web_tool for searching",
    metadata={
        "type": "learning",
        "tool": "web_tool",
        "timestamp": time.time()
    }
)
```

### 💡 Relevance Filtering

Ne všechny vzpomínky stojí za uložení. Systém filtruje:

```python
def is_relevant_memory(self, content: str, metadata: dict = None) -> bool:
    """Check if memory content is relevant and worth storing."""
    
    # Skip if too short
    if len(content.strip()) < 10:
        return False
    
    # Skip spam patterns
    spam_patterns = [
        "LLM not available",
        "Error:",
        "boredom",
        "waiting",
        "checking"
    ]
    
    content_lower = content.lower()
    if any(pattern in content_lower for pattern in spam_patterns):
        return False
    
    # Skip if metadata marks it as irrelevant
    if metadata and metadata.get("type") == "internal":
        return False
    
    return True
```

---

## Vyhledávání Vzpomínek

### 🔍 search_relevant_memories()

Používá FTS5 pro keyword-based search:

```python
memories = memory.search_relevant_memories(
    query="Python programming",
    limit=5
)
```

### 🔧 Implementace

```python
def search_relevant_memories(self, query: str, limit: int = 5):
    """Search using FTS5 keyword matching."""
    
    # Extract keywords
    keywords = [w for w in query.lower().split() if len(w) > 2]
    
    if not keywords:
        return self.get_recent_memories(limit)
    
    # Build FTS5 query
    fts_query = " OR ".join(keywords)
    
    cursor.execute("""
        SELECT m.id, m.content, m.metadata, m.timestamp
        FROM memories_fts fts
        JOIN memories m ON fts.rowid = m.id
        WHERE memories_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (fts_query, limit * 2))
    
    # Score and sort results
    results = []
    for row in cursor.fetchall():
        score = sum(1 for kw in keywords if kw in row[1].lower())
        results.append({
            "id": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else {},
            "timestamp": row[3],
            "score": score
        })
    
    # Sort by score and return top N
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]
```

### 📊 Scoring

Skóre = počet matching keywords v content.

---

## Získání Nedávných Vzpomínek

### 🔧 get_recent_memories()

```python
recent = memory.get_recent_memories(limit=10)
```

Vrací posledních N vzpomínek seřazených podle timestamp.

---

## Správa Paměti

### 🗑️ delete_boredom_memories()

Vymaže vzpomínky související s nudou:

```python
memory.delete_boredom_memories()
```

```sql
DELETE FROM memories 
WHERE content LIKE '%boredom%' 
   OR content LIKE '%waiting%'
```

### 🗑️ delete_error_memories()

Vymaže chybové vzpomínky:

```python
memory.delete_error_memories()
```

```sql
DELETE FROM memories 
WHERE content LIKE '%Error:%' 
   OR content LIKE '%LLM not available%'
```

---

## Backup & Restore

### 💾 create_backup()

```python
memory.create_backup()
```

Vytvoří kopii databáze:
```
backup/agent_memory_20251202_130500.db
```

### 🔄 restore_from_backup()

```python
memory.restore_from_backup()
```

Obnoví z nejnovějšího zálohy.

---

## Metadata Types

### 📝 Standardní Typy

| Type | Popis | Příklad |
|------|-------|---------|
| `learning` | Naučená věc | "Learned web_tool" |
| `action` | Provedená akce | "Searched for Python" |
| `user_teaching` | Od uživatele (`!teach`) | "Python is a language" |
| `conversation` | Z konverzace | "User asked about weather" |
| `discovery` | Objevená aktivita | "Discovered Minecraft game" |
| `internal` | Interní (neukládá se) | "Boredom check" |

### 🔧 Příklad Metadata

```json
{
  "type": "learning",
  "tool": "web_tool",
  "source": "autonomous_action",
  "timestamp": 1733140123.45,
  "user_id": 123456789
}
```

---

## Statistiky

### 📊 count_memories_by_type()

```python
learning_count = memory.count_memories_by_type("learning")
```

```sql
SELECT COUNT(*) FROM memories 
WHERE json_extract(metadata, '$.type') = ?
```

---

## Database Optimalizace

### 🔧 PRAGMA Settings

```python
conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=10000")
conn.execute("PRAGMA temp_store=MEMORY")
```

### 📊 Výhody

- **WAL Mode** - Lepší concurrency, rychlejší zápisy
- **Cache** - Méně disk I/O
- **Temp Memory** - Rychlejší temporary operace

---

## Corrupted Database Handling

### ⚠️ Auto-Recovery

```python
def _initialize_db(self):
    try:
        # Try to open database
        self.conn = sqlite3.connect(self.db_path)
        # Test connection
        self.conn.execute("SELECT 1")
    except sqlite3.DatabaseError:
        logger.error("Database corrupted! Auto-recovering...")
        self._backup_corrupted_and_start_fresh()
```

### 🔄 Recovery Process

1. Přejmenuj corrupted DB na `.corrupted`
2. Vytvoř novou prázdnou databázi
3. Inicializuj schema
4. Loguj warning pro admina

---

## Integration s Agentem

### 🔧 V core.py

```python
# Initialize memory
self.memory = VectorStore()

# Add memory during actions
self.memory.add_memory(
    content=f"Used {tool_name}: {result}",
    metadata={"type": "action", "tool": tool_name}
)

# Search for relevant context
memories = self.memory.search_relevant_memories(question, limit=5)
context = "\n".join([m['content'] for m in memories])
```

---

## 🔗 Související

- [Autonomous Behavior](autonomous-behavior.md) - Jak agent používá paměť pro rozhodování
- [`!memory`](../commands/data-management.md#memory) - Příkaz pro statistiky
- [`!export memory`](../commands/data-management.md#export) - Export paměti

---

**Poslední aktualizace:** 2025-12-02  
**Verze:** 1.0.0
