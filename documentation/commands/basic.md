# Základní Příkazy

> **Navigace:** [📂 Dokumentace](../README.md) | [💬 Příkazy](../README.md#commands-příkazy) | [Základní příkazy](basic.md)

> Základní příkazy pro interakci s agentem a zobrazení stavu.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Základní příkazy poskytují přístup k nápovědě, stavu agenta a statistikám. Tyto příkazy jsou dostupné všem uživatelům.

---

<a name="help"></a>
## `!help`

<a name="popis"></a>
### 📋 Popis
Zobrazí kompletní seznam všech dostupných příkazů s krátkým popisem jejich funkcí.

<a name="použití"></a>
### ⚙️ Použití
```
!help
```

<a name="výstup"></a>
### 💡 Výstup
Příkaz vrátí strukturovanou zprávu obsahující:

- **Základní funkce** - `!help`, `!status`, `!stats`, `!intelligence`
- **Nástroje a učení** - `!tools`, `!learn`, `!ask`, `!teach`, `!search`
- **Správa dat** - `!memory`, `!logs`, `!live`, `!export`
- **Interakce** - `!mood`, `!goals`, `!config`
- **Administrace** - `!restart`, `!monitor`, `!ssh`, `!cmd`, `!debug`

<a name="příklad"></a>
### 📝 Příklad
```
User: !help

Bot: 📋 **Available Commands:**

**Format:** `[]` = optional, `<>` = required

**✅ Core Functions:**
• `!help` – Show this help message
• `!status` – Show agent status with system info
• `!stats` – Detailed statistics
...
```

<a name="související"></a>
### 🔗 Související
- [📖 Administrace](admin.md) - Pro admin příkazy
- [📖 Nástroje a učení](tools-learning.md) - Pro work s nástroji

---

<a name="documentation"></a>
## `!documentation` / `!docs`

<a name="popis"></a>
### 📋 Popis
Otevře interaktivní dokumentaci přímo v Discordu nebo odkáže na webovou verzi.

<a name="použití"></a>
### ⚙️ Použití
```
!documentation
!docs
```

<a name="příklad"></a>
### 📝 Příklad
```
User: !docs

Bot: 📚 **AI Agent Documentation**
     Vyberte kategorii:
     [Basic] [Tools] [Admin] [Web]
```

<a name="související"></a>
### 🔗 Související
- [`!help`](#help) - Základní nápověda
- [`!web`](#web) - Web interface

---

<a name="web"></a>
## `!web`

<a name="popis"></a>
### 📋 Popis
Správa webového rozhraní (Flask server + ngrok tunnel).

<a name="použití"></a>
### ⚙️ Použití

**Start:**
```
!web start
!web
```

**Stop:**
```
!web stop
```

**Restart:**
```
!web restart
```

<a name="příklady"></a>
### 📝 Příklady

```
User: !web start

Bot: 🌐 Starting web tunnel...
     ✅ **Web Interface Online!**
     [🏠 Dashboard] [📚 Documentation]
```

<a name="související"></a>
### 🔗 Související
- [`!info`](#info) - Systémové informace
- [`!status`](#status) - Stav agenta

---

<a name="status"></a>
## `!status`

<a name="popis"></a>
### 📋 Popis
Zobrazí aktuální stav agenta včetně diagnostických kontrol LLM, internetu a disku. Obsahuje tlačítko pro zobrazení detailních statistik.

<a name="použití"></a>
### ⚙️ Použití
```
!status
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

**Základní informace:**

- Hostname a operační systém
- Stav běhu agenta

**Diagnostika:**
- **LLM Status** - Zda je LLM dostupný + latence v ms + typ providera (Local/Cloud)
- **Internet** - Ping test na 8.8.8.8
- **Disk Free** - Volné místo na disku v GB

**Interaktivní prvky:**
- Tlačítko **"Zobrazit detailní statistiky"** - Spustí `!stats` příkaz

<a name="příklad"></a>
### 📝 Příklad
```
User: !status

Bot: 📊 **Agent Status**

🖥️ **Host:** `raspberrypi` (Linux)
✅ **Running**

**🔍 Diagnostics:**
• **LLM:** ✅ Online (245ms) [Local]
• **Internet:** ✅ Connected
• **Disk Free:** 15.3 GB

[Tlačítko: Zobrazit detailní statistiky]
```

<a name="implementační-detaily"></a>
### 🔧 Implementační detaily

**Kontrola LLM:**
```python
# Provede ping test na LLM
response = await self.agent.llm.generate_response("ping", system_prompt="Reply with 'pong'.")
latency = (time.time() - start_time) * 1000
```

**Kontrola internetu:**
```python
# Ping 8.8.8.8
cmd = "ping -c 1 8.8.8.8"  # Linux
cmd = "ping -n 1 8.8.8.8"  # Windows
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- LLM test může trvat 200-500ms
- Internet test může selhat pokud je firewall příliš restriktivní
- Disk Space se měří na root partition (`/`)

<a name="související"></a>
### 🔗 Související
- [`!stats`](#stats) - Detailní statistiky
- [`!monitor`](admin.md#monitor) - Monitorování zdrojů
- [`!debug`](admin.md#debug) - Pokročilá diagnostika

---

<a name="stats"></a>
## `!stats`

<a name="popis"></a>
### 📋 Popis
Zobrazí kompletní statistiky agenta včetně uptime, intelligence score, aktivity, paměti a použití nástrojů.

<a name="použití"></a>
### ⚙️ Použití
```
!stats
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

**1. Systém:**

- Hostname a OS
- Uptime (formátovaný)
- Čas spuštění (Discord timestamp)

**2. Intelligence (0-1000 bodů):**

- **Tool Diversity** - Počet různých použitých nástrojů (max 500 bodů)
- **Usage Efficiency** - Celkový počet použití nástrojů (max 300 bodů)
- **Learnings** - Počet naučených věcí (max 200 bodů)

**3. Aktivita:**

- Zpracované zprávy
- Autonomní akce
- Activity Rate (akce za minutu)
- Aktuální boredom %

**4. Paměť:**

- Počet vzpomínek
- Velikost historie akcí

**5. Top 5 Nástrojů:**

- Nejpoužívanější nástroje s počty

<a name="příklad"></a>
### 📝 Příklad
```
User: !stats

Bot: 📊 **Comprehensive Statistics**

🖥️ **System:**
• Host: `raspberrypi` (Linux)
• Uptime: 2 days, 5 hours, 23 minutes
• Started: <t:1733123456:R>

🧠 **Intelligence: 487/1000**
• Tool Diversity: 8 tools (245 pts)
• Usage Efficiency: 142 uses (182 pts)
• Learnings: 12 (60 pts)

📈 **Activity:**
• Messages Processed: 89
• Autonomous Actions: 156
• Activity Rate: 2.1 actions/min
• Current Boredom: 45%

💾 **Memory:**
• Total Memories: 234
• Action History: 100 entries

🏆 **Top Tools:**
1. web_tool: 45 uses
2. time_tool: 38 uses
3. math_tool: 22 uses
4. file_tool: 18 uses
5. weather_tool: 12 uses
```

<a name="výpočet-intelligence"></a>
### 🔧 Výpočet Intelligence

**Logaritmické škálování pro realistické skóre:**

```python
# Tool Diversity (max 500)
tool_diversity_score = min(500, math.log(tool_diversity + 1) * 120)

# Usage Efficiency (max 300)
usage_efficiency = min(300, math.log(total_tool_uses + 1) * 100)

# Learning Score (max 200)
learning_score = min(200, math.log(learnings + 1) * 45)

# Total
intelligence = tool_diversity_score + usage_efficiency + learning_score
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Intelligence škála je logaritmická - exponenciální růst se zpomaluje
- Uptime se načítá z `agent.start_time`
- Top 5 nástrojů seřazeno podle použití
- Activity rate = `total_actions / (uptime_seconds / 60)`

<a name="související"></a>
### 🔗 Související
- [`!intelligence`](#intelligence) - Pouze intelligence metriky
- [`!tools`](tools-learning.md#tools) - Detaily o nástrojích
- [`!memory`](data-management.md#memory) - Paměťové statistiky

---

<a name="intelligence"></a>
## `!intelligence`

<a name="popis"></a>
### 📋 Popis
Zobrazí metriky inteligence agenta s analýzou úrovně.

<a name="použití"></a>
### ⚙️ Použití
```
!intelligence
```
nebo
```
!inteligence
```
(oba překlepy fungují)

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

**Metriky:**

- Overall Intelligence (0-100)
- Tool Diversity
- Total Tool Uses
- Successful Learnings

**Analýza úrovně:**

- **< 20:** Very low - Just starting out
- **20-49:** Low - Learning the basics
- **50-74:** Moderate - Getting smarter!
- **75+:** High - Very capable!

<a name="příklad"></a>
### 📝 Příklad
```
User: !intelligence

Bot: 🧠 **Intelligence Metrics:**

**Overall Intelligence:** 67/100
• Tool Diversity: 8 different tools
• Total Tool Uses: 45
• Successful Learnings: 5

**Analysis:** Moderate - Getting smarter!
```

<a name="výpočet-starší-verze"></a>
### 🔧 Výpočet (starší verze)

```python
# Jednoduchá formula (pouze pro !intelligence)
intelligence = min(100, 
    (tool_diversity * 10) + 
    (total_tool_uses * 2) + 
    (successful_learns * 5)
)
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Tento příkaz používá starší, jednodušší výpočet než `!stats`
- Pro přesnější metriky použij `!stats`
- `!inteligence` je alias (automaticky opraveno)

<a name="související"></a>
### 🔗 Související
- [`!stats`](#stats) - Komplexnější statistiky
- [`!learn`](tools-learning.md#learn) - Učení nových dovedností

---

<a name="documentation"></a>
## `!documentation`

<a name="popis"></a>
### 📋 Popis
Zobrazí interaktivní dokumentaci přímo v Discordu pomocí tlačítek.

<a name="použití"></a>
### ⚙️ Použití
```
!documentation
```
nebo
```
!docs
```

<a name="funkce"></a>
### 💡 Funkce

- Zobrazí rozcestník kategorií
- Tlačítka pro navigaci (Overview, Commands, Tools, Core)
- Odesílá soubory dokumentace jako přílohy (ephemeral messages)

<a name="příklad"></a>
### 📝 Příklad
```
User: !docs

Bot: 📚 **AI Agent Dokumentace**
     Vyberte kategorii:
     
     [📖 Overview] [💬 Příkazy] [🛠️ Nástroje] [🧠 Core]
     
     (Po kliknutí na '💬 Příkazy'):
     Bot: Odesílám soubor: commands.md
```

---

<a name="fuzzy-command-matching"></a>
## Fuzzy Command Matching

<a name="popis"></a>
### 📋 Popis
Agent automaticky opravuje překlepy v příkazech pomocí Levenshtein distance algoritmu.

<a name="jak-funguje"></a>
### ⚙️ Jak funguje

**1. Porovnání příkazu:**
```python
distance = levenshtein_distance(user_command, valid_command)
```

**2. Auto-korekce:**

- Pokud distance ≤ 2, příkaz se auto-opraví
- Uživatel dostane notifikaci o korekci
- Příkaz se normálně vykoná

<a name="příklady-auto-korekce"></a>
### 💡 Příklady auto-korekce

```
!hlep      → !help
!statu     → !status
!toools    → !tools
!rstart    → !restart
!inteligence → !intelligence  (alias)
```

<a name="příklad-použití"></a>
### 📝 Příklad použití
```
User: !statu

Bot: 💡 Did you mean `!status`? (auto-correcting '!statu')

     📊 **Agent Status**
     ...
```

<a name="implementace"></a>
### 🔧 Implementace

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    # Dynamic programming implementation
    ...
```

<a name="poznámky"></a>
### ⚠️ Poznámky

- Funguje pro všechny příkazy
- Threshold je 2 znaky (příliš vzdálené příkazy se neopraví)
- Pokud ne existuje blízká shoda, vrátí se error "Unknown command"

---

<a name="command-queue-system"></a>
## Command Queue System

<a name="popis"></a>
### 📋 Popis
Všechny příkazy jsou zpracovávány asynchronně přes interní frontu.

<a name="jak-funguje"></a>
### ⚙️ Jak funguje

**1. Příkaz přijde:**
```python
await self.queue.put(msg)
```

**2. Worker loop:**
```python
while self.is_running:
    msg = await self.queue.get()
    await self._execute_command(msg)
    self.queue.task_done()
```

**3. Feedback:**
- Pokud je fronta neprázdná, uživatel dostane pozici ve frontě

<a name="výhody"></a>
### 💡 Výhody

- Příkazy se nezablokují
- Můžeš poslat více příkazů najednou
- Error v jednom příkazu nezastaví ostatní

<a name="příklad"></a>
### 📝 Příklad
```
User: !stats
User: !tools
User: !logs 20

Bot: [Zpracovává !stats]
     Command queued (Position: 2)
     Command queued (Position: 3)
```

<a name="poznámky"></a>
### ⚠️ Poznámky

- Všechny příkazy se vykonají v pořadí
- Pokud příkaz vyhodí error, ostatní pokračují
- Worker běží jako background task (`asyncio.create_task`)

---

<a name="souhrn"></a>
## 📊 Souhrn

| Příkaz | Účel | Výstup |
|--------|------|--------|
| `!help` | Zobraz nápovědu | Seznam všech příkazů |
| `!status` | Stav agenta | Diagnostika + tlačítko stats |
| `!stats` | Detailní statistiky | Intelligence, aktivita, top nástroje |
| `!intelligence` | Intelligence metriky | Skóre 0-100 + analýza |
| `!documentation` | Dokumentace | Interaktivní tlačítka |
| `!info` | Systémové info | Detailní HW/SW informace |

---

<a name="info"></a>
## `!info`

<a name="popis"></a>
### 📋 Popis
Zobrazí detailní informace o systému, hardwaru a běžícím agentovi, napodobující data z Web Dashboardu.

<a name="použití"></a>
### ⚙️ Použití
```
!info
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

**1. System Info:**
- OS a verze
- Hardware model (Raspberry Pi model)
- Verze Pythonu a projektu
- Použitý LLM model

**2. Resources:**
- Využití CPU, RAM a Disku (v GB a %)

**3. Environment:**
- Discord Latency
- Local Time

**4. About:**
- Informace o tvůrcích a technologiích

<a name="příklad"></a>
### 📝 Příklad
```
User: !info

Bot: ℹ️ **System & Agent Information**

     **System Info:**
     **OS:** Linux (Raspbian GNU/Linux 11) running on Raspberry Pi 4B (4GB)
     **Python:** 3.11.2
     **LLM Model:** QWEN 0.5B Instruct
     **Project Version:** Beta - CLOSED

     **Environment:**
     **Discord Latency:** 23ms
     **Local Time:** 2025-12-06 18:30:00

     **About:**
     Created in collaboration with Antigravity
     Powered by Discord, ngrok, and local LLMs.
```

<a name="poznámky"></a>
### ⚠️ Poznámky

- Slouží jako rychlý přehled bez nutnosti otevírat web interface
- Zobrazuje statičtější data než `!monitor` (live)



<a name="související"></a>
## 🔗 Související

- [📋 Všechny příkazy](../SUMMARY.md#commands-api)
- [🏗️ Command Architecture](../architecture.md#command-layer)
- [🆘 Troubleshooting](../troubleshooting.md#command-errors)

---
Poslední aktualizace: 2025-12-06  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
