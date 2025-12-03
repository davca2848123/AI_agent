# 🔍 Rychlý Index - Všechny Příkazy a Funkce

> Abecední index všech příkazů, nástrojů a funkcí

## 📋 Discord Příkazy (A-Z)

| Příkaz | Kategorie | Popis | Dokumentace |
|--------|-----------|-------|-------------|
| `!ask` | Tools & Learning | Zeptej se AI na otázku | [→](commands/tools-learning.md#ask) |
| `!cmd` | Admin | Spusť shell příkaz | [→](commands/admin.md#cmd) |
| `!config` | Interaction | Zobraz konfiguraci | [→](commands/interaction.md#config) |
| `!documentation` | Basic | Interaktivní dokumentace | [→](commands/basic.md#documentation) |
| `!debug` | Admin | Pokročilá diagnostika | [→](commands/admin.md#debug) |
| `!export` | Data Management | Export dat | [→](commands/data-management.md#export) |
| `!goals` | Interaction | Správa cílů | [→](commands/interaction.md#goals) |
| `!help` | Basic | Zobraz nápovědu | [→](commands/basic.md#help) |
| `!intelligence` | Basic | Intelligence metriky | [→](commands/basic.md#intelligence) |
| `!learn` | Tools & Learning | Nauč se nástroj | [→](commands/tools-learning.md#learn) |
| `!live logs` | Data Management | Live stream logů | [→](commands/data-management.md#live-logs) |
| `!logs` | Data Management | Zobraz logy | [→](commands/data-management.md#logs) |
| `!memory` | Data Management | Statistiky paměti | [→](commands/data-management.md#memory) |
| `!monitor` | Admin | Resource monitoring | [→](commands/admin.md#monitor) |
| `!mood` | Interaction | Zobraz náladu agenta | [→](commands/interaction.md#mood) |
| `!report` | Admin | Generate topics report | [→](commands/admin.md#report) |
| `!restart` | Admin | Restart agenta | [→](commands/admin.md#restart) |
| `!search` | Tools & Learning | Vyhledej informace | [→](commands/tools-learning.md#search) |
| `!ssh` | Admin | Správa SSH tunelu | [→](commands/admin.md#ssh) |
| `!stats` | Basic | Detailní statistiky | [→](commands/basic.md#stats) |
| `!status` | Basic | Stav agenta | [→](commands/basic.md#status) |
| `!teach` | Tools & Learning | Nauč AI něco | [→](commands/tools-learning.md#teach) |
| `!tools` | Tools & Learning | Seznam nástrojů | [→](commands/tools-learning.md#tools) |
| `!topic` | Admin | Manage discussion topics | [→](commands/admin.md#topic) |

## 🛠️ Nástroje (A-Z)

| Nástroj | Účel | Dokumentace |
|---------|------|-------------|
| **CodeTool** | Spouštění Python kódu | [→](tools/all-tools.md#codetool) |
| **DatabaseTool** | SQLite SELECT dotazy | [→](tools/all-tools.md#databasetool) |
| **DiscordActivityTool** | Sledování Discord aktivit | [→](tools/all-tools.md#discordactivitytool) |
| **FileTool** | Práce se soubory | [→](tools/all-tools.md#filetool) |
| **GitTool** | Git status/log | [→](tools/all-tools.md#gittool) |
| **MathTool** | Matematické výpočty | [→](tools/all-tools.md#mathtool) |
| **NoteTool** | Správa poznámek | [→](tools/all-tools.md#notetool) |
| **RSSTool** | Čtení RSS feedů | [→](tools/all-tools.md#rsstool) |
| **SystemTool** | Systémové informace | [→](tools/all-tools.md#systemtool) |
| **TimeTool** | Práce s časem | [→](tools/all-tools.md#timetool) |
| **TranslateTool** | Překlady textu | [→](tools/all-tools.md#translatetool) |
| **WeatherTool** | Informace o počasí | [→](tools/all-tools.md#weathertool) |
| **WebTool** | Vyhledávání a čtení webu | [→](tools/all-tools.md#webtool) |
| **WikipediaTool** | Wikipedia vyhledávání | [→](tools/all-tools.md#wikipediatool) |

## 🧠 Core Systémy

| Systém | Popis | Dokumentace |
|--------|-------|-------------|
| **Autonomous Behavior** | Boredom, decision making | [→](core/autonomous-behavior.md) |
| **Discord Client** | Discord bot integrace | [→](core/discord-client.md) |
| **LLM Integration** | Qwen 2.5, generování | [→](core/llm-integration.md) |
| **Memory System** | VectorStore, FTS5 | [→](core/memory-system.md) |
| **Resource Manager** | 4-tier system, SWAP | [→](core/resource-manager.md) |

## 📚 Hlavní Dokumenty

| Dokument | Obsah |
|----------|-------|
| [README.md](README.md) | Hlavní index s TOC |
| [OVERVIEW.md](OVERVIEW.md) | Rychlý přehled a statistiky |
| [SUMMARY.md](SUMMARY.md) | Finální souhrn dokumentace |
| [architecture.md](architecture.md) | Architektura systému |

## 🔍 Vyhledávání Podle Tématu

### Pokud hledáš...

**Jak používat agenta?**
→ [README.md](README.md) → [Základní příkazy](commands/basic.md)

**Jak naučit agenta?**
→ [Tools & Learning](commands/tools-learning.md) → `!learn`, `!teach`

**Jak agent funguje uvnitř?**
→ [Architektura](architecture.md) → [Core systémy](core/)

**Jak monitorovat systém?**
→ [Admin příkazy](commands/admin.md) → `!monitor`, `!debug`

**Jak agent rozhoduje?**
→ [Autonomous Behavior](core/autonomous-behavior.md)

**Jak funguje paměť?**
→ [Memory System](core/memory-system.md)

**Jak funguje LLM?**
→ [LLM Integration](core/llm-integration.md)

**Jak funguje resource management?**
→ [Resource Manager](core/resource-manager.md)

**Jaké nástroje jsou dostupné?**
→ [All Tools](tools/all-tools.md)

## 📖 Dokumentace Podle Role

### 🆕 Nový Uživatel
1. [README.md](README.md) - Start here
2. [Basic Commands](commands/basic.md) - `!help`, `!status`
3. [Tools & Learning](commands/tools-learning.md) - `!ask`, `!learn`

### 👤 Běžný Uživatel
1. [Interaction](commands/interaction.md) - `!mood`, `!goals`
2. [Data Management](commands/data-management.md) - `!memory`, `!logs`
3. [All Tools](tools/all-tools.md) - Co všechno umí

### 👨‍💼 Administrátor
1. [Admin Commands](commands/admin.md) - `!restart`, `!monitor`, `!debug`
2. [Resource Manager](core/resource-manager.md) - Tier system
3. [Architecture](architecture.md) - Jak to funguje

### 👨‍💻 Vývojář
1. [Architecture](architecture.md) - Celkový přehled
2. [Core Systems](core/) - Implementace
3. [All Tools](tools/all-tools.md) - Tool development

---

**Vytvořeno:** 2025-12-02  
**Účel:** Rychlá navigace v dokumentaci  
**Tip:** Použij Ctrl+F pro vyhledávání
