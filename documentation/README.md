# 📚 RPI AI Agent - Kompletní Dokumentace

> **Navigace:** [📂 Dokumentace](README.md) | [📄 Přehled (OVERVIEW)](OVERVIEW.md) | [🔍 Index (INDEX)](INDEX.md) | [📋 API Tasklist (SUMMARY)](SUMMARY.md) | [🏗️ Architektura](architecture.md) | [🆘 Troubleshooting](troubleshooting.md)

> Detailní dokumentace autonomního AI agenta běžícího na Raspberry Pi s Discord integrací.
> **Verze:** Beta - CLOSED

---

<a name="obsah-dokumentace"></a>
## 📖 Obsah Dokumentace

<a name="základní-přehled"></a>
### 🎯 Základní Přehled
- [**O Projektu**](#o-projektu) - Úvod a přehled
- [**Architektura**](architecture.md) - Celková architektura systému
- [**Instalace a Nastavení**](scripts/deployment-guide.md) - Průvodce instalací

<a name="discord-příkazy"></a>
### 💬 Discord Příkazy
- [**Základní Příkazy**](commands/basic.md) - `!help`, `!status`, `!stats`, `!intelligence`, `!documentation`, `!web`
- [**Nástroje a Učení**](commands/tools-learning.md) - `!learn`, `!tools`, `!ask`, `!teach`, `!search`
- [**Správa Dat**](commands/data-management.md) - `!memory`, `!logs`, `!live`, `!export`
- [**Interakce**](commands/interaction.md) - `!mood`, `!config`, `!monitor`
- [**Administrace**](commands/admin.md) - `!restart`, `!shutdown`, `!debug`, `!ssh`, `!cmd`, `!topic`, `!goals`, `!report`, `!upload`, `!disable`/`!enable`

<a name="nástroje-tools"></a>
### 🛠️ Nástroje (Tools)
- [**Všechny Nástroje**](tools/all-tools.md) - Kompletní přehled všech 14 nástrojů

<a name="základní-funkcionality"></a>
### 🧠 Základní Funkcionality
- [**Autonomní Chování**](core/autonomous-behavior.md) - Systém "nudy" a autonomní rozhodování
- [**Paměťový Systém**](core/memory-system.md) - VectorStore a správa vzpomínek
- [**LLM Integrace**](core/llm-integration.md) - Lokální LLM model (llama-cpp)
- [**Resource Manager**](core/resource-manager.md) - Správa systémových zdrojů (4-tier system)
- [**Discord Client**](core/discord-client.md) - Discord bot integrace

<a name="skripty-a-utility"></a>
### 📝 Skripty a Utility
- [**Deployment Guide**](scripts/deployment-guide.md) - Nasazení na RPI
- [**Batch Scripts**](scripts/batch-scripts-reference.md) - Reference skriptů
- [**Maintenance**](scripts/maintenance.md) - Údržba

<a name="konfigurace"></a>
### 🔧 Konfigurace
- [**Settings Reference**](configuration/config_settings_reference.md) - Nastavení agenta
- [**Secrets Template**](configuration/config_secrets_template.md) - API klíče a tokeny
- [**Environment Variables**](configuration/environment_variables.md) - Proměnné prostředí
- [**Customization**](configuration/customization-guide.md) - Průvodce úpravami

<a name="pokročilé-témata"></a>
### 🔍 Pokročilé Témata
- [**Fuzzy Matching**](advanced/fuzzy-matching-algorithm.md) - Automatická korekce překlepů

<a name="řešení-problémů"></a>
### 🐛 Řešení Problémů
- [**Troubleshooting Guide**](troubleshooting.md) - Řešení častých problémů

---

<a name="o-projektu"></a>
## O Projektu

**RPI AI Agent** je autonomní AI asistent běžící na Raspberry Pi, který komunikuje přes Discord a má schopnost:

- 🤖 **Autonomně se rozhodovat** - Na základě "nudy" a cílů
- 🧠 **Učit se** - Objevovat a používat nástroje
- 💾 **Pamatovat si** - Ukládat zkušenosti do SQLite databáze
- 🛠️ **Používat nástroje** - FileTool, WebTool, MathTool, atd.
- 💬 **Komunikovat** - Přes Discord s uživateli
- 📊 **Monitorovat** - Systémové zdroje a automaticky reagovat

<a name="hlavní-komponenty"></a>
### Hlavní Komponenty

```
rpi_ai/
├── agent/
│   ├── core.py              # Hlavní agent (AutonomousAgent)
│   ├── commands.py          # Discord command handler
│   ├── tools.py             # Implementace nástrojů
│   ├── memory.py            # VectorStore paměť
│   ├── llm.py               # LLM klient
│   ├── discord_client.py    # Discord integrace
│   ├── resource_manager.py  # Správa zdrojů
│   └── error_tracker.py     # Sledování chyb
├── scripts/                 # Utility skripty
├── tests/                   # Testovací soubory
├── main.py                  # Entry point
└── documentation/           # Tato dokumentace
```

<a name="klíčové-funkce"></a>
### Klíčové Funkce

<a name="autonomní-rozhodování"></a>
#### 🎯 Autonomní Rozhodování
Agent používá systém "boredom" (nudy), který postupně roste. Když dosáhne prahu, agent se autonomně rozhodne pro akci pomocí LLM.

<a name="dynamické-nástroje"></a>
#### 🛠️ Dynamické Nástroje
Agent může objevovat a učit se používat nástroje. Každý nástroj má:

- Název a popis
- `execute()` metodu
- Automatické logování použití

<a name="paměťový-systém"></a>
#### 💾 Paměťový Systém
SQLite databáze s FTS5 vyhledáváním pro:
- Ukládání akcí a zkušeností
- Konverzace s uživateli
- Naučené informace
- Relevantní filtrování

<a name="resource-management"></a>
#### 📊 Resource Management
4-tier systém reagující na zatížení:
- **Tier 0** (< 85%): Normální provoz
- **Tier 1** (85%): Varování, cleanup
- **Tier 2** (90%): Aktivní mitigace, redukce LLM
- **Tier 3** (95%): Nouzový režim, ukončení procesů

<a name="technologie"></a>
### Technologie

- **Python 3.11+** - Hlavní jazyk
- **discord.py** - Discord bot framework
- **llama-cpp-python** - Lokální LLM (Qwen 2.5)
- **SQLite** - Databáze s FTS5
- **psutil** - Monitorování systému
- **asyncio** - Asynchronní operace

---

<a name="rychly-start"></a>

<a name="rychlý-start"></a>
## Rychlý Start

<a name="prerekvizity"></a>
### Prerekvizity
```bash
# Python 3.11+
python --version

# Instalace závislostí
pip install -r requirements.txt
```

<a name="konfigurace"></a>
### Konfigurace
1. Vytvoř `config_secrets.py`:
```python
DISCORD_TOKEN = "tvůj_discord_token"
DISCORD_CHANNEL_ID = 123456789  # Channel ID
ADMIN_USER_IDS = [987654321]    # Tvoje Discord ID
```

2. Nastav `config_settings.py` podle potřeby

<a name="spuštění"></a>
### Spuštění
```bash
python main.py
```

---

<a name="priklady-pouziti"></a>

<a name="příklady-použití"></a>
## Příklady Použití

<a name="základní-příkazy"></a>
### Základní Příkazy
```
!help              # Zobraz nápovědu
!status            # Stav agenta
!stats             # Detailní statistiky
!tools             # Seznam nástrojů
```

<a name="interakce-s-ai"></a>
### Interakce s AI
```
!ask co je to Python?
!teach Python je programovací jazyk
!search nejnovější zprávy o AI
!learn web_tool    # Nauč se konkrétní nástroj
```

<a name="administrace"></a>
### Administrace
```
!logs 50           # Posledních 50 řádků logů
!live logs 2m      # Live stream logů 2 minuty
!monitor 30        # Monitoruj zdroje 30 sekund
!restart           # Restart agenta
```

---

<a name="struktura-dokumentace"></a>
## Struktura Dokumentace

Každý dokument v této dokumentaci obsahuje:

- **📋 Přehled** - Co daná funkce/příkaz dělá
- **⚙️ Použití** - Jak to použít (příklady)
- **🔧 Parametry** - Dostupné parametry a volby
- **💡 Příklady** - Praktické ukázky
- **⚠️ Poznámky** - Důležité informace
- **🔗 Související** - Odkazy na související dokumenty

---

<a name="přispívání"></a>
## Přispívání

Pro přidání funkcí nebo opravu chyb:
1. Prostuduj dokumentaci
2. Otestuj změny lokálně
3. Aktualizuj dokumentaci
4. Vytvoř pull request

<a name="licence"></a>
## Licence

Tento projekt je pro osobní použití.


<a name="související"></a>
## 🔗 Související

- [📚 Přehled Dokumentace](documentation/OVERVIEW.md)
- [🏗️ Architektura](documentation/architecture.md)
- [🚀 Quick Start](documentation/README.md#quick-start)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
