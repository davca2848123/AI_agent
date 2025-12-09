# 🧠 Memory System API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Memory System](memory-system.md)

Dokumentace pro `VectorStore` v `agent/memory.py`.

<a name="přehled"></a>
## 📋 Přehled

`VectorStore` zajišťuje dlouhodobou paměť agenta pomocí SQLite databáze s podporou vektorového vyhledávání (pokud je dostupné) a fulltextového vyhledávání (FTS5).

<a name="třída-vectorstore"></a>
## 🔧 Třída VectorStore

```python
class VectorStore:
    def __init__(self, db_path: str = "agent_memory.db")
```

<a name="hlavní-metody"></a>
### Hlavní Metody

<a name="add_memoryself-content-str-metadata-dictstr-any-none"></a>
#### `add_memory(self, content: str, metadata: Dict[str, Any] = None)`
Uloží novou vzpomínku.
- **content**: Text vzpomínky.
- **metadata**: Slovník s doplňujícími údaji (např. `type`, `source`).
- **Návratová hodnota**: `True` pokud byla uložena, `False` pokud byla zamítnuta (duplicita, error).

<a name="search_relevant_memoriesself-query-str-limit-int-5"></a>
#### `search_relevant_memories(self, query: str, limit: int = 5)`
Vyhledá nejrelevantnější vzpomínky pro daný dotaz.
- **query**: Hledaný text.
- **limit**: Maximální počet výsledků.

<a name="get_recent_memoriesself-limit-int-10"></a>
#### `get_recent_memories(self, limit: int = 10)`
Vrátí chronologicky nejnovější vzpomínky.

<a name="create_backupself"></a>
#### `create_backup(self)`
Vytvoří zálohu databáze do složky `backup/`.

<a name="delete_boredom_memoriesself"></a>
#### `delete_boredom_memories(self)`
Smaže dočasné vzpomínky vzniklé z nudy (cleanup).

<a name="související"></a>
## 🔗 Související
- [📖 Memory Architecture Guide](../core/memory-system.md) - Detailní popis fungování, scoringu a FTS5
- [🏗️ Architektura](../architecture.md)
- [📂 Source Code](../agent/)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
