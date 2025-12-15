# Paměťový Systém (Memory System)

> **Navigace:** [📂 Dokumentace](../README.md) | [🧠 Core](../README.md#core-jádro) | [Paměťový systém](memory-system.md)

> VectorStore a správa vzpomínek agenta.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Agent používá SQLite databázi s FTS5 (Full-Text Search) pro ukládání a vyhledávání vzpomínek. **Nově** obsahuje systém pro inteligentní filtrování a scoring vzpomínek.

<a name="intelligent-memory-filtering"></a>
### 🧠 Intelligent Memory Filtering
Před vlastním scoringem probíhá **pre-processing** pomocí LLM (metoda `add_filtered_memory` v `AutonomousAgent`).
- **Cíl**: Odstranit balast ("fluff"), konverzační výplň a zachovat pouze faktickou podstatu.
- **Použití**: `WebTool` (obsah stránek), `DiscordActivityTool` (popis aktivit), `!teach` (uživatelské učení).
- **Výsledek**: Do databáze se dostane pouze kondenzovaná informace.

---

<a name="vectorstore-class"></a>
## VectorStore Class

<a name="inicializace"></a>
### 🔧 Inicializace

```python
from agent.memory import VectorStore

memory = VectorStore(db_path="agent_memory.db")
```

<a name="databázové-schema"></a>
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

<a name="adding-memories"></a>

<a name="přidávání-vzpomínek"></a>
## Přidávání Vzpomínek

<a name="add_memory"></a>
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

<a name="advanced-scoring-system-new"></a>
### ⭐ Advanced Scoring System (NEW!)

Agent používá **pokročilý scoring systém** pro rozhodování, které vzpomínky ukládat.

<a name="konfigurace"></a>
#### Konfigurace

Parametry v `config_settings.py`:

```python
MEMORY_CONFIG = {
    'MIN_SCORE_TO_SAVE': 70,        # Minimální skóre pro uložení
    'ERROR_PENALTY': -20,            # Penalizace za error slova
    'KEYWORD_BONUS': 10,             # Bonus za každé klíčové slovo
    'UNIQUENESS_BONUS': 30,          # Bonus pokud je vzpomínka unikátní
    'UNIQUENESS_THRESHOLD': 0.90,    # Práh pro považování za duplicitu (90%)
    'KEYWORDS': [                    # Důležitá klíčová slova
        'python', 'discord', 'tool', 'learned', 'user', 
        'command', 'function', 'error', 'fix', 'create'
    ],
    'BLACKLIST': [                   # Okamžité zamítnutí
        'discord.gateway', 'discord.client', 'Keep Alive',
        'WebSocket', 'Heartbeat'
    ]
}
```

<a name="scoring-process-5-kroků"></a>
#### Scoring Process (5 kroků)

**1. Blacklist Check** → Okamžité zamítnutí

```python
BLACKLIST = ['discord.gateway', 'WebSocket Event', ...]

if any(blacklisted in content.lower() for blacklisted in BLACKLIST):
    logger.debug(f"Memory rejected (blacklist): {content[:50]}...")
    return None  # Není uloženo
```

**2. Error Detection** → -20 bodů

```python
error_words = ['error', 'exception', 'failed', 'traceback']
if any(word in content_lower for word in error_words):
    score += ERROR_PENALTY  # -20 bodů
    logger.debug(f"Error detected, penalty: -20 pts")
```

**3. Keyword Matching** → +10 bodů za každé keyword

```python
KEYWORDS = ['python', 'discord', 'tool', 'learned', ...]

keyword_matches = 0
for keyword in KEYWORDS:
    if keyword.lower() in content_lower:
        keyword_matches += 1
        score += KEYWORD_BONUS  # +10

logger.debug(f"Keywords matched: {keyword_matches}, bonus: +{keyword_matches * 10} pts")
```

**4. Uniqueness Check** → +30 bodů pokud unikátní

```python
# Porovná s existujícími vzpomínkami
similar_memories = self.search_relevant_memories(content, limit=1)

for mem in similar_memories:
    # Vypočítá word overlap
    content_words = set(content_lower.split())
    similar_words = set(mem['content'].lower().split())
    
    overlap = len(content_words.intersection(similar_words)) / len(content_words)
    
    if overlap > UNIQUENESS_THRESHOLD:  # > 90%
        is_unique = False
        logger.debug(f"Similar memory found (overlap: {overlap:.0%}), not unique")
        break

if is_unique:
    score += UNIQUENESS_BONUS  # +30 bodů
```

**5. Final Decision** → Uložit pokud `score >= MIN_SCORE`

```python
MIN_SCORE_TO_SAVE = 70

if score >= MIN_SCORE_TO_SAVE:
    logger.info(f"Memory accepted (score: {score}), saving...")
    # Save to database
else:
    logger.info(f"Memory rejected (low score {score} < {MIN_SCORE_TO_SAVE})")
    return None
```

<a name="příklady-scoring"></a>
#### Příklady Scoring

**Příklad 1: Zamítnutá vzpomínka**

```
Content: "Learned to use web_tool for searching Python documentation"

1. Blacklist: None ✓
2. Errors: None → 0 pts
3. Keywords: 'learned' (+10), 'tool' (+10), 'python' (+10) → +30 pts
4. Uniqueness: Podobná vzpomínka existuje → 0 pts
5. Total Score: 30 pts

Decision: ❌ REJECTED (30 < 70)
```

**Příklad 2: Přijatá vzpomínka**

```
Content: "User taught me: Discord bots can use slash commands with discord.py"

1. Blacklist: None ✓
2. Errors: None → 0 pts
3. Keywords: 'discord' (+10), 'command' (+10), 'python' (+10) → +30 pts  
4. Uniqueness: Unikátní → +30 pts
5. Total Score: 60 pts

Decision: ❌ REJECTED (60 < 70)

⚠️ Ale 'user_teaching' metadata → BYPASS scoring! ✅ SAVED
```

**Příklad 3: High-score vzpomínka**

```
Content: "Successfully created Python function to fix Discord command parsing error"

1. Blacklist: None ✓
2. Errors: 'error' → -20 pts
3. Keywords: 'python' (+10), 'function' (+10), 'fix' (+10), 
             'discord' (+10), 'command' (+10) → +50 pts
4. Uniqueness: Unikátní → +30 pts
5. Total Score: 60 pts (-20 + 50 + 30)

Decision: ❌ REJECTED (60 < 70)
```

<a name="scoring-bypass"></a>
### 🔓 Scoring Bypass

**Některé typy vzpomínek VŽDY projdou bez ohledu na skóre:**

```python
metadata = {
    "type": "user_teaching",  # !teach příkaz
    "importance": "high"       # Vysoká důležitost
}
```

**Bypass typy:**
- `!teach` příkaz → `type: "user_teaching"` → **Vždy uloženo**
- `importance: "high"` → **Vždy uloženo**
- Admin metadata → **Vždy uloženo**

**Implementace v `!teach`:**

```python
async def cmd_teach(self, channel_id: int, info: str):
    # !teach VŽDY uloží bez scoring check
    self.agent.memory.add_memory(
        content=f"User taught me: {info}",
        metadata={"type": "user_teaching", "importance": "high"}
    )
```

⚠️ **Poznámka:** `user_teaching` typ dostává bypass, protože uživatelské učení je vždy cenné.

<a name="basic-relevance-filter-pre-scoring"></a>
### 💡 Basic Relevance Filter (Pre-Scoring)

Před scoring systémem běží **basic filter**:

```python
def is_relevant_memory(self, content: str, metadata: dict = None) -> bool:
    """Check if memory content is relevant (runs BEFORE scoring)."""
    
    # Skip if too short
    if len(content.strip()) < 10:
        return False
    
    # Skip obvious spam
    spam_patterns = [
        "LLM not available",
        "boredom",
        "waiting",
        "checking"
    ]
    
    content_lower = content.lower()
    if any(pattern in content_lower for pattern in spam_patterns):
        return False
    
    # Skip internal memories
    if metadata and metadata.get("type") == "internal":
        return False
    
    return True
```

**Tento basic filter běží PŘED scoring systémem a rychle odfiltruje spam.**

---

<a name="searching-memories"></a>

<a name="vyhledávání-vzpomínek"></a>
## Vyhledávání Vzpomínek

<a name="search_relevant_memories"></a>
### 🔍 search_relevant_memories()

Používá FTS5 pro keyword-based search:

```python
memories = memory.search_relevant_memories(
    query="Python programming",
    limit=5
)
```

<a name="implementace"></a>
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

<a name="search-scoring"></a>
### 📊 Search Scoring

Skóre = počet matching keywords v content.

---

<a name="getting-recent-memories"></a>

<a name="získání-nedávných-vzpomínek"></a>
## Získání Nedávných Vzpomínek

<a name="get_recent_memories"></a>
### 🔧 get_recent_memories()

```python
recent = memory.get_recent_memories(limit=10)
```

Vrací posledních N vzpomínek seřazených podle timestamp.

---

<a name="memory-management"></a>

<a name="správa-paměti"></a>
## Správa Paměti

<a name="delete_boredom_memories"></a>
### 🗑️ delete_boredom_memories()

Vymaže vzpomínky související s nudou:

```python
memory.delete_boredom_memories()
```

```sql
DELETE FROM memories 
WHERE content LIKE '%Boredom:%' 
   OR json_extract(metadata, '$.type') = 'boredom'
```

<a name="delete_error_memories"></a>
### 🗑️ delete_error_memories()

Vymaže chybové vzpomínky:

```python
memory.delete_error_memories()
```

```sql
DELETE FROM memories 
WHERE content LIKE '%Error%' 
   OR content LIKE '%LLM not available%'
```

---

<a name="backup-restore"></a>
## Backup & Restore

<a name="create_backup"></a>
### 💾 create_backup()

```python
memory.create_backup()
```

Vytvoří kopii databáze:
```
backup/agent_memory_20251203_230000.db
```

<a name="restore_from_backup"></a>
### 🔄 restore_from_backup()

```python
memory.restore_from_backup()
```

Obnoví z nejnovější zálohy.

---

<a name="metadata-types"></a>
## Metadata Types

<a name="standardní-typy"></a>
### 📝 Standardní Typy

| Type | Popis | Scoring Bypass | Příklad |
|------|-------|----------------|---------|
| `learning` | Naučená věc | ❌ Ne | "Learned web_tool" |
| `action` | Provedená akce | ❌ Ne | "Searched for Python" |
| `user_teaching` | Od uživatele (`!teach`) | ✅ **Ano** | "Python is a language" |
| `conversation` | Z konverzace | ❌ Ne | "User asked about weather" |
| `discovery` | Objevená aktivita | ❌ Ne | "Discovered Minecraft" |
| `internal` | Interní (pre-filtered) | N/A | "Boredom check" |

<a name="příklad-metadata"></a>
### 🔧 Příklad Metadata

```json
{
  "type": "user_teaching",
  "importance": "high",
  "source": "!teach_command",
  "timestamp": 1733257523.45,
  "user_id": 123456789
}
```

---

<a name="statistics"></a>

<a name="statistiky"></a>
## Statistiky

<a name="count_memories_by_type"></a>
### 📊 count_memories_by_type()

```python
learning_count = memory.count_memories_by_type("learning")
teaching_count = memory.count_memories_by_type("user_teaching")
```

```sql
SELECT COUNT(*) FROM memories 
WHERE json_extract(metadata, '$.type') = ?
```

---

<a name="database-optimization"></a>

<a name="database-optimalizace"></a>
## Database Optimalizace

<a name="pragma-settings"></a>
### 🔧 PRAGMA Settings

```python
conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
conn.execute("PRAGMA foreign_keys=ON")
```

<a name="výhody"></a>
### 📊 Výhody

- **WAL Mode** - Lepší concurrency, rychlejší zápisy
- **Foreign Keys** - Integrita dat (pokud jsou relace)

---

<a name="corrupted-database-handling"></a>
## Corrupted Database Handling

<a name="auto-recovery"></a>
### ⚠️ Auto-Recovery

```python
def _initialize_db(self):
    try:
        # Try to open database
        self.conn = sqlite3.connect(self.db_path)
        # Integrity check
        self.conn.execute("PRAGMA integrity_check")
    except sqlite3.DatabaseError:
        logger.error("Database corrupted! Auto-recovering...")
        self._backup_corrupted_and_start_fresh()
```

<a name="recovery-process"></a>
### 🔄 Recovery Process

1. Přejmenuj corrupted DB na `.corrupted`
2. Vytvoř novou prázdnou databázi
3. Inicializuj schema
4. Loguj warning pro admina


<a name="debug-logging"></a>
### 🐛 Debug Logging

Všechny pokusy o zápis do paměti jsou detailně logovány do souboru `memory.log` s důrazem na důvod přijetí či zamítnutí.

- **Účel:** Debugging scoring algoritmu a kontrola filtrování.
- **Formát:**
  - **Řádek 1 (INPUT):** Timestamp, Raw content, Metadata
  - **Řádek 2 (STATUS):** Výsledek operace (SAVED/REJECTED) a konkrétní důvod.

**Příklady výstupu:**

```text
[2025-12-08 22:45:01] INPUT: Python code example... | META: {'type': 'learning'}
           STATUS: SAVED (ID: 158, Score: 85)

[2025-12-08 22:45:05] INPUT: Boredom: checking... | META: {}
           STATUS: REJECTED (Boredom loop spam)

[2025-12-08 22:45:10] INPUT: Hello world | META: {}
           STATUS: REJECTED (Low Score: 20/70)
```

---

<a name="integration-with-agent"></a>

<a name="integration-s-agentem"></a>
## Integration s Agentem

<a name="v-corepy"></a>
### 🔧 V core.py

```python
# Initialize memory
self.memory = VectorStore()

# Add memory using Intelligent Filtering (for big content)
if hasattr(self, 'add_filtered_memory'):
    await self.add_filtered_memory(
        content=raw_web_content,
        metadata={"type": "web_knowledge", "source": url}
    )

# Add user teaching (uses filtered memory + special metadata)
await self.add_filtered_memory(
    content=info,
    metadata={
        "type": "user_teaching", 
        "importance": "high",
        "taught_by_user": True
    }
)

# Search for relevant context
memories = self.memory.search_relevant_memories(question, limit=5)
context = "\n".join([m['content'] for m in memories])
```

---

<a name="související"></a>
## 🔗 Související

- [📖 Autonomous Behavior](autonomous-behavior.md) - Jak agent používá paměť pro rozhodování
- [`!memory`](../commands/data-management.md#memory) - Příkaz pro statistiky
- [`!export memory`](../commands/data-management.md#export) - Export paměti
- [`!teach`](../commands/tools-learning.md#teach) - Učení agenta (bypass scoring)
- [📚 API Reference](../api/memory-system.md) - Technická dokumentace tříd a metod
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
