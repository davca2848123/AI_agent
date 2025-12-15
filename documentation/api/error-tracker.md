# 🐛 Error Tracker API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Error Tracker API](error-tracker.md)

Dokumentace pro modul `agent/error_tracker.py`, který zajišťuje sledování a analýzu chyb.

<a name="přehled"></a>
## 📋 Přehled

`ErrorTracker` zachytává runtime výjimky, ukládá je do historie pro debugging (přístupné přes příkaz `!debug errors`) a poskytuje analytiku pro identifikaci problematických míst v kódu.

---

<a name="třída-errortracker"></a>
## 🔧 Třída ErrorTracker

<a name="usage"></a>
### Použití
```python
from agent.error_tracker import get_error_tracker

tracker = get_error_tracker()
try:
    # some risky code
    1 / 0
except Exception as e:
    tracker.log_error(e)
```

<a name="metody"></a>
### Metody

<a name="log_errorexception-tb_str"></a>
#### `log_error(exception, tb_str=None)`
Zaloguje výjimku do trackeru.
- **exception**: Objekt výjimky.
- **tb_str**: Volitelný string s tracebackem (pokud není zadán, extrahuje se automaticky).

<a name="get_recentlimit-hours"></a>
#### `get_recent(limit=10, hours=24)`
Vrátí seznam nedávných chyb (`List[ErrorEntry]`).
- **limit**: Max počet chyb.
- **hours**: Časové okno v hodinách.

<a name="get_recommendations"></a>
#### `get_recommendations()`
Analyzuje chyby a navrhuje opravy (např. "Check variable initialization...").
- **Returns**: `List[str]` s doporučeními.

<a name="cleanup_old_errors"></a>
#### `cleanup_old_errors()`
Odstraní chyby starší než 24 hodin (automaticky voláno při startu/loadu).

---

<a name="datové-struktury"></a>
## 📊 Datové Struktury

<a name="errorentry"></a>
### `ErrorEntry`
Dataclass reprezentující jednu chybu.
- `timestamp`: Čas vzniku (float)
- `error_type`: Typ výjimky (str, např. "ZeroDivisionError")
- `message`: Chybová hláška (str)
- `file`: Soubor kde chyba nastala
- `line`: Řádek kódu
- `function`: Funkce/metoda


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🧠 Core Documentation](../core/)
- **📂 Source Code:** `agent/`
---
Poslední aktualizace: 2025-12-15  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
