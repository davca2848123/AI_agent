# 📚 Dokumentace - Rychlý Přehled

> **Navigace:** [📂 Dokumentace](README.md) | [📄 Přehled (OVERVIEW)](OVERVIEW.md) | [🔍 Index (INDEX)](INDEX.md) | [📋 API Tasklist (SUMMARY)](SUMMARY.md) | [🏗️ Architektura](architecture.md) | [🆘 Troubleshooting](troubleshooting.md) | [🔍 Hledat](INDEX.md#vyhledavani)

> Stručné shrnutí všech dokumentovaných částí projektu.
> **Verze:** Alpha

---

<a name="dokončené-sekce"></a>
## ✅ Dokončené Sekce

<a name="hlavní-dokumentace"></a>
### 📖 Hlavní Dokumentace
- ✅ **[README.md](README.md)** - Hlavní dokumentace s kompletním obsahem

<a name="příkazy-commands"></a>
### 💬 Příkazy (Commands)
- ✅ **[Základní příkazy](commands/basic.md)** - help, status, stats, intelligence
- ✅ **[Nástroje a učení](commands/tools-learning.md)** - tools, learn, ask, teach, search
- ✅ **[Správa dat](commands/data-management.md)** - memory, logs, live logs, export
- ✅ **[Interakce](commands/interaction.md)** - mood, goals, config
- ✅ **[Administrace](commands/admin.md)** - restart, cmd, monitor, ssh, debug

<a name="nástroje-tools"></a>
### 🛠️ Nástroje (Tools)
- ✅ **[Všechny nástroje](tools/all-tools.md)** - Kompletní dokumentace všech 14 nástrojů

<a name="core-funkcionality"></a>
### 🧠 Core Funkcionality
- ✅ **[Autonomní chování](core/autonomous-behavior.md)** - Boredom, decision making, learning mode
- ✅ **[Paměťový systém](core/memory-system.md)** - VectorStore, FTS5, backup/restore
- ✅ **[LLM integrace](core/llm-integration.md)** - Qwen 2.5, generování, tool calling
- ✅ **[Resource Manager](core/resource-manager.md)** - 4-tier system, SWAP, network monitor
- ✅ **[Discord Client](core/discord-client.md)** - Discord bot integrace

---

<a name="statistiky-dokumentace"></a>
## 📊 Statistiky Dokumentace

<a name="vytvořené-soubory"></a>
### Vytvořené Soubory

```
documentation/
├── README.md                           # Hlavní index s TOC
├── commands/
│   ├── basic.md                       # 4 příkazy
│   ├── tools-learning.md              # 5 příkazů
│   ├── data-management.md             # 4 příkazy
│   ├── interaction.md                 # 3 příkazy
│   └── admin.md                       # 5 příkazů
├── tools/
│   └── all-tools.md                   # 14 nástrojů
└── core/
    ├── autonomous-behavior.md         # Autonomní systém
    ├── memory-system.md               # Paměť
    ├── llm-integration.md             # LLM
    └── resource-manager.md            # Resource management
```

<a name="pokryté-komponenty"></a>
### Pokryté Komponenty

- **✅ 24 Discord příkazů** - Všechny příkazy zdokumentovány
- **✅ 14 nástrojů** - FileTool, WebTool, MathTool, atd.
- **✅ 5 core systémů** - Autonomous, Memory, LLM, Resources, Discord
- **✅ Fuzzy matching** - Automatická korekce překlepů
- **✅ Command queue** - Asynchronní zpracování
- **✅ Learning mode** - Systematické učení
- **✅ 4-tier system** - Resource management
- **✅ Network monitoring** - Internet disconnect/reconnect

---

<a name="hlavní-funkcionality-projektu"></a>
## 🎯 Hlavní Funkcionality Projektu

<a name="1-autonomní-rozhodování"></a>
### 1. Autonomní Rozhodování
- Boredom systém (0-100%)
- LLM-based decision making
- Context-aware actions
- Goal-oriented behavior

<a name="2-nástroje-tools"></a>
### 2. Nástroje (Tools)
- 14 různých nástrojů
- FileTool, WebTool, MathTool, WeatherTool, atd.
- Automatické logování
- Usage tracking

<a name="3-paměť"></a>
### 3. Paměť
- SQLite + FTS5
- Relevance filtering
- Keyword search
- Auto-backup

<a name="4-discord-integrace"></a>
### 4. Discord Integrace
- 21 příkazů
- Interactive buttons
- Status updates
- Live monitoring

<a name="5-resource-management"></a>
### 5. Resource Management
- 4-tier adaptive system
- SWAP expansion
- Process termination
- LLM parameter adjustment

<a name="6-learning-system"></a>
### 6. Learning System
- Autonomous discovery
- Systematic learning mode
- Activity monitoring
- Tool mastery tracking

---

<a name="použití-dokumentace"></a>
## 📝 Použití Dokumentace

<a name="pro-uživatele"></a>
### Pro Uživatele

**Začni zde:**
1. [📖 README.md](README.md) - Úvod a obsah
2. [📖 Základní příkazy](commands/basic.md) - `!help`, `!status`
3. [📖 Nástroje a učení](commands/tools-learning.md) - `!ask`, `!learn`

<a name="pro-administrátory"></a>
### Pro Administrátory

**Pokročilé:**
1. [📖 Administrace](commands/admin.md) - `!restart`, `!monitor`, `!debug`
2. [📖 Resource Manager](core/resource-manager.md) - Tier system
3. [📖 LLM Integrace](core/llm-integration.md) - Model management

<a name="pro-vývojáře"></a>
### Pro Vývojáře

**Implementace:**
1. [📖 Autonomní chování](core/autonomous-behavior.md) - Decision making
2. [📖 Paměťový systém](core/memory-system.md) - VectorStore API
3. [📖 Všechny nástroje](tools/all-tools.md) - Tool development

---

<a name="hledání-v-dokumentaci"></a>
## 🔍 Hledání v Dokumentaci

<a name="podle-typu"></a>
### Podle Typu

**Příkazy:** `documentation/commands/*.md`  
**Nástroje:** `documentation/tools/*.md`  
**Core:** `documentation/core/*.md`

<a name="podle-tématu"></a>
### Podle Tématu

| Téma | Dokumenty |
|------|-----------|
| LLM | [llm-integration.md](core/llm-integration.md), [autonomous-behavior.md](core/autonomous-behavior.md) |
| Paměť | [memory-system.md](core/memory-system.md), [data-management.md](commands/data-management.md) |
| Nástroje | [all-tools.md](tools/all-tools.md), [tools-learning.md](commands/tools-learning.md) |
| Admin | [admin.md](commands/admin.md), [resource-manager.md](core/resource-manager.md) |
| Statistiky | [basic.md](commands/basic.md), [data-management.md](commands/data-management.md) |

---

<a name="co-ještě-chybí"></a>
## ⚠️ Co Ještě Chybí

Sekce které zatím nejsou dokončeny:

- [ ] API Reference (podrobná)
- [x] Troubleshooting guide
- [x] Advanced topics (fuzzy matching)
- [x] Scripts documentation
- [x] Configuration guide
- [x] Installation guide

---

<a name="aktualizace-dokumentace"></a>
## 🔄 Aktualizace Dokumentace

Po každé změně v kódu nezapomeň aktualizovat příslušnou dokumentaci!

**Pravidla:**
1. Změnil jsi příkaz? → Aktualizuj `commands/*.md`
2. Přidal jsi nástroj? → Aktualizuj `tools/all-tools.md`
3. Změnil jsi core logiku? → Aktualizuj `core/*.md`
4. Přidal jsi funkci? → Aktualizuj `README.md` obsah

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
