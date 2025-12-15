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
Poslední aktualizace: 2025-12-09  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
