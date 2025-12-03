# Všechny Nástroje (Tools) - Kompletní Přehled

> Detailní dokumentace všech dostupných nástrojů agenta

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
9. **[GitTool](#gittool)** - Git operace
10. **[DatabaseTool](#databasetool)** - SQLite dotazy
11. **[RSSTool](#rsstool)** - Ze čtení RSS feedů
12. **[TranslateTool](#translatetool)** - Překlady textu
13. **[WikipediaTool](#wikipediatool)** - Vyhledávání na Wikipedii
14. **[DiscordActivityTool](#discordactivitytool)** - Sledování Discord aktivit

---

## FileTool

### 📋 Popis
Umožňuje číst, zapisovat a listovat soubory v projektu.

### 🔧 Parametry

**Action types:**
- `read` - Přečti obsah souboru
- `write` - Zapiš do souboru
- `list_files` - Seznam souborů v adresáři

**Parametry:**
- `action` *(required)* - Typ akce
- `filename` *(optional)* - Cesta k souboru
- `content` *(optional)* - Obsah pro zápis

### 💡 Příklady

```python
# Read file
file_tool.execute(action="read", filename="README.md")

# Write file
file_tool.execute(action="write", filename="test.txt", content="Hello World")

# List files
file_tool.execute(action="list_files", filename=".")
```

### ⚠️ Security
- Přístup pouze v rámci workspace directory
- Filtruje hidden files (.*)
- Ignoruje `__pycache__`, `venv`, `node_modules`

---

## SystemTool

### 📋 Popis
Poskytuje informace o systému (CPU, RAM, Disk, Procesy).

### 🔧 Parametry

**Actions:**
- `info` - Základní systémové info
- `process_list` - Top 5 procesů podle paměti

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

## WebTool

### 📋 Popis
Vyhledává na webu pomocí DuckDuckGo a čte obsah webových stránek.

### 🔧 Parametry

**Actions:**
- `search` - Vyhledej na webu
- `read` - Přečti webovou stránku

**Parametry:**
- `query` - Vyhledávací dotaz (pro search)
- `url` - URL stránky (pro read)
- `limit` - Max délka textu (default 1000)

### 💡 Příklady

```python
# Search
web_tool.execute(action="search", query="Python tutorial")

# Read webpage
web_tool.execute(action="read", url="https://example.com")
```

### ⚠️ Poznámky
- Vyžaduje `duckduckgo_search`, `bs4`, `aiohttp`
- Search vrací max 3 výsledky
- Read extrahuje text pomocí BeautifulSoup

---

## TimeTool

### 📋 Popis
Práce s časem - aktuální čas, formátování, rozdíly.

### 🔧 Parametry

**Actions:**
- `now` - Aktuální čas
- `format` - Formátovaný čas
- `diff` - Rozdíl mezi dvěma časy

**Parametry:**
- `format_str` - Formát (např. "%Y-%m-%d %H:%M:%S")
- `time1`, `time2` - ISO formát časů pro diff

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

## MathTool

### 📋 Popis
Matematické výpočty, konverze jednotek.

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

### ⚠️ Poznámky
- Calc používá `eval()` s omezeným scope (bezpečné)
- Podporované funkce: abs, round, min, max, sum, sqrt, sin, cos, tan

---

## WeatherTool

### 📋 Popis
Získá aktuální počasí pro zadanou lokaci pomocí wttr.in.

### 🔧 Parametry

- `location` *(optional)* - Název města (default z config)

### 💡 Příklady

```python
# Weather for location
weather_tool.execute(location="Praha")
weather_tool.execute(location="London")

# Default location
weather_tool.execute()
```

### ⚠️ Poznámky
- Používá wttr.in (zdarma, bez API klíče)
- Timeout 30s (wttr.in může být pomalý)
- Default lokace: `config_settings.DEFAULT_LOCATION`

### 📝 Výstup Format

```
Weather: Praha: Clear +5°C 78% ↓15km/h
```

---

## CodeTool

### 📋 Popis
Bezpečné spouštění Python kódu v omezeném sandboxu.

### 🔧 Parametry

- `code` *(required)* - Python kód ke spuštění

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

### ⚠️ Security
- Velmi omezený sandbox
- Povolené built-ins: print, len, range, str, int, float, list, dict, sum, max, min, abs
- Import není povolen
- File I/O není povolen

---

## NoteTool

### 📋 Popis
Ukládání a správa poznámek do JSON souboru.

### 🔧 Parametry

**Actions:**
- `add` - Přidej poznámku
- `list` - Seznam poznámek
- `search` - Vyhledej v poznámkách

**Parameters:**
- `content` - Text poznámky
- `tag` - Štítek (optional, default "general")

### 💡 Příklady

```python
# Add note
note_tool.execute(action="add", content="Remember to check logs", tag="todo")

# List notes
note_tool.execute(action="list")

# Search notes
note_tool.execute(action="search", content="logs")
```

### 📝 Storage
- Soubor: `workspace/notes.json`
- Format: JSON array s ID, content, tag, timestamp

---

## GitTool

### 📋 Popis
Základní Git operace (status, log) pomocí dulwich.

### 🔧 Parametry

**Actions:**
- `status` - Git status
- `log` - Git log (5 posledních commitů)

**Parameters:**
- `repo_path` *(optional)* - Cesta k repozitáři (default ".")

### 💡 Příklady

```python
# Git status
git_tool.execute(action="status")

# Git log
git_tool.execute(action="log")
```

### ⚠️ Poznámky
- Vyžaduje `dulwich` balíček
- Pouze read-only operace
- Commit/push nejsou podporovány (bezpečnost)

---

## DatabaseTool

### 📋 Popis
Spouštění SELECT dotazů na SQLite databázi.

### 🔧 Parametry

- `query` *(required)* - SQL SELECT dotaz

### 💡 Příklady

```python
# Simple SELECT
database_tool.execute(query="SELECT * FROM users LIMIT 10")

# Filtered query
database_tool.execute(query="SELECT name, email FROM users WHERE active=1")
```

### ⚠️ Security
- **POUZE SELECT dotazy**
- INSERT/UPDATE/DELETE/DROP jsou zakázány
- Databáze: `workspace/agent.db`
- Max 10 řádků výstupu

---

## RSSTool

### 📋 Popis
Čtení RSS/Atom feedů pomocí feedparser.

### 🔧 Parametry

- `url` *(required)* - URL RSS feedu

### 💡 Příklady

```python
# Read RSS feed
rss_tool.execute(url="https://example.com/feed.xml")
```

### 📝 Výstup
- Název feedu
- 5 nejnovějších článků (title + link)

### ⚠️ Poznámky
- Vyžaduje `feedparser` balíček

---

## TranslateTool

### 📋 Popis
Překládá text mezi jazyky pomocí Google Translate API.

### 🔧 Parametry

- `text` *(required)* - Text k překladu
- `source` *(optional)* - Zdrojový jazyk (default "auto")
- `target` *(optional)* - Cílový jazyk (default "en")

### 💡 Příklady

```python
# Auto-detect to English
translate_tool.execute(text="Ahoj světe")

# Czech to German
translate_tool.execute(text="Dobrý den", source="cs", target="de")
```

### ⚠️ Poznámky
- Vyžaduje `deep-translator` balíček
- Používá Google Translate (zdarma, s limity)

---

## WikipediaTool

### 📋 Popis
Vyhledává články na Wikipedii.

### 🔧 Parametry

- `query` *(required)* - Vyhledávací dotaz
- `lang` *(optional)* - Jazyk Wikipedia (default "en")

### 💡 Příklady

```python
# English Wikipedia
wikipedia_tool.execute(query="Python programming")

# Czech Wikipedia
wikipedia_tool.execute(query="Albert Einstein", lang="cs")
```

### 📝 Výstup
- Název článku
- Summary (prvních 500 znaků)
- URL článku

### ⚠️ Poznámky
- Vyžaduje `wikipediaapi` balíček
- Pokud článek neexistuje, vrátí chybu

---

## DiscordActivityTool

### 📋 Popis
Sleduje aktivity (hry) uživatelů na Discord serveru.

### 🔧 Parametry
*(žádné)*

### 💡 Příklady

```python
# Check activities
discord_activity_tool.execute()
```

### 📝 Výstup

```
Current User Activities:
- John is playing/doing: Minecraft
- Sarah is playing/doing: Spotify
```

### ⚠️ Poznámky
- Vyžaduje Discord připojení
- Vyžaduje internet
- Automaticky researche neznámé aktivity
- Ukládá aktivity do paměti

---

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

## 📊 Tool Execution Wrapper

Každý nástroj má wrapper `_execute_with_logging()` který:

1. **Loguje parametry** - S bezpečným sanitizací
2. **Měří čas** - Elapsed time v sekundách
3. **Mapuje parametry** - Inteligentní mapping `query` → tool-specific params
4. **Zachytává errors** - Type hned nebo obecné exceptions
5. **Loguje výsledky** - S truncated output

### Příklad logu

```
INFO: web_tool: Starting with params: {'action': 'search', 'query': 'Python tutorial'}
INFO: web_tool: Completed in 1.23s - Result: Search Results:
1. Python Tutorial...
```

---

## 🔗 Související

- [Commands - Tools & Learning](../commands/tools-learning.md) - Příkazy pro práci s nástroji
- [Autonomous Behavior](../core/autonomous-behavior.md) - Jak agent vybírá nástroje
- [LLM Integration](../core/llm-integration.md) - Jak LLM volá nástroje

---

**Poslední aktualizace:** 2025-12-02  
**Verze:** 1.0.0
