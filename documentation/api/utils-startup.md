# 🚀 Startup Tracker API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Startup Tracker API](utils-startup.md)

Dokumentace pro modul `agent/startup_tracker.py`.

<a name="přehled"></a>
## 📋 Přehled

Sleduje opakovaná selhání při startu agenta. Pokud agent spadne příliš mnohokrát v řadě (boot loop), tento modul vynutí čekací dobu (cool-down), aby se zabránilo zbytečnému vytěžování systému nebo spamování API.

---

<a name="funkce"></a>
## 🔧 Funkce

<a name="record_failure"></a>
### `record_failure()`
Zaznamená neúspěšný start. Zvyšuje počítadlo chyb a ukládá čas.
- **Returns**: Nový počet chyb (int).

<a name="record_success"></a>
### `record_success()`
Zaznamená úspěšný start. Resetuje počítadlo chyb a maže záznam o selhání.
- **Použití**: Volá se po úspěšné inicializaci všech systémů.

<a name="check_should_waitretry_limit-wait_hours"></a>
### `check_should_wait(retry_limit=3, wait_hours=3)`
Zkontroluje, zda má agent čekat před dalším pokusem o start.

- **retry_limit**: Kolikrát může spadnout, než se aktivuje ochrana (default: 3).
- **wait_hours**: Jak dlouho čekat po překročení limitu (default: 3 hodiny).

**Návratová hodnota:** `tuple(bool, float)`
- `should_wait` (bool): True pokud má čekat.
- `remaining` (float): Zbývající čas v sekundách.

<a name="load_failures"></a>
### `load_failures()`
Načte data o selháních ze souboru `.startup_failures`.

---

<a name="konfigurace"></a>
## ⚙️ Konfigurace

Limity jsou definovány v `config_settings.py`:
- `STARTUP_RETRY_LIMIT`
- `STARTUP_FAILURE_WAIT`


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🧠 Core Documentation](../core/)
- [📂 Source Code](../agent/)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
