# 🧪 Testing & Verification Guide

> **Navigace:** [📂 Dokumentace](../README.md) | [📜 Scripts](../README.md#scripts-advanced) | [Testing Guide](testing-guide.md)

Tento průvodce popisuje testovací skripty a postupy pro ověřování functionality agenta.

<a name="přehled"></a>
## 📋 Přehled

Projekt obsahuje sadu skriptů v `scripts/internal/` (pro manuální spouštění) a `tests/` (pro automatizované testy - *budoucí implementace*), které slouží k validaci oprav a funkčnosti.

---

<a name="verification-scripts"></a>
## 🔍 Verification Scripts

Tyto skripty slouží k rychlému ověření, zda kritické komponenty fungují správně.

<a name="verify_fixespy"></a>
### [`verify_fixes.py`](../../scripts/internal/verify_fixes.py)
Univerzální testovací skript pro ověření specifických oprav (např. po refactoringu).
- **Spuštění**: `python scripts/internal/verify_fixes.py`
- **Testuje**:
    - Základní importy (`agent.core`, `agent.main`).
    - Existenci kritických souborů.
    - Základní funkčnost loggeru.

<a name="verify_tools_functionalitypy"></a>
### [`verify_tools_functionality.py`](../../scripts/internal/verify_tools_functionality.py)
Komplexní test všech registrovaných nástrojů.
- **Spuštění**: `python scripts/internal/verify_tools_functionality.py`
- **Testuje**:
    - Inicializaci `ToolRegistry`.
    - Spuštění dummy příkazů pro každý nástroj (`TimeTool.now`, `App.get_status`, atd.).
    - Ověřuje, že nástroje nepadají na importech nebo syntax chyby.

<a name="verify_websocket_and_infopy"></a>
### [`verify_websocket_and_info.py`](../../scripts/internal/verify_websocket_and_info.py)
Testuje integritu Web Interface a systémových informací.
- **Spuštění**: `python scripts/internal/verify_websocket_and_info.py`
- **Testuje**:
    - Funkčnost `psutil` pro sběr dat o CPU/RAM.
    - Simuluje WebSocket payload.

---

<a name="testovací-data"></a>
## 📊 Testovací Data

Skripty mohou generovat dočasné soubory:
- `test_output/`: Výstupy z testů (pokud existují).
- `.startup_failures`: Testování startup trackeru.

Doporučuje se po testování spustit cleanup skripty (viz [Maintenance](maintenance.md)).


<a name="související"></a>
## 🔗 Související

- [⚙️ Konfigurace](../configuration/complete-configuration-guide.md)
- [🆘 Troubleshooting](../troubleshooting.md)
- [🏗️ Architektura](../architecture.md)

---
Poslední aktualizace: 2025-12-06  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
