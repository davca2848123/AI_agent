# 📚 Dokumentace - Rychlý Přehled

> Stručné shrnutí všech dokumentovaných částí projektu

## ✅ Dokončené Sekce

### 📖 Hlavní Dokumentace
- ✅ **[README.md](README.md)** - Hlavní dokumentace s kompletním obsahem

### 💬 Příkazy (Commands)
- ✅ **[Základní příkazy](commands/basic.md)** - help, status, stats, intelligence
- ✅ **[Nástroje a učení](commands/tools-learning.md)** - tools, learn, ask, teach, search
- ✅ **[Správa dat](commands/data-management.md)** - memory, logs, live logs, export
- ✅ **[Interakce](commands/interaction.md)** - mood, goals, config
- ✅ **[Administrace](commands/admin.md)** - restart, cmd, monitor, ssh, debug

### 🛠️ Nástroje (Tools)
- ✅ **[Všechny nástroje](tools/all-tools.md)** - Kompletní dokumentace všech 14 nástrojů

### 🧠 Core Funkcionality
- ✅ **[Autonomní chování](core/autonomous-behavior.md)** - Boredom, decision making, learning mode
- ✅ **[Paměťový systém](core/memory-system.md)** - VectorStore, FTS5, backup/restore
- ✅ **[LLM integrace](core/llm-integration.md)** - Qwen 2.5, generování, tool calling
- ✅ **[Resource Manager](core/resource-manager.md)** - 4-tier system, SWAP, network monitor

---

## 📊 Statistiky Dokumentace

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

### Pokryté Komponenty

- **✅ 24 Discord příkazů** - Všechny příkazy zdokumentovány
- **✅ 14 nástrojů** - FileTool, WebTool, MathTool, atd.
- **✅ 4 core systémy** - Autonomous, Memory, LLM, Resources
- **✅ Fuzzy matching** - Automatická korekce překlepů
- **✅ Command queue** - Asynchronní zpracování
- **✅ Learning mode** - Systematické učení
- **✅ 4-tier system** - Resource management
- **✅ Network monitoring** - Internet disconnect/reconnect

---

## 🎯 Hlavní Funkcionality Projektu

### 1. Autonomní Rozhodování
- Boredom systém (0-100%)
- LLM-based decision making
- Context-aware actions
- Goal-oriented behavior

### 2. Nástroje (Tools)
- 14 různých nástrojů
- FileTool, WebTool, MathTool, WeatherTool, atd.
- Automatické logování
- Usage tracking

### 3. Paměť
- SQLite + FTS5
- Relevance filtering
- Keyword search
- Auto-backup

### 4. Discord Integrace
- 21 příkazů
- Interactive buttons
- Status updates
- Live monitoring

### 5. Resource Management
- 4-tier adaptive system
- SWAP expansion
- Process termination
- LLM parameter adjustment

### 6. Learning System
- Autonomous discovery
- Systematic learning mode
- Activity monitoring
- Tool mastery tracking

---

## 📝 Použití Dokumentace

### Pro Uživatele

**Začni zde:**
1. [README.md](README.md) - Úvod a obsah
2. [Základní příkazy](commands/basic.md) - `!help`, `!status`
3. [Nástroje a učení](commands/tools-learning.md) - `!ask`, `!learn`

### Pro Administrátory

**Pokročilé:**
1. [Administrace](commands/admin.md) - `!restart`, `!monitor`, `!debug`
2. [Resource Manager](core/resource-manager.md) - Tier system
3. [LLM Integrace](core/llm-integration.md) - Model management

### Pro Vývojáře

**Implementace:**
1. [Autonomní chování](core/autonomous-behavior.md) - Decision making
2. [Paměťový systém](core/memory-system.md) - VectorStore API
3. [Všechny nástroje](tools/all-tools.md) - Tool development

---

## 🔍 Hledání v Dokumentaci

### Podle Typu

**Příkazy:** `documentation/commands/*.md`  
**Nástroje:** `documentation/tools/*.md`  
**Core:** `documentation/core/*.md`

### Podle Tématu

| Téma | Dokumenty |
|------|-----------|
| LLM | llm-integration.md, autonomous-behavior.md |
| Paměť | memory-system.md, data-management.md |
| Nástroje | all-tools.md, tools-learning.md |
| Admin | admin.md, resource-manager.md |
| Statistiky | basic.md (stats), data-management.md |

---

## ⚠️ Co Ještě Chybí

Sekce které zatím nejsou dokončeny:

- [ ] API Reference (podrobná)
- [x] Troubleshooting guide
- [x] Advanced topics (fuzzy matching)
- [x] Scripts documentation
- [x] Configuration guide
- [ ] Installation guide

---

## 🔄 Aktualizace Dokumentace

Po každé změně v kódu nezapomeň aktualizovat příslušnou dokumentaci!

**Pravidla:**
1. Změnil jsi příkaz? → Aktualizuj `commands/*.md`
2. Přidal jsi nástroj? → Aktualizuj `tools/all-tools.md`
3. Změnil jsi core logiku? → Aktualizuj `core/*.md`
4. Přidal jsi funkci? → Aktualizuj `README.md` obsah

---

**Vytvořeno:** 2025-12-02  
**Poslední aktualizace:** 2025-12-03  
**Verze Dokumentace:** 1.1.0  
**Soubory:** 19 dokumentačních souborů
