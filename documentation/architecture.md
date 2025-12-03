# Architektura Systému

> Celkový přehled architektury RPI AI Agenta

## 📋 High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Discord Server                        │
│                   (Uživatelské rozhraní)                     │
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
└──┬─────────┬───────────┬────────────┬──────────┬───────────┘
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

## 🏗️ Komponenty

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

### 2. Command Layer

**Účel:** Zpracování příkazů

**Komponenty:**
- `CommandHandler` - Routing a execution
- Fuzzy Matching - Automatická korekce
- Command Queue - Worker loop

**Kategorie příkazů:**
- Basic (help, status, stats)
- Tools & Learning (tools, learn, ask)
- Data Management (memory, logs, export)
- Interaction (mood, goals, config)
- Admin (restart, monitor, debug)

---

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

### 8. Network Monitor

**Účel:** Sledování připojení

**Funkce:**
- Ping test (8.8.8.8)
- Disable web tools on disconnect
- Restore on reconnect
- Admin notifications

---

## 🔄 Datové Toky

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

## 📊 State Management

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

### Tool Stats

```python
{
    "web_tool": 45,
    "math_tool": 22,
    ...
}
```

**Persistence:** `tool_stats.json`

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

## 🔐 Security Layers

### 1. File Access

```python
# Restricted to workspace
safe_path = os.path.abspath(os.path.join(workspace_dir, filename))
if not safe_path.startswith(workspace_dir):
    return "Error: Access denied"
```

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

### 3. Database

```python
# Only SELECT allowed
if not query.strip().upper().startswith("SELECT"):
    return "Error: Only SELECT queries allowed"
```

### 4. Admin Commands

```python
# Permission check
if author_id not in config_settings.ADMIN_USER_IDS:
    return "⛔ Access Denied"
```

---

## 🚀 Performance

### Asynchronní Operace

- Command processing (queue worker)
- LLM inference (thread pool)
- Discord I/O (asyncio)
- Background loops (boredom, monitoring)

### Resource Optimization

- **Tier-based LLM** - Adaptivní parametry
- **Memory limits** - Max 100 action history
- **SWAP expansion** - Dynamic allocation
- **Process cleanup** - Tier 3 termination

---

## 🔗 Související

- [Autonomous Behavior](core/autonomous-behavior.md)
- [Memory System](core/memory-system.md)
- [Resource Manager](core/resource-manager.md)
- [All Commands](commands/)

---

**Poslední aktualizace:** 2025-12-02  
**Verze:** 1.0.0
