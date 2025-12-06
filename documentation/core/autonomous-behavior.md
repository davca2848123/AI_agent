# Autonomní Chování

> **Navigace:** [📂 Dokumentace](../README.md) | [🧠 Core](../README.md#core-jádro) | [Autonomní chování](autonomous-behavior.md)

> Jak agent samostatně rozhoduje a jedná.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Agent má schopnost autonomního rozhodování díky systému "nudy" (boredom) a kontextově informovanému decision-makingu pomocí LLM.

---

<a name="boredom-mechanism"></a>
## Boredom Mechanism

<a name="princip"></a>
### 🎯 Princip

Agent má **boredom score** (0.0 - 1.0), které postupně roste v čase. Když překročí threshold, agent se autonomně rozhodne pro akci.

<a name="parametry"></a>
### 🔧 Parametry

```python
# V agent/core.py
self.boredom_score = 0.0
self.BOREDOM_THRESHOLD_LOW = 0.2
self.BOREDOM_THRESHOLD_HIGH = 0.4  # 40% triggers action
self.BOREDOM_DECAY_RATE = 0.05
self.BOREDOM_INTERVAL = 300  # 5 minutes
```

<a name="boredom-loop"></a>
### 💡 Boredom Loop

```python
async def boredom_loop(self):
    """Simulates the passage of time and intrinsic decay (boredom)."""
    while True:
        await asyncio.sleep(self.BOREDOM_INTERVAL)  # Every 5 minutes
        
        # Increase boredom
        self.boredom_score = min(1.0, self.boredom_score + self.BOREDOM_DECAY_RATE)
        
        # Trigger action if threshold reached
        if self.boredom_score > self.BOREDOM_THRESHOLD_HIGH:
            await self.trigger_autonomous_action()
            
        # Update Discord status
        await self.discord.update_activity(f"Boredom: {self.boredom_score * 100:.0f}%")
```

<a name="boredom-reduction"></a>
### 📊 Boredom Reduction

Akce redukují boredom na základě typu interakce:

```python
def reduce_boredom(self, amount: float):
    """Reduces boredom score."""
    self.boredom_score = max(0.0, self.boredom_score - amount)
```

**Typické hodnoty:**

- Zpracování zprávy (observation): -0.1
- Vykonání akce (execute_action): -0.3


---

<a name="decision-making"></a>
## Decision Making

<a name="llm-based-decisions"></a>
### 🧠 LLM-Based Decisions

Agent používá LLM k rozhodování jakou akci provést:

```python
async def trigger_autonomous_action(self):
    """The 'Free Will' mechanism."""
    
    # 1. Check learning mode
    if self.is_learning_mode and self.learning_queue:
        tool_name = self.learning_queue.pop(0)
        action = f"Learn and test: {tool_name}"
        # ... execute learning
        return
    
    # 2. Build context
    context = self._build_decision_context()
    
    # 3. Ask LLM to decide
    decision = await self.llm.decide_action(
        context=context,
        past_memories=recent_memories,
        tools_desc=tools_description
    )
    
    # 4. Execute decision
    await self.execute_action(decision)
```

<a name="decision-context"></a>
### 📝 Decision Context

```python
def _build_decision_context(self):
    """Build context for decision making."""
    return f"""
Current Status:
- Boredom: {self.boredom_score * 100}%
- Actions without tools: {self.actions_without_tools}
- Recent actions: {self.action_history[-5:]}
- Goals: {self.goals}
- Available tools: {list(self.tools.tools.keys())}
- Online activities: {recent_activities}
"""
```

<a name="decision-types"></a>
### 🎯 Decision Types

**1. Learning Mode** - Procházet learning_queue  
**2. Goal-Oriented** - Pracovat na cílech  
**3. Exploration** - Zkoušet nové nástroje  
**4. Social** - Reagovat na Discord aktivity  
**5. Maintenance** - Cleanup, backup, atd.

---

<a name="learning-mode"></a>
## Learning Mode

<a name="popis"></a>
### 📋 Popis

Speciální režim kdy agent systematicky prochází frontu nástrojů k naučení.

<a name="aktivace"></a>
### 🔧 Aktivace

```python
# Via !learn command
self.learning_queue = [tool_name]  # nebo list všech
self.is_learning_mode = True
self.boredom_score = 1.0  # Force immediate action
```

<a name="learning-flow"></a>
### 💡 Learning Flow

```python
if self.is_learning_mode and self.learning_queue:
    tool_name = self.learning_queue.pop(0)
    
    # Report what we're learning
    await self.report_learning(f"🎓 Learning: {tool_name}")
    
    # Ask LLM to use the tool
    action = f"Learn and test: {tool_name}"
    
    # LLM generates appropriate usage
    # Tool is executed
    # Result is stored in memory
    
    # If queue empty, exit learning mode
    if not self.learning_queue:
        self.is_learning_mode = False
```

---

<a name="action-execution"></a>
## Action Execution

<a name="execute-action"></a>
### 🔧 Action Handling

Logika vykonávání akcí je rozdělena:

1. **Tool Actions** - Řešeno přímo v `trigger_autonomous_action`:

   - Parsování tool callu
   - Exekuce nástroje
   - Uložení výsledku

2. **Text Actions** - Řešeno v `execute_action`:
   
   - Pouze pro textové odpovědi (bez nástrojů)
   - Odeslání reportu adminovi (pokud relevantní)

```python
async def execute_action(self, action: str):
    """Executes a decided action (text-only)."""
    logger.info(f"Executing action: {action}")
    
    # Send report if action implies communication
    if "status" in action.lower() or "report" in action.lower():
         await self.send_admin_dm(f"🤖 Autonomous Report:\n{action}")
```

---

<a name="activity-monitoring"></a>
## Activity Monitoring

<a name="discord-activity-detection"></a>
### 📋 Discord Activity Detection

Agent sleduje co uživatelé dělají na Discord (hry, apky):

```python
async def observation_loop(self):
    """Polls sensors and queues inputs."""
    while True:
        await asyncio.sleep(30)  # Every 30s
        
        # Get online activities
        activities = await self.discord.get_online_activities()
        
        for activity in activities:
            await self._process_activity(activity)
```

<a name="activity-processing"></a>
### 🔍 Activity Processing

```python
async def _process_activity(self, activity_data: dict):
    """Research unknown user activities and store in memory."""
    
    activity_name = activity_data['name']
    
    # Check if we know about this activity
    memories = self.memory.search_relevant_memories(activity_name, limit=1)
    
    if not memories:
        # New activity - research it
        web_tool = self.tools.get_tool('web_tool')
        if web_tool:
            result = await web_tool._execute_with_logging(
                action="search",
                query=f"What is {activity_name}"
            )
            
            # Store discovery
            self.memory.add_memory(
                content=f"Discovered activity: {activity_name}. {result[:300]}",
                metadata={"type": "learning", "source": "discord_activity"}
            )
```

---

<a name="service-loops"></a>
## Service Loops

<a name="backup-loop"></a>
### 💾 Backup Loop
Periodicky provádí zálohu databáze (`agent_memory.db`) do adresáře `backup/`.

```python
async def backup_loop(self):
    """Periodically backs up the database (2x daily)."""
    # 1. Check loop health
    # 2. Check if backup needed (>12h since last)
    # 3. Create backup (memory.create_backup())
```

<a name="check-subsystems"></a>
### 🛠️ Subsystem Check (Self-Healing)
Automatická kontrola a oprava klíčových komponent každých 30 sekund.

```python
async def check_subsystems(self):
    """Checks health of subsystems and restarts if needed."""
    
    # 1. Web Server
    # Auto-restart pokud je down > 10s
    
    # 2. SSH Tunnel
    # Auto-restart pokud chybí ngrok tunel
    
    # 3. Loop Health
    # Kontrola běžících smyček (boredom, observation...)
```

---

<a name="action-history"></a>
## Action History

<a name="historie-akcí"></a>
### 📝 Historie akcí

Agent udržuje historii posledních akcí:

```python
self.action_history = []  # Max 100 items

def _add_to_history(self, action: str):
    """Add action to history and keep it trimmed."""
    self.action_history.append(action)
    
    # Keep only last 100
    if len(self.action_history) > 100:
        self.action_history = self.action_history[-100:]
```

<a name="použití"></a>
### 💡 Použití

- Context pro LLM rozhodování
- Prevence opakování stejných akcí
- Statistiky pro `!stats`
- Export přes `!export history`

---

<a name="goals-system"></a>
## Goals System

<a name="cíle-agenta"></a>
### 🎯 Cíle agenta

```python
self.goals = [
    "Learn new things using tools",
    "Try to maintain boredom below 70%",
    "Use diverse tools",
    "Build knowledge base"
]
```

<a name="ovlivnění-rozhodování"></a>
### 💡 Ovlivnění rozhodování

Cíle jsou součástí decision context:

```python
context = f"""
Goals:
{chr(10).join(f"- {g}" for g in self.goals)}

Based on your goals, what should you do next?
"""
```

LLM bere cíle v úvahu při výběru akce.

---

<a name="simplified-action-status"></a>
## Simplified Action Status

<a name="discord-status-update"></a>
### 📋 Discord Status Update

Agent zobrazuje co dělá jako Discord status:

```python
def _simplify_action(self, action: str) -> str:
    """Simplifies English action to concise form for Discord status."""
    # Remove common prefixes and filler words
    clean = action.replace("ACTION:", "").strip()
    clean = clean.replace("I will try to", "").strip()
    
    return clean[:50]  # Simple string manipulation
```

**Příklady:**

- "ACTION: Learn and test: web_tool" → "Learn and test: web_tool"
- "I will try to research Python" → "Research Python"

---

<a name="související"></a>
## 🔗 Související

- [📖 LLM Integration](llm-integration.md) - Jak LLM rozhoduje
- [📖 Memory System](memory-system.md) - Ukládání zkušeností
- [📖 Boredom Mechanism](../advanced/boredom.md) - Detailní vysvětlení
- [🏗️ Architektura](../architecture.md)
- [🆘 Troubleshooting](../troubleshooting.md)

---
Poslední aktualizace: 2025-12-06  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
