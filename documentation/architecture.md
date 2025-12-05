# Architektura Systému

> **Navigace:** [📂 Dokumentace](README.md) | [📄 Přehled (OVERVIEW)](OVERVIEW.md) | [🔍 Index (INDEX)](INDEX.md) | [📋 API Tasklist (SUMMARY)](SUMMARY.md) | [🏗️ Architektura](architecture.md) | [🆘 Troubleshooting](troubleshooting.md)

> Celkový přehled architektury RPI AI Agenta.
> **Verze:** Alpha

---

<a name="high-level-overview"></a>
## 📋 High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Discord Server                       │
│                   (Uživatelské rozhraní)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Discord Client                          │
│              (Příjem/odesílání zpráv)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Command Handler                           │
│           (Parsing a routing příkazů)                       │
└──────┬──────────────────┬───────────────────┬───────────────┘
       │                  │                   │
       ▼                  ▼                   ▼
┌─────────────┐  ┌──────────────┐   ┌──────────────┐
│   Basic     │  │   Tools &    │   │    Admin     │
│  Commands   │  │   Learning   │   │   Commands   │
└─────────────┘  └──────────────┘   └──────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Autonomous Agent                           │
│                  (Hlavní logika)                            │
├─────────────────────────────────────────────────────────────┤
│  • Boredom System                                           │
│  • Decision Making (LLM)                                    │
│  • Goal Management                                          │
│  • Action Execution                                         │
└──┬─────────┬───────────┬────────────┬──────────┬────────────┘
   │         │           │            │          │
   ▼         ▼           ▼            ▼          ▼
┌─────┐  ┌──────┐  ┌─────────┐  ┌────────┐  ┌──────────┐
│ LLM │  │Memory│  │  Tools  │  │Resource│  │ Network  │
│     │  │Store │  │Registry │  │Manager │  │ Monitor  │
└─────┘  └──────┘  └─────────┘  └────────┘  └──────────┘
   │         │           │            │          │
   ▼         ▼           ▼            ▼          ▼
┌─────┐  ┌──────┐  ┌─────────┐  ┌────────┐  ┌──────────┐
│Qwen │  │SQLite│  │14 Tools │  │psutil  │  │Internet  │
│ 2.5 │  │+FTS5 │  │         │  │        │  │  Ping    │
└─────┘  └──────┘  └─────────┘  └────────┘  └──────────┘
```

---

<a name="komponenty"></a>
## 🏗️ Komponenty

<a name="1-discord-layer"></a>
### 1. Discord Layer

**Účel:** Komunikace s uživateli

**Komponenty:**
- `DiscordClient` - Wrapper pro discord.py
- Message Queue - Asynchronní fronta příkazů
- Event Handlers - on_ready, on_message

**Datový tok:**
```
User → Discord Server → Bot → Message Queue → Command Handler
```

---

<a name="2-command-layer"></a>
### 2. Command Layer

**Účel:** Zpracování příkazů

**Komponenty:**
- `CommandHandler` - Routing a execution
- Fuzzy Matching - Automatická korekce
- Command Queue - Worker loop

**Kategorie příkazů:**
- [Basic](commands/basic.md) (help, status, stats)
- [Tools & Learning](commands/tools-learning.md) (tools, learn, ask)
- [Data Management](commands/data-management.md) (memory, logs, export)
- [Interaction](commands/interaction.md) (mood, goals, config)
- [Admin](commands/admin.md) (restart, monitor, debug)

---

<a name="3-agent-core"></a>
### 3. Agent Core

**Účel:** Autonomní rozhodování a akce

**Klíčové subsystémy:**

**Boredom System:**
```python
boredom_score += decay_rate  # Každou minutu
if boredom_score >= threshold:
    trigger_autonomous_action()
```

**Decision Making:**
```python
context = build_context()
decision = llm.decide_action(context, memories, tools)
execute_action(decision)
```

**Learning Mode:**
```python
while learning_queue:
    tool = learning_queue.pop()
    test_and_learn(tool)
```

---

<a name="4-llm-integration"></a>
### 4. LLM Integration

**Účel:** AI inference

**Model:** Qwen 2.5-0.5B-Instruct (Q4 quantization)

**Capabilities:**
- Response generation
- Action decision making
- Tool call parsing

**Adaptive parameters:**
```
Tier 0: ctx=2048, threads=4
Tier 1: ctx=1024, threads=3
Tier 2: ctx=512, threads=2
Tier 3: ctx=256, threads=1
```

---

<a name="5-memory-system"></a>
### 5. Memory System

**Účel:** Perzistentní vzpomínky

**Technologie:** SQLite + FTS5

**Schema:**
```sql
memories (
    id, content, metadata, timestamp, embedding
)

memories_fts (
    FTS5 index on content
)
```

**Features:**
- Keyword search
- Relevance filtering
- Auto-backup
- Type categorization

---

<a name="6-tool-registry"></a>
### 6. Tool Registry

**Účel:** Registr a správa nástrojů

**14 nástrojů:**
- FileTool, SystemTool, WebTool
- TimeTool, MathTool, WeatherTool
- CodeTool, NoteTool, GitTool
- DatabaseTool, RSSTool, TranslateTool
- WikipediaTool, DiscordActivityTool

**Interface:**
```python
class Tool(ABC):
    @property
    def name() -> str
    
    @property
    def description() -> str
    
    async def execute(**kwargs) -> str
```

---

<a name="7-resource-manager"></a>
### 7. Resource Manager

**Účel:** Správa systémových zdrojů

**4-Tier System:**

| Tier | Threshold | Akce |
|------|-----------|------|
| 0 | < 85% | Normální |
| 1 | 85% | GC, Cleanup |
| 2 | 90% | SWAP, Reduce LLM |
| 3 | 95% | Kill processes |

**Monitoring:**
- CPU, RAM, Disk, Swap
- Check každých 30s
- Hystereze (2min)

---

<a name="8-network-monitor"></a>
### 8. Network Monitor

**Účel:** Sledování připojení

**Funkce:**
- Ping test (8.8.8.8)
- Disable web tools on disconnect
- Restore on reconnect
- Admin notifications

---

<a name="9-web-interface"></a>
### 9. Web Interface

**Účel:** Webová dokumentace a monitoring

**Komponenty:**
- Flask server (port 5001+)
- Ngrok tunnel (public URL)
- Markdown renderer
- Search functionality (fuzzy + exact)
- Live dashboard

**Funkce:**
- Dashboard s real-time stats
- Documentation browser
- Search s Levenshtein distance
- Auto-refresh (konfiguratelní)

---

<a name="10-error-tracker"></a>
### 10. Error Tracker

**Účel:** Sledování chyb a restart attemptů

**Funkce:**
- Tracking startup errors
- Restart attempt limity
- Critical error notifications
- Startup recovery mechanism

---

<a name="datove-toky"></a>

<a name="datové-toky"></a>
## 🔄 Datové Toky

<a name="command-flow"></a>
### Command Flow

```
1. User sends    "!ask weather Prague"
2. Discord       → message_queue
3. Worker loop   → _execute_command()
4. Parse command → cmd_ask
5. LLM selects   → weather_tool
6. Tool executes → API call
7. LLM formats   → answer
8. Discord sends → response to user
```

<a name="autonomous-action-flow"></a>
### Autonomous Action Flow

```
1. Boredom timer → score >= 0.8
2. Build context → recent actions, goals
3. LLM decides   → "Learn web_tool"
4. Execute       → web_tool.execute(...)
5. Store result  → memory.add_memory()
6. Reduce        → boredom_score -= 0.3
7. Report        → Discord channel (optional)
```

<a name="learning-mode-flow"></a>
### Learning Mode Flow

```
1. User: !learn all
2. Queue: [web_tool, math_tool, ...]
3. Loop:
    a. Pop tool from queue
    b. LLM generates usage
    c. Execute tool
    d. Store in memory
    e. Next tool
4. End: is_learning_mode = False
```

---

<a name="state-management"></a>
## 📊 State Management

<a name="agent-state"></a>
### Agent State

```python
{
    "boredom_score": 0.0,
    "last_admin_dm": {...},
    "is_learning_mode": False,
    "learning_queue": []
}
```

**Persistence:** `.agent_state.json`

<a name="tool-stats"></a>
### Tool Stats

```python
{
    "web_tool": 45,
    "math_tool": 22,
    ...
}
```

**Persistence:** `tool_stats.json`

<a name="tool-timestamps"></a>
### Tool Timestamps

```python
{
    "web_tool": 1733140123.45,
    "math_tool": 1733139000.12,
    ...
}
```

**Persistence:** `tool_timestamps.json`

---

<a name="security-layers"></a>
## 🔐 Security Layers

<a name="1-file-access"></a>
### 1. File Access

```python
# Restricted to workspace
safe_path = os.path.abspath(os.path.join(workspace_dir, filename))
if not safe_path.startswith(workspace_dir):
    return "Error: Access denied"
```

<a name="2-code-execution"></a>
### 2. Code Execution

```python
# Limited builtins
safe_globals = {
    "__builtins__": {
        "print": print, "len": len, ...  # Only safe functions
    }
}
exec(code, safe_globals, {})
```

<a name="3-database"></a>
### 3. Database

```python
# Only SELECT allowed
if not query.strip().upper().startswith("SELECT"):
    return "Error: Only SELECT queries allowed"
```

<a name="4-admin-commands"></a>
### 4. Admin Commands

```python
# Permission check
if author_id not in config_settings.ADMIN_USER_IDS:
    return "⛔ Access Denied"
```

---

<a name="performance"></a>
## 🚀 Performance

<a name="asynchronní-operace"></a>
### Asynchronní Operace

- Command processing (queue worker)
- LLM inference (thread pool)
- Discord I/O (asyncio)
- Background loops (boredom, monitoring)

<a name="resource-optimization"></a>
### Resource Optimization

- **Tier-based LLM** - Adaptivní parametry
- **Memory limits** - Max 100 action history
- **SWAP expansion** - Dynamic allocation
- **Process cleanup** - Tier 3 termination

---

<a name="související"></a>
## 🔗 Související

- [📖 Autonomous Behavior](core/autonomous-behavior.md)
- [📖 Memory System](core/memory-system.md)
- [📖 Resource Manager](core/resource-manager.md)
- [📂 All Commands](commands/)

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
