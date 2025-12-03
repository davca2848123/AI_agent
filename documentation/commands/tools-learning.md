# Nástroje a Učení

> Příkazy pro práci s nástroji, učení a interakci s AI

## 📋 Přehled

Tyto příkazy umožňují agentovi učit se používat nástroje, klást otázky AI a učit AI nové věci.

---

## `!tools`

### 📋 Popis
Zobrazí seznam všech dostupných nástrojů s informacemi o jejich použití.

### ⚙️ Použití
```
!tools
```

### 💡 Co zobrazuje

Pro každý nástroj:
- **Název nástroje**
- **Status** - 🆕 New nebo ✅ Learned/Used X times
- **Poslední použití** - Datum a čas (pokud byl použit)
- **Popis** - Co nástroj dělá

### 📝 Příklad
```
User: !tools

Bot: 🛠️ **Available Tools:**

• `file_tool` - ✅ Learned/Used 18 times (Last: 2025-12-01 14:25)
  _Manage files and folders: create, read, write, delete, list directory contents_

• `web_tool` - ✅ Learned/Used 45 times (Last: 2025-12-02 09:15)
  _Search the web or read webpage content_

• `time_tool` - ✅ Learned/Used 38 times (Last: 2025-12-02 10:00)
  _Get current time, format dates, calculate time differences_

• `math_tool` - ✅ Learned/Used 22 times (Last: 2025-12-01 16:45)
  _Perform calculations, evaluate expressions, convert units_

• `weather_tool` - ✅ Learned/Used 12 times (Last: 2025-12-02 08:30)
  _Get weather information for any location_

• `code_tool` - 🆕 New
  _Execute Python code safely_
```

### ⚠️ Poznámky
- "Learned" znamená že nástroj byl alespoň jednou použit
- Timestamp je ve formátu `YYYY-MM-DD HH:MM`
- Statistiky se ukládají do `tool_stats.json`

### 🔗 Související
- [`!learn`](#learn) - Naučit se nástroj
- [`!stats`](basic.md#stats) - Zobraz top 5 nástrojů
- [Tool Implementations](../tools/) - Detaily o jednotlivých nástrojích

---

## `!learn`

### 📋 Popis
Přinutí agenta naučit se používat nástroj(e). Agent vyzkouší nástroj a uloží si zkušenost.

### ⚙️ Použití

**Jednorázové učení:**
```
!learn
```

**Specifický nástroj:**
```
!learn <tool_name>
```

**Všechny nástroje:**
```
!learn all
```

**Zastavit učení:**
```
!learn stop
```

### 🔧 Parametry

| Parametr | Popis | Příklad |
|----------|-------|---------|
| *(none)* | Jednorázové učení | `!learn` |
| `<tool_name>` | Naučit se konkrétní nástroj | `!learn web_tool` |
| `all` | Naučit se všechny nástroje postupně | `!learn all` |
| `stop` | Zastavit probíhající učení | `!learn stop` |

### 💡 Jak to funguje

**Jednorázové učení:**
```python
agent.actions_without_tools = 2  # Trigger learning
agent.boredom_score = 1.0  # Force immediate action
```

**Targeted/All Learning:**
```python
agent.learning_queue = [tool_name]  # nebo list všech
agent.is_learning_mode = True
agent.boredom_score = 1.0
```

### 📝 Příklady

**Jednorázové učení:**
```
User: !learn

Bot: 🎓 Forcing single learning session...
     ✅ Learning forced. I will try to learn something new now.

[Agent autonomously chooses a tool and tries it]
```

**Specifický nástroj:**
```
User: !learn weather

Bot: 🎓 **Targeted Learning:** `weather_tool`
     🚀 Learning sequence initiated for `weather_tool`!

[Agent tests weather_tool]
```

**Všechny nástroje:**
```
User: !learn all

Bot: 🎓 **Starting Comprehensive Learning Session**
     📋 Plan: I will systematically learn and test 8 tools.
     Tools: file_tool, web_tool, time_tool, math_tool, weather_tool, code_tool, wikipedia_tool, git_tool
     🚀 Learning sequence initiated!

[Agent learns each tool one by one]
```

**Zastavit:**
```
User: !learn stop

Bot: 🛑 **Learning Session Stopped.**
     Resuming normal autonomous behavior.
```

### ⚠️ Poznámky
- Learning mode nastaví `agent.is_learning_mode = True`
- Během učení agent postupně zpracovává `learning_queue`
- Partial match funguje (např. `!learn web` najde `web_tool`)
- Po dokončení učení se režim automaticky vrátí na normální

### 🔗 Související
- [Learning Mode](../advanced/learning-mode.md) - Jak learning mode funguje
- [Autonomous Behavior](../core/autonomous-behavior.md) - Jak agent rozhoduje

---

## `!ask`

### 📋 Popis
Zeptej se AI na otázku. Agent použije vhodné nástroje k nalezení odpovědi.

### ⚙️ Použití
```
!ask <otázka>
```

### 🔧 Podporované typy otázek

**Počasí:**
```
!ask počasí ostrava
!ask weather in Prague
```

**Matematika:**
```
!ask kolik je 15 * 234?
!ask what is square root of 144?
```

**Čas:**
```
!ask kolik je hodin?
!ask what time is it?
```

**Vyhledávání:**
```
!ask who is Elon Musk?
!ask co je to Python?
```

**Obecné otázky:**
```
!ask explain quantum physics
```

### 💡 Jak to funguje

1. **Detekce typu otázky** - Rozpozná weather, math, time queries
2. **Výběr nástroje** - LLM vybere vhodný nástroj
3. **Spuštění nástroje** - Zavolá `tool.execute()` s parametry
4. **Formulace odpovědi** - LLM vytvoří odpověď z výsledku

### 📝 Příklady

**Počasí:**
```
User: !ask počasí ostrava

Bot: [uses weather_tool]
     V Ostravě je momentálně 5°C, zataženo. Vlhkost vzduchu 78%.
```

**Matematika:**
```
User: !ask co je 234 * 567?

Bot: [uses math_tool]
     234 × 567 = 132,678
```

**Vyhledávání:**
```
User: !ask who invented Python?

Bot: [uses web_tool to search]
     Python was created by Guido van Rossum and first released in 1991...
```

### 🔧 Implementační detaily

**Tool Selection Prompt:**
```python
You are a helpful AI. User asked: "{question}"
Available tools: {tool_descriptions}
Use TOOL_CALL format to call tools.
```

**Tool Call Format:**
```
TOOL_CALL: tool_name
ARGS: {"param": "value"}
```

**Weather Detection:**
```python
weather_keywords = ['počasí', 'weather', 'teplota', 'temperature']
if any(kw in question.lower() for kw in weather_keywords):
    # Extract location and use weather_tool
```

### ⚠️ Poznámky
- LLM musí být dostupný (!status zkontroluje)
- Pokud je otázka příliš složitá, může selhat
- Agent si zapamatuje odpověď do memory
- Tool selection závisí na kvalitě LLM

### 🔗 Související
- [Tools](../tools/) - Dostupné nástroje
- [LLM Integration](../core/llm-integration.md) - Jak LLM funguje
- [`!search`](#search) - Specificky vyhledávání

---

## `!teach`

### 📋 Popis
Nauč agenta novou informaci, kterou si zapamatuje.

### ⚙️ Použití
```
!teach <informace>
```

### 💡 Jak to funguje

1. **Přijme informaci** - Text od uživatele
2. **Uloží do paměti** - Jako `user_teaching` type
3. **Potvrdí** - Vrátí potvrzení

### 📝 Příklady

```
User: !teach Python je programovací jazyk vytvořený Guido van Rossumem

Bot: ✅ Zapamatováno! Uložil jsem si: "Python je programovací jazyk..."
```

```
User: !teach My favorite color is blue

Bot: ✅ Got it! I've learned: "My favorite color is blue"
```

### 🔧 Implementace

```python
# Store in memory
memory.add_memory(
    content=info,
    metadata={
        "type": "user_teaching",
        "source": "!teach command",
        "timestamp": time.time()
    }
)
```

### ⚠️ Poznámky
- Informace se ukládá do SQLite databáze
- Agent může použít tuto informaci později v konverzaci
- Paměť je prohledávatelná pomocí FTS5
- Nepodstatné informace se mohou automaticky filtrovat

### 🔗 Související
- [Memory System](../core/memory-system.md) - Jak paměť funguje
- [`!memory`](data-management.md#memory) - Zobraz statistiky paměti

---

## `!search`

### 📋 Popis
Přikaž agentovi vyhledat informace na internetu.

### ⚙️ Použití
```
!search <dotaz>
```

### 💡 Jak to funguje

1. **Vytvoří autonomní akci** - „Research: {query}"
2. **Agent sám vyhledá** - Použije web_tool
3. **Reportuje výsledky** - Pošle do Discord kanálu

### 📝 Příklady

```
User: !search latest news about AI

Bot: 🔍 Researching: latest news about AI
     [Agent uses web_tool]
     📊 Found: Recent breakthroughs in AI include...
```

```
User: !search škola třinec

Bot: 🔍 Hledám: škola třinec
     [Results from DuckDuckGo]
```

### 🔧 Implementace

```python
# Create autonomous research action
action = f"Research: {query}"
agent.execute_action(action)
```

### ⚠️ Poznámky
- Vyžaduje funkční internet
- používá DuckDuckGo search
- Výsledky závisí na kvalitě vyhledávače
- Agent si zapamatuje nalezené informace

### 🔗 Související
- [WebTool](../tools/web-tool.md) - Detaily web_tool
- [`!ask`](#ask) - Pro interaktivní otázky

---

## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!tools` | Zobraz nástroje | `!tools` |
| `!learn` | Nauč se nástroj | `!learn web_tool` |
| `!learn all` | Nauč se vše | `!learn all` |
| `!learn stop` | Zastav učení | `!learn stop` |
| `!ask` | Zeptej se AI | `!ask počasí praha` |
| `!teach` | Nauč AI | `!teach Python je jazyk` |
| `!search` | Vyhledej | `!search AI news` |

---

**Poslední aktualizace:** 2025-12-02  
**Platné pro verzi:** 1.0.0
