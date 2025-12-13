# Všechny Nástroje (Tools) - Kompletní Přehled

> **Navigace:** [📂 Dokumentace](../README.md) | [🛠️ Nástroje](../README.md#tools-nástroje) | [Všechny nástroje](all-tools.md)

> Detailní dokumentace všech dostupných nástrojů agenta.
> **Verze:** Beta - CLOSED

---

<a name="seznam-nástrojů"></a>
## 📋 Seznam Nástrojů

Agent má k dispozici následující nástroje:

1. **[FileTool](#filetool)** - Práce se soubory
2. **[SystemTool](#systemtool)** - Systémové informace
3. **[WebTool](#webtool)** - Vyhledávání a čtení webu
4. **[TimeTool](#timetool)** - Práce s časem
5. **[MathTool](#mathtool)** - Matematické výpočty
6. **[WeatherTool](#weathertool)** - Informace o počasí
7. **[CodeTool](#codetool)** - Spouštění Python kódu
8. **[NoteTool](#notetool)** - Správa poznámek
9. **[DatabaseTool](#databasetool)** - SQLite dotazy
10. **[RSSTool](#rsstool)** - Ze čtení RSS feedů
11. **[TranslateTool](#translatetool)** - Překlady textu
12. **[WikipediaTool](#wikipediatool)** - Vyhledávání na Wikipedii
13. **[DiscordActivityTool](#discordactivitytool)** - Sledování Discord aktivit

---

<a name="filetool"></a>
## FileTool

<a name="popis"></a>
### 📋 Popis
Umožňuje číst, zapisovat a listovat soubory v projektu.

<a name="parametry"></a>
### 🔧 Parametry

**Action types:**
- `read` - Přečti obsah souboru
- `write` - Zapiš do souboru
- `list_files` - Seznam souborů v adresáři

**Parametry:**
- `action` *(required)* - Typ akce
- `filename` *(optional)* - Cesta k souboru
- `content` *(optional)* - Obsah pro zápis

<a name="příklady"></a>
### 💡 Příklady

```python
# Read file
file_tool.execute(action="read", filename="README.md")

# Write file
file_tool.execute(action="write", filename="test.txt", content="Hello World")

# List files
file_tool.execute(action="list_files", filename=".")
```

<a name="security"></a>
### ⚠️ Security
- Přístup pouze v rámci `agent_workspace` directory
- Ochrana proti accidental modification of core project files
- Filtruje hidden files (.*)
- Ignoruje `__pycache__`, `venv`, `node_modules`

---

<a name="systemtool"></a>
## SystemTool

<a name="popis"></a>
### 📋 Popis
Poskytuje informace o systému (CPU, RAM, Disk, Procesy).

<a name="parametry"></a>
### 🔧 Parametry

**Actions:**
- `info` - Základní systémové info
- `process_list` - Top 5 procesů podle paměti

<a name="příklady"></a>
### 💡 Příklady

```python
# System info
system_tool.execute(action="info")
# Output: OS, CPU%, RAM%, Disk%

# Process list
system_tool.execute(action="process_list")
# Output: Top 5 processes
```

---

<a name="webtool"></a>
## WebTool

<a name="popis"></a>
### 📋 Popis
Vyhledává na webu pomocí DuckDuckGo a čte obsah webových stránek.

<a name="parametry"></a>
### 🔧 Parametry

**Actions:**
- `search` - Vyhledej na webu
- `read` - Přečti webovou stránku

**Parametry:**
- `action` *(optional)* - Typ akce. Pokud chybí, automaticky detekováno:
    - `"read"` pokud je přítomno `url`
    - `"search"` pokud je přítomno `query`
- `query` - Vyhledávací dotaz (pro search)
- `url` - URL stránky (pro read)
- `limit` - Max délka textu (default 1000)

<a name="příklady"></a>
### 💡 Příklady

```python
# Search (explicit action)
web_tool.execute(action="search", query="Python tutorial")

# Search (implicit action)
web_tool.execute(query="Jak uvařit guláš?")

# Read webpage (implicit action)
web_tool.execute(url="https://example.com")
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Vyžaduje `duckduckgo_search`, `bs4`, `aiohttp`
- **Robustness**: Tool automaticky doplňuje chybějící `action` na základě argumentů, což zabraňuje pádům při autonomním volání LLM.
- **Lokální vyhledávání**: Automaticky upravuje dotazy pro preferenci obsahu v češtině, slovenštině a angličtině (přidává filtr `lang:cs OR lang:sk OR lang:en`).
- Search vrací max 3 výsledky
- Read extrahuje text pomocí BeautifulSoup
- **Smart Memory Integration**: Při čtení stránky (`action='read'`) je obsah automaticky zpracován LLM (filtered) a uložen do paměti agenta jako `web_knowledge`.

---

<a name="timetool"></a>
## TimeTool

<a name="popis"></a>
### 📋 Popis
Práce s časem - aktuální čas, formátování, rozdíly.

<a name="parametry"></a>
### 🔧 Parametry

**Actions:**
- `now` - Aktuální čas
- `format` - Formátovaný čas
- `diff` - Rozdíl mezi dvěma časy

**Parametry:**
- `format_str` - Formát (např. "%Y-%m-%d %H:%M:%S")
- `time1`, `time2` - ISO formát časů pro diff

<a name="příklady"></a>
### 💡 Příklady

```python
# Current time
time_tool.execute(action="now")

# Formatted time
time_tool.execute(action="format", format_str="%A, %B %d, %Y")

# Time difference
time_tool.execute(action="diff", time1="2025-12-01T10:00:00", time2="2025-12-02T15:30:00")
```

---

<a name="mathtool"></a>
## MathTool

<a name="popis"></a>
### 📋 Popis
Matematické výpočty, konverze jednotek.

<a name="parametry"></a>
### 🔧 Parametry

**Actions:**
- `calc` - Vyhodnoť matematický výraz
- `sqrt` - Druhá odmocnina
- `pow` - Mocnina
- `convert` - Konverze jednotek (C↔F)

**Parametry:**
- `expression` - Matematický výraz
- `value` - Hodnota pro sqrt/convert
- `base`, `exponent` - Pro mocninu
- `unit`, `to_unit` - Pro konverzi

<a name="příklady"></a>
### 💡 Příklady

```python
# Calculate
math_tool.execute(action="calc", expression="234 * 567")

# Square root
math_tool.execute(action="sqrt", value=144)

# Power
math_tool.execute(action="pow", base=2, exponent=10)

# Temperature conversion
math_tool.execute(action="convert", value=25, unit="C", to_unit="F")
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Calc používá `eval()` s omezeným scope (bezpečné)
- Podporované funkce: abs, round, min, max, sum, sqrt, sin, cos, tan

---

<a name="weathertool"></a>
## WeatherTool

<a name="popis"></a>
### 📋 Popis
Získá aktuální počasí pro zadanou lokaci pomocí wttr.in.

<a name="parametry"></a>
### 🔧 Parametry

- `location` *(optional)* - Název města (default z config)

<a name="příklady"></a>
### 💡 Příklady

```python
# Weather for location
weather_tool.execute(location="Praha")
weather_tool.execute(location="London")

# Default location
weather_tool.execute()
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Používá wttr.in (zdarma, bez API klíče)
- Timeout 30s (wttr.in může být pomalý)
- Default lokace: `config_settings.DEFAULT_LOCATION`

<a name="výstup-format"></a>
### 📝 Výstup Format

```
Weather: Praha: Clear +5°C 78% ↓15km/h
```

---

<a name="codetool"></a>
## CodeTool

<a name="popis"></a>
### 📋 Popis
Bezpečné spouštění Python kódu v omezeném sandboxu.

<a name="parametry"></a>
### 🔧 Parametry

- `code` *(required)* - Python kód ke spuštění

<a name="příklady"></a>
### 💡 Příklady

```python
# Simple calculation
code_tool.execute(code="print(2 + 2)")

# Loop example
code_tool.execute(code="""
for i in range(5):
    print(f"Number: {i}")
""")
```

<a name="security"></a>
### ⚠️ Security
- Velmi omezený sandbox
- Povolené built-ins: print, len, range, str, int, float, list, dict, sum, max, min, abs
- Import není povolen
- File I/O není povolen

---

<a name="notetool"></a>
## NoteTool

<a name="popis"></a>
### 📋 Popis
Ukládání a správa poznámek do JSON souboru.

<a name="parametry"></a>
### 🔧 Parametry

**Actions:**
- `add` - Přidej poznámku
- `list` - Seznam poznámek
- `search` - Vyhledej v poznámkách

**Parameters:**
- `content` - Text poznámky
- `tag` - Štítek (optional, default "general")

<a name="příklady"></a>
### 💡 Příklady

```python
# Add note
note_tool.execute(action="add", content="Remember to check logs", tag="todo")

# List notes
note_tool.execute(action="list")

# Search notes
note_tool.execute(action="search", content="logs")
```

<a name="storage"></a>
### 📝 Storage
- Soubor: `agent_workspace/notes.json`
- Format: JSON array s ID, content, tag, timestamp

---

---

<a name="databasetool"></a>
## DatabaseTool

<a name="popis"></a>
### 📋 Popis
Spouštění SELECT dotazů na SQLite databázi.

<a name="parametry"></a>
### 🔧 Parametry

- `query` *(required)* - SQL SELECT dotaz

<a name="příklady"></a>
### 💡 Příklady

```python
# Simple SELECT
database_tool.execute(query="SELECT * FROM users LIMIT 10")

# Filtered query
database_tool.execute(query="SELECT name, email FROM users WHERE active=1")
```

<a name="security"></a>
### ⚠️ Security
- **POUZE SELECT dotazy**
- INSERT/UPDATE/DELETE/DROP jsou zakázány
- Databáze: `agent_workspace/agent.db`
- Max 10 řádků výstupu

---

<a name="rsstool"></a>
## RSSTool

<a name="popis"></a>
### 📋 Popis
Čtení RSS/Atom feedů pomocí feedparser.

<a name="parametry"></a>
### 🔧 Parametry

- `url` *(required)* - URL RSS feedu

<a name="příklady"></a>
### 💡 Příklady

```python
# Read RSS feed
rss_tool.execute(url="https://example.com/feed.xml")
```

<a name="výstup"></a>
### 📝 Výstup
- Název feedu
- 5 nejnovějších článků (title + link)

<a name="poznámky"></a>
### ⚠️ Poznámky
- Vyžaduje `feedparser` balíček

---

<a name="translatetool"></a>
## TranslateTool

<a name="popis"></a>
### 📋 Popis
Překládá text mezi jazyky pomocí Google Translate API.

<a name="parametry"></a>
### 🔧 Parametry

- `text` *(required)* - Text k překladu
- `source` *(optional)* - Zdrojový jazyk (default "auto")
- `target` *(optional)* - Cílový jazyk (default "en")

<a name="příklady"></a>
### 💡 Příklady

```python
# Auto-detect to English
translate_tool.execute(text="Ahoj světe")

# Czech to German
translate_tool.execute(text="Dobrý den", source="cs", target="de")
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Vyžaduje `deep-translator` balíček
- Používá Google Translate (zdarma, s limity)

---

<a name="wikipediatool"></a>
## WikipediaTool

<a name="popis"></a>
### 📋 Popis
Vyhledává články na Wikipedii.

<a name="parametry"></a>
### 🔧 Parametry

- `query` *(required)* - Vyhledávací dotaz
- `lang` *(optional)* - Jazyk Wikipedia (default "en")

<a name="příklady"></a>
### 💡 Příklady

```python
# English Wikipedia
wikipedia_tool.execute(query="Python programming")

# Czech Wikipedia
wikipedia_tool.execute(query="Albert Einstein", lang="cs")
```

<a name="výstup"></a>
### 📝 Výstup
- Název článku
- Summary (prvních 500 znaků)
- URL článku

<a name="poznámky"></a>
### ⚠️ Poznámky
- Vyžaduje `wikipediaapi` balíček
- Pokud článek neexistuje, vrátí chybu

---

<a name="discordactivitytool"></a>
## DiscordActivityTool

<a name="popis"></a>
### 📋 Popis
Sleduje aktivity (hry) uživatelů na Discord serveru.

<a name="parametry"></a>
### 🔧 Parametry
*(žádné)*

<a name="příklady"></a>
### 💡 Příklady

```python
# Check activities
discord_activity_tool.execute()
```

<a name="výstup"></a>
### 📝 Výstup

```
Current User Activities:
- John is playing/doing: Minecraft
- Sarah is playing/doing: Spotify
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Vyžaduje Discord připojení
- Vyžaduje internet
- **Activity Enrichment**: Automaticky provede web search pro nové/neznámé aktivity
- Ukládá shrnutí aktivity do paměti jako `activity_knowledge`

---

<a name="tool-registry"></a>
## 🔧 Tool Registry

Všechny nástroje jsou registrovány v `ToolRegistry` třídě:

```python
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.usage_stats: Dict[str, int] = {}
    
    def register(self, tool: Tool):
        # Registruje nástroj
        
    def get_tool(self, name: str) -> Tool:
        # Vrátí nástroj podle jména
        
    def increment_usage(self, name: str):
        # Zvýší počítadlo použití
```

<a name="registrace-v-agentovi"></a>
### Registrace v Agentovi

```python
# V agent/core.py
self.tools = ToolRegistry()
self.tools.register(FileTool())
self.tools.register(SystemTool())
self.tools.register(WebTool())
# ... atd
```

---

<a name="tool-execution-wrapper"></a>
## 📊 Tool Execution Wrapper

Každý nástroj má wrapper `_execute_with_logging()` který:

1. **Loguje parametry** - S bezpečným sanitizací
2. **Měří čas** - Elapsed time v sekundách
3. **Mapuje parametry** - Inteligentní mapping `query` → tool-specific params
4. **Zachytává errors** - Type hned nebo obecné exceptions
5. **Loguje výsledky** - S truncated output

<a name="příklad-logu"></a>
### Příklad logu

```
INFO: web_tool: Starting with params: {'action': 'search', 'query': 'Python tutorial'}
INFO: web_tool: Completed in 1.23s - Result: Search Results:
1. Python Tutorial...
```

---

<a name="související"></a>
## 🔗 Související

- [📖 Commands - Tools & Learning](../commands/tools-learning.md) - Příkazy pro práci s nástroji
- [📖 Autonomous Behavior](../core/autonomous-behavior.md) - Jak agent vybírá nástroje
- [📖 LLM Integration](../core/llm-integration.md) - Jak LLM volá nástroje
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-13  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
