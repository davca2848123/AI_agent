# Nástroje a Učení

> **Navigace:** [📂 Dokumentace](../README.md) | [💬 Příkazy](../README.md#commands-příkazy) | [Nástroje a učení](tools-learning.md)

> Příkazy pro práci s nástroji, učení a interakci s AI.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Tyto příkazy umožňují agentovi učit se používat nástroje, klást otázky AI a učit AI nové věci.

---

<a name="tools"></a>
## `!tools`

<a name="popis"></a>
### 📋 Popis
Zobrazí seznam všech dostupných nástrojů s informacemi o jejich použití.

<a name="použití"></a>
### ⚙️ Použití
```
!tools
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

Pro každý nástroj:

- **Název nástroje**
- **Status** - 🆕 New nebo ✅ Learned/Used X times
- **Poslední použití** - Datum a čas (pokud byl použit)
- **Popis** - Co nástroj dělá

<a name="příklad"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky
- "Learned" znamená že nástroj byl alespoň jednou použit
- Timestamp je ve formátu `YYYY-MM-DD HH:MM`
- Statistiky se ukládají do `tool_stats.json`

<a name="související"></a>
### 🔗 Související
- [`!learn`](#learn) - Naučit se nástroj
- [`!stats`](basic.md#stats) - Zobraz top 5 nástrojů
- [Tool Implementations](../tools/all-tools.md) - Detaily o jednotlivých nástrojích

---

<a name="learn"></a>
## `!learn`

<a name="popis"></a>
### 📋 Popis
Přinutí agenta naučit se používat nástroj(e). Agent vyzkouší nástroj a uloží si zkušenost.

<a name="použití"></a>
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

**Fronta učení:**
```
!learn queue
```

**Zastavit učení:**
```
!learn stop
```

<a name="parametry"></a>
### 🔧 Parametry

| Parametr | Popis | Příklad |
|----------|-------|---------|
| *(none)* | Jednorázové učení | `!learn` |
| `<tool_name>` | Naučit se konkrétní nástroj | `!learn web_tool` |
| `all` | Naučit se všechny nástroje postupně | `!learn all` |
| `queue` | Zobrazit aktuální frontu nástrojů k učení | `!learn queue` |
| `stop` | Zastavit probíhající učení | `!learn stop` |

<a name="jak-to-funguje"></a>
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

**Queue Management:**

- `!learn queue` zobrazí seznam nástrojů čekajících na naučení
- `!learn stop` vyprázdní frontu a vypne learning mode

<a name="příklady"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky

- Learning mode nastaví `agent.is_learning_mode = True`
- Během učení agent postupně zpracovává `learning_queue`
- Partial match funguje (např. `!learn web` najde `web_tool`)
- Po dokončení učení se režim automaticky vrátí na normální

<a name="související"></a>
### 🔗 Související
- [📖 Autonomous Behavior](../core/autonomous-behavior.md) - Jak agent rozhoduje

---

<a name="ask"></a>
## `!ask`

<a name="popis"></a>
### 📋 Popis
Zeptej se AI na otázku. Agent použije vhodné nástroje k nalezení odpovědi.

<a name="použití"></a>
### ⚙️ Použití
```
!ask <otázka>
```

<a name="podporované-typy-otázek"></a>
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

<a name="jak-to-funguje"></a>
### 💡 Jak to funguje

1. **Detekce typu otázky** - Rozpozná weather, math, time queries
2. **Výběr nástroje** - LLM vybere vhodný nástroj
3. **Spuštění nástroje** - Zavolá `tool.execute()` s parametry
4. **Formulace odpovědi** - LLM vytvoří odpověď z výsledku

<a name="příklady"></a>
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

<a name="implementační-detaily"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky

- LLM musí být dostupný (!status zkontroluje)
- Pokud je otázka příliš složitá, může selhat
- Agent si zapamatuje odpověď do memory
- Tool selection závisí na kvalitě LLM

<a name="související"></a>
### 🔗 Související
- [📖 Tools](../tools/all-tools.md) - Dostupné nástroje
- [📖 LLM Integration](../core/llm-integration.md) - Jak LLM funguje
- [`!search`](#search) - Specificky vyhledávání

---

<a name="teach"></a>
## `!teach`

<a name="popis"></a>
### 📋 Popis
Nauč agenta novou informaci, kterou si zapamatuje.

<a name="použití"></a>
### ⚙️ Použití
```
!teach <informace>
```

<a name="jak-to-funguje"></a>
### 💡 Jak to funguje

1. **Přijme informaci** - Text od uživatele
2. **Uloží do paměti** - Jako `user_teaching` type
3. **Potvrdí** - Vrátí potvrzení

<a name="příklady"></a>
### 📝 Příklady

```
User: !teach Python je programovací jazyk vytvořený Guido van Rossumem

Bot: ✅ Zapamatováno! Uložil jsem si: "Python je programovací jazyk..."
```

```
User: !teach My favorite color is blue

Bot: ✅ Got it! I've learned: "My favorite color is blue"
```

<a name="implementace"></a>
### 🔧 Implementace

```python
async def cmd_teach(self, channel_id: int, info: str):
    # Store as a high-priority memory
    self.agent.memory.add_memory(
        content=f"User taught me: {info}",
        metadata={"type": "user_teaching", "importance": "high", "taught_by_user": True}
    )
    
    self.agent.successful_learnings += 1
```

**⭐ Důležité:** `!teach` memories **VŽDY** projdou bez ohledu na scoring!

```python
# V memory.py - add_memory()
metadata_type = metadata.get("type") if metadata else None

if metadata_type == "user_teaching":
    # BYPASS scoring system!
    # User teaching is always valuable
    logger.info("user_teaching type - bypassing score check")
    # Save directly to database
```

<a name="scoring-bypass"></a>
### 🔓 Scoring Bypass

Zatímco normální vzpomínky musí projít [scoring systémem](../core/memory-system.md#advanced-scoring-system), `!teach` příkaz má **garantované uložení**:

| Typ Vzpomínky | Scoring | Uloženo? |
|---------------|---------|----------|
| Normální akce | ✅ Ano (min 70 pts) | ❓ Možná |
| LLM response | ✅ Ano (min 70 pts) | ❓ Možná |
| **!teach příkaz** | ❌ **BYPASS** | ✅ **Vždy** |
| user_teaching | ❌ **BYPASS** | ✅ **Vždy** |

**Důvod:** Uživatelské učení je vždy cenné a nesmí být odmítnuto kvůli nízkému skóre.

<a name="poznámky"></a>
### ⚠️ Poznámky

- **Informace se VŽDY uloží** - Není filtrováno scoring systémem
- Agent může použít tuto informaci později v konverzaci
- Paměť je prohledávatelná pomocí FTS5
- Každé `!teach` zvýší `successful_learnings` counter

<a name="související"></a>
### 🔗 Související
- [📖 Memory System](../core/memory-system.md) - Jak paměť funguje
- [`!memory`](data-management.md#memory) - Zobraz statistiky paměti

---

<a name="search"></a>
## `!search`

<a name="popis"></a>
### 📋 Popis
Přikaž agentovi vyhledat informace na internetu.

<a name="použití"></a>
### ⚙️ Použití
```
!search <dotaz>
```

<a name="jak-to-funguje"></a>
### 💡 Jak to funguje

1. **Vytvoří autonomní akci** - „Research: {query}"
2. **Agent sám vyhledá** - Použije web_tool
3. **Reportuje výsledky** - Pošle do Discord kanálu

<a name="příklady"></a>
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

<a name="implementace"></a>
### 🔧 Implementace

```python
# Create autonomous research action
action = f"Research: {query}"
agent.execute_action(action)
```

<a name="poznámky"></a>
### ⚠️ Poznámky

- Vyžaduje funkční internet
- používá DuckDuckGo search
- Výsledky závisí na kvalitě vyhledávače
- Agent si zapamatuje nalezené informace

<a name="související"></a>
### 🔗 Související
- [📖 WebTool](../tools/all-tools.md#webtool) - Detaily web_tool
- [`!ask`](#ask) - Pro interaktivní otázky

---

<a name="souhrn"></a>
## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!tools` | Zobraz nástroje | `!tools` |
| `!learn` | Nauč se nástroj | `!learn web_tool` |
| `!learn all` | Nauč se vše | `!learn all` |
| `!learn queue` | Zobraz frontu | `!learn queue` |
| `!learn stop` | Zastav učení | `!learn stop` |
| `!ask` | Zeptej se AI | `!ask počasí praha` |
| `!teach` | Nauč AI | `!teach Python je jazyk` |
| `!search` | Vyhledej | `!search AI news` |


<a name="související"></a>
## 🔗 Související

- [📋 Všechny příkazy](../SUMMARY.md#commands-api)
- [🏗️ Command Architecture](../architecture.md#command-layer)
- [🆘 Troubleshooting](../troubleshooting.md#command-errors)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
