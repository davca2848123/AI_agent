# 📚 RPI AI Agent - Kompletní Dokumentace

> Detailní dokumentace autonomního AI agenta běžícího na Raspberry Pi s Discord integrací

## 📖 Obsah Dokumentace

### 🎯 Základní Přehled
- [**O Projektu**](#o-projektu) - Úvod a přehled
- [**Architektura**](architecture.md) - Celková architektura systému
- [**Instalace a Nastavení**](installation.md) - Průvodce instalací

### 💬 Discord Příkazy
- [**Základní Příkazy**](commands/basic.md) - `!help`, `!status`, `!stats`, `!intelligence`
- [**Nástroje a Učení**](commands/tools-learning.md) - `!tools`, `!learn`, `!ask`, `!teach`, `!search`
- [**Správa Dat**](commands/data-management.md) - `!memory`, `!logs`, `!live`, `!export`
- [**Interakce**](commands/interaction.md) - `!mood`, `!goals`, `!config`
- [**Administrace**](commands/admin.md) - `!restart`, `!monitor`, `!ssh`, `!cmd`, `!debug`

### 🛠️ Nástroje (Tools)
- [**FileTool**](tools/file-tool.md) - Práce se soubory a složkami
- [**SystemTool**](tools/system-tool.md) - Systémové informace
- [**WebTool**](tools/web-tool.md) - Vyhledávání a čtení webu
- [**TimeTool**](tools/time-tool.md) - Práce s časem a datumy
- [**MathTool**](tools/math-tool.md) - Matematické výpočty
- [**WeatherTool**](tools/weather-tool.md) - Informace o počasí
- [**CodeTool**](tools/code-tool.md) - Spouštění Python kódu
- [**WikipediaTool**](tools/wikipedia-tool.md) - Vyhledávání na Wikipedia
- [**GitTool**](tools/git-tool.md) - Git operace (pokročilé)

### 🧠 Základní Funkcionality
- [**Autonomní Chování**](core/autonomous-behavior.md) - Systém "nudy" a autonomní rozhodování
- [**Paměťový Systém**](core/memory-system.md) - VectorStore a správa vzpomínek
- [**LLM Integrace**](core/llm-integration.md) - Lokální LLM model (llama-cpp)
- [**Resource Manager**](core/resource-manager.md) - Správa systémových zdrojů (4-tier system)
- [**Discord Client**](core/discord-client.md) - Discord bot integrace
- [**Error Tracking**](core/error-tracking.md) - Sledování a logování chyb
- [**Network Monitor**](core/network-monitor.md) - Monitorování připojení

### 📝 Skripty a Utility
- [**SSH Skripty**](scripts/ssh-scripts.md) - Připojení a správa RPI
- [**Údržbové Skripty**](scripts/maintenance.md) - Cleanup, swap, atd.
- [**Deployment**](scripts/deployment.md) - Nasazení na RPI

### 🔧 Konfigurace
- [**config_settings.py**](config/settings.md) - Nastavení agenta
- [**config_secrets.py**](config/secrets.md) - API klíče a tokeny
- [**Proměnné Prostředí**](config/environment.md) - Environment variables

### 📊 Datové Struktury
- [**Agent State**](data-structures/agent-state.md) - Stav agenta
- [**Memory Schema**](data-structures/memory-schema.md) - Databázové schéma
- [**Tool Stats**](data-structures/tool-stats.md) - Statistiky nástrojů

### 🔍 Pokročilé Témata
- [**Command Queue System**](advanced/command-queue.md) - Asynchronní zpracování příkazů
- [**Fuzzy Command Matching**](advanced/fuzzy-matching.md) - Automatická korekce překlep
- [**Learning Mode**](advanced/learning-mode.md) - Režim učení
- [**Boredom Mechanism**](advanced/boredom.md) - Systém "nudy"
- [**Tier System**](advanced/tier-system.md) - Reakční systém na zátěž

### 🐛 Řešení Problémů
- [**Časté Problémy**](troubleshooting/common-issues.md)
- [**LLM Issues**](troubleshooting/llm-issues.md)
- [**Discord Issues**](troubleshooting/discord-issues.md)
- [**RPI Issues**](troubleshooting/rpi-issues.md)

### 📚 Reference API
- [**AutonomousAgent**](api/autonomous-agent.md) - Hlavní třída agenta
- [**CommandHandler**](api/command-handler.md) - Handler pro příkazy
- [**VectorStore**](api/vector-store.md) - Paměťový systém
- [**LLMClient**](api/llm-client.md) - LLM klient

---

## O Projektu

**RPI AI Agent** je autonomní AI asistent běžící na Raspberry Pi, který komunikuje přes Discord a má schopnost:

- 🤖 **Autonomně se rozhodovat** - Na základě "nudy" a cílů
- 🧠 **Učit se** - Objevovat a používat nástroje
- 💾 **Pamatovat si** - Ukládat zkušenosti do SQLite databáze
- 🛠️ **Používat nástroje** - FileTool, WebTool, MathTool, atd.
- 💬 **Komunikovat** - Přes Discord s uživateli
- 📊 **Monitorovat** - Systémové zdroje a automaticky reagovat

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

### Klíčové Funkce

#### 🎯 Autonomní Rozhodování
Agent používá systém "boredom" (nudy), který postupně roste. Když dosáhne prahu, agent se autonomně rozhodne pro akci pomocí LLM.

#### 🛠️ Dynamické Nástroje
Agent může objevovat a učit se používat nástroje. Každý nástroj má:
- Název a popis
- `execute()` metodu
- Automatické logování použití

#### 💾 Paměťový Systém
SQLite databáze s FTS5 vyhledáváním pro:
- Ukládání akcí a zkušeností
- Konverzace s uživateli
- Naučené informace
- Relevantní filtrování

#### 📊 Resource Management
4-tier systém reagující na zatížení:
- **Tier 0** (< 85%): Normální provoz
- **Tier 1** (85%): Varování, cleanup
- **Tier 2** (90%): Aktivní mitigace, redukce LLM
- **Tier 3** (95%): Nouzový režim, ukončení procesů

### Technologie

- **Python 3.11+** - Hlavní jazyk
- **discord.py** - Discord bot framework
- **llama-cpp-python** - Lokální LLM (Qwen 2.5)
- **SQLite** - Databáze s FTS5
- **psutil** - Monitorování systému
- **asyncio** - Asynchronní operace

---

## Rychlý Start

### Prerekvizity
```bash
# Python 3.11+
python --version

# Instalace závislostí
pip install -r requirements.txt
```

### Konfigurace
1. Vytvoř `config_secrets.py`:
```python
DISCORD_TOKEN = "tvůj_discord_token"
DISCORD_CHANNEL_ID = 123456789  # Channel ID
ADMIN_USER_IDS = [987654321]    # Tvoje Discord ID
```

2. Nastav `config_settings.py` podle potřeby

### Spuštění
```bash
python main.py
```

---

## Příklady Použití

### Základní Příkazy
```
!help              # Zobraz nápovědu
!status            # Stav agenta
!stats             # Detailní statistiky
!tools             # Seznam nástrojů
```

### Interakce s AI
```
!ask co je to Python?
!teach Python je programovací jazyk
!search nejnovější zprávy o AI
!learn web_tool    # Nauč se konkrétní nástroj
```

### Administrace
```
!logs 50           # Posledních 50 řádků logů
!live logs 2m      # Live stream logů 2 minuty
!monitor 30        # Monitoruj zdroje 30 sekund
!restart           # Restart agenta
```

---

## Struktura Dokumentace

Každý dokument v této dokumentaci obsahuje:

- **📋 Přehled** - Co daná funkce/příkaz dělá
- **⚙️ Použití** - Jak to použít (příklady)
- **🔧 Parametry** - Dostupné parametry a volby
- **💡 Příklady** - Praktické ukázky
- **⚠️ Poznámky** - Důležité informace
- **🔗 Související** - Odkazy na související dokumenty

---

## Přispívání

Pro přidání funkcí nebo opravu chyb:
1. Prostuduj dokumentaci
2. Otestuj změny lokálně
3. Aktualizuj dokumentaci
4. Vytvoř pull request

## Licence

Tento projekt je pro osobní použití.

---

**Poslední aktualizace:** 2025-12-02  
**Verze Dokumentace:** 1.0.0
