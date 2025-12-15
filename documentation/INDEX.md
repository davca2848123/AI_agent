# 🔍 Rychlý Index - Všechny Příkazy a Funkce

> **Navigace:** [📂 Dokumentace](README.md) | [📄 Přehled (OVERVIEW)](OVERVIEW.md) | [🔍 Index (INDEX)](INDEX.md) | [📋 API Tasklist (SUMMARY)](SUMMARY.md) | [🏗️ Architektura](architecture.md) | [🆘 Troubleshooting](troubleshooting.md)

> Abecední index všech příkazů, nástrojů a funkcí.
> **Verze:** Beta - CLOSED

---

<a name="discord-příkazy-a-z"></a>
## 📋 Discord Příkazy (A-Z)

| Příkaz | Kategorie | Popis | Dokumentace |
|--------|-----------|-------|-------------|
| `!help` | Basic | Zobraz nápovědu | [📖 Zobrazit dokumentaci](commands/basic.md#help) |
| `!status` | Basic | Stav agenta | [📖 Zobrazit dokumentaci](commands/basic.md#status) |
| `!stats` | Basic | Detailní statistiky | [📖 Zobrazit dokumentaci](commands/basic.md#stats) |
| `!intelligence` | Basic | Intelligence metriky | [📖 Zobrazit dokumentaci](commands/basic.md#intelligence) |
| `!documentation` | Basic | Interaktivní dokumentace | [📖 Zobrazit dokumentaci](commands/basic.md#documentation) |
| `!learn` | Tools & Learning | Nauč se nástroj | [📖 Zobrazit dokumentaci](commands/tools-learning.md#learn) |
| `!tools` | Tools & Learning | Seznam nástrojů | [📖 Zobrazit dokumentaci](commands/tools-learning.md#tools) |
| `!ask` | Tools & Learning | Zeptej se AI na otázku | [📖 Zobrazit dokumentaci](commands/tools-learning.md#ask) |
| `!teach` | Tools & Learning | Nauč AI něco | [📖 Zobrazit dokumentaci](commands/tools-learning.md#teach) |
| `!search` | Tools & Learning | Vyhledej informace | [📖 Zobrazit dokumentaci](commands/tools-learning.md#search) |
| `!memory` | Data Management | Statistiky paměti | [📖 Zobrazit dokumentaci](commands/data-management.md#memory) |
| `!logs` | Data Management | Zobraz logy | [📖 Zobrazit dokumentaci](commands/data-management.md#logs) |
| `!live logs` | Data Management | Live stream logů | [📖 Zobrazit dokumentaci](commands/data-management.md#live-logs) |
| `!export` | Data Management | Export dat | [📖 Zobrazit dokumentaci](commands/data-management.md#export) |
| `!mood` | Interaction | Zobraz náladu agenta | [📖 Zobrazit dokumentaci](commands/interaction.md#mood) |
| `!goals` | Interaction | Správa cílů | [📖 Zobrazit dokumentaci](commands/interaction.md#goals) |
| `!config` | Interaction | Zobraz konfiguraci | [📖 Zobrazit dokumentaci](commands/interaction.md#config) |
| `!restart` | Admin | Restart agenta | [📖 Zobrazit dokumentaci](commands/admin.md#restart) |
| `!monitor` | Admin | Resource monitoring | [📖 Zobrazit dokumentaci](commands/admin.md#monitor) |
| `!debug` | Admin | Pokročilá diagnostika | [📖 Zobrazit dokumentaci](commands/admin.md#debug) |
| `!ssh` | Admin | Správa SSH tunelu | [📖 Zobrazit dokumentaci](commands/admin.md#ssh) |
| `!cmd` | Admin | Spusť shell příkaz | [📖 Zobrazit dokumentaci](commands/admin.md#cmd) |
| `!web` | Admin | Web interface správa | [📖 Zobrazit dokumentaci](commands/admin.md#web) |
| `!topic` | Admin | Manage discussion topics | [📖 Zobrazit dokumentaci](commands/admin.md#topic) |
| `!report` | Admin | Generate topics report | [📖 Zobrazit dokumentaci](commands/admin.md#report) |
| `!upload` | Admin | GitHub release upload | [📖 Zobrazit dokumentaci](commands/admin.md#upload) |
| `!disable` | Admin | Vypnout interakci (non-admin) | [📖 Zobrazit dokumentaci](commands/admin.md#disable) |
| `!enable` | Admin | Zapnout interakci | [📖 Zobrazit dokumentaci](commands/admin.md#enable) |

<a name="nástroje-a-z"></a>
## 🛠️ Nástroje (A-Z)

| Nástroj | Účel | Dokumentace |
|---------|------|-------------|
| **CodeTool** | Spouštění Python kódu | [📖 Zobrazit dokumentaci](tools/all-tools.md#codetool) |
| **DatabaseTool** | SQLite SELECT dotazy | [📖 Zobrazit dokumentaci](tools/all-tools.md#databasetool) |
| **DiscordActivityTool** | Sledování Discord aktivit | [📖 Zobrazit dokumentaci](tools/all-tools.md#discordactivitytool) |
| **FileTool** | Práce se soubory | [📖 Zobrazit dokumentaci](tools/all-tools.md#filetool) |
| **GitTool** | Git status/log | [📖 Zobrazit dokumentaci](tools/all-tools.md#gittool) |
| **MathTool** | Matematické výpočty | [📖 Zobrazit dokumentaci](tools/all-tools.md#mathtool) |
| **NoteTool** | Správa poznámek | [📖 Zobrazit dokumentaci](tools/all-tools.md#notetool) |
| **RSSTool** | Čtení RSS feedů | [📖 Zobrazit dokumentaci](tools/all-tools.md#rsstool) |
| **SystemTool** | Systémové informace | [📖 Zobrazit dokumentaci](tools/all-tools.md#systemtool) |
| **TimeTool** | Práce s časem | [📖 Zobrazit dokumentaci](tools/all-tools.md#timetool) |
| **TranslateTool** | Překlady textu | [📖 Zobrazit dokumentaci](tools/all-tools.md#translatetool) |
| **WeatherTool** | Informace o počasí | [📖 Zobrazit dokumentaci](tools/all-tools.md#weathertool) |
| **WebTool** | Vyhledávání a čtení webu | [📖 Zobrazit dokumentaci](tools/all-tools.md#webtool) |
| **WikipediaTool** | Wikipedia vyhledávání | [📖 Zobrazit dokumentaci](tools/all-tools.md#wikipediatool) |

<a name="architecture-guides"></a>
## 🏗️ Architecture & Guides

| Systém | Popis | Dokumentace |
|--------|-------|-------------|
| **Autonomous Behavior** | Boredom, decision making | [📖 Zobrazit dokumentaci](core/autonomous-behavior.md) |
| **Discord Client** | Discord bot integrace | [📖 Zobrazit dokumentaci](core/discord-client.md) |
| **LLM Integration** | Qwen 2.5, generování | [📖 Zobrazit dokumentaci](core/llm-integration.md) |
| **Memory System** | VectorStore, FTS5 | [📖 Zobrazit dokumentaci](core/memory-system.md) |
| **Resource Manager** | 4-tier system, SWAP | [📖 Zobrazit dokumentaci](core/resource-manager.md) |
| **Reporting** | Daily stats & logs | [📖 Zobrazit dokumentaci](core/reporting.md) |

<a name="api-reference"></a>
## 📚 API Reference

| Modul | Popis | Dokumentace |
|-------|-------|-------------|
| **Agent Core** | AutonomousAgent class | [📖 API Docs](api/agent-core.md) |
| **Memory System** | VectorStore class | [📖 API Docs](api/memory-system.md) |
| **Tools API** | Tool base class & implementations | [📖 API Docs](api/tools-api.md) |
| **Discord Client** | DiscordClient wrapper | [📖 API Docs](api/discord-client.md) |
| **LLM Integration** | LLMClient class | [📖 API Docs](api/llm-integration.md) |
| **Error Tracker** | ErrorTracking & Recovery | [📖 API Docs](api/error-tracker.md) |
| **Sanitizer** | Data Masking Utils | [📖 API Docs](api/utils-sanitizer.md) |
| **Startup Utils** | Boot loop protection | [📖 API Docs](api/utils-startup.md) |
| **Hardware** | Monitor & LED Control | [📖 API Docs](api/hardware-monitor.md) |
| **Web Interface** | Logs & Process API | [📖 API Docs](api/api-logs.md) |

<a name="konfigurace"></a>
## ⚙️ Konfigurace

| Soubor | Popis | Dokumentace |
|--------|-------|-------------|
| **Complete Guide** | Kompletní průvodce nastavením | [📖 Zobrazit](configuration/complete-configuration-guide.md) |
| **Settings Ref** | Referenční příručka nastavení | [📖 Zobrazit](configuration/config_settings_reference.md) |
| **Env Variables** | Proměnné prostředí (.env) | [📖 Zobrazit](configuration/environment_variables.md) |
| **Secrets** | Šablona pro secrets | [📖 Zobrazit](configuration/config_secrets_template.md) |
| **Customization** | Průvodce úpravami | [📖 Zobrazit](configuration/customization-guide.md) |

<a name="skripty-a-pokročilé"></a>
## 📜 Skripty a Pokročilé

| Téma | Popis | Dokumentace |
|------|-------|-------------|
| **Deployment** | Průvodce nasazením | [📖 Zobrazit](scripts/deployment-guide.md) |
| **Maintenance** | Údržba systému | [📖 Zobrazit](scripts/maintenance.md) |
| **Batch Scripts** | Referenční příručka skriptů | [📖 Zobrazit](scripts/batch-scripts-reference.md) |
| **Testing Guide** | Testování a verifikace | [📖 Zobrazit](scripts/testing-guide.md) |
| **Memory Manager** | Database CLI Tool | [📖 Zobrazit](scripts/memory-manager.md) |
| **Fuzzy Matching** | Algoritmus vyhledávání | [📖 Zobrazit](advanced/fuzzy-matching-algorithm.md) |

<a name="hlavní-dokumenty"></a>
## 📚 Hlavní Dokumenty


| Dokument | Obsah |
|----------|-------|
| [README.md](README.md) | Hlavní index s TOC |
| [OVERVIEW.md](OVERVIEW.md) | Rychlý přehled a statistiky |
| [SUMMARY.md](SUMMARY.md) | Finální souhrn dokumentace |
| [architecture.md](architecture.md) | Architektura systému |

<a name="vyhledávání-podle-tématu"></a>
## 🔍 Vyhledávání Podle Tématu

<a name="pokud-hledáš"></a>
### Pokud hledáš...

**Jak používat agenta?**
→ [📖 README.md](README.md) → [📖 Základní příkazy](commands/basic.md)

**Jak naučit agenta?**
→ [📖 Tools & Learning](commands/tools-learning.md) → `!learn`, `!teach`

**Jak agent funguje uvnitř?**
→ [📖 Architektura](architecture.md) → [📖 Core systémy](core/)

**Jak monitorovat systém?**
→ [📖 Admin příkazy](commands/admin.md) → `!monitor`, `!debug`

**Jak agent rozhoduje?**
→ [📖 Autonomous Behavior](core/autonomous-behavior.md)

**Jak funguje paměť?**
→ [📖 Memory System](core/memory-system.md)

**Jak funguje LLM?**
→ [📖 LLM Integration](core/llm-integration.md)

**Jak funguje resource management?**
→ [📖 Resource Manager](core/resource-manager.md)

**Jaké nástroje jsou dostupné?**
→ [📖 All Tools](tools/all-tools.md)

3. [📖 Architecture](architecture.md) - Jak to funguje

<a name="vývojář"></a>
### 👨‍💻 Vývojář
1. [📖 Architecture](architecture.md) - Celkový přehled
2. [📖 Core Systems](core/) - Implementace
3. [📖 All Tools](tools/all-tools.md) - Tool development


<a name="související"></a>
## 🔗 Související

- [📄 Přehled (OVERVIEW)](OVERVIEW.md)
- [🏗️ Architektura](architecture.md)
- [📋 Tasklist (SUMMARY)](SUMMARY.md)
---
Poslední aktualizace: 2025-12-15  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
