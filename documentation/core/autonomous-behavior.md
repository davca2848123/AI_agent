# Autonomní Chování

> Jak agent samostatně rozhoduje a jedná

## 📋 Přehled

Agent má schopnost autonomního rozhodování díky systému "nudy" (boredom) a kontextově informovanému decision-makingu pomocí LLM.

---

## Boredom Mechanism

### 🎯 Princip

Agent má **boredom score** (0.0 - 1.0), které postupně roste v čase. Když překročí threshold, agent se autonomně rozhodne pro akci.

### 🔧 Parametry

```python
# V agent/core.py
self.boredom_score = 0.0
self.boredom_threshold = 0.8  # 80%
self.boredom_decay_rate = 0.02  # Per minute
```

### 💡 Boredom Loop

```python
async def boredom_loop(self):
    """Simulates the passage of time and intrinsic decay (boredom)."""
    while True:
        await asyncio.sleep(60)  # Every minute
        
        # Increase boredom
        self.boredom_score += self.boredom_decay_rate
        
        # Trigger action if threshold reached
        if self.boredom_score >= self.boredom_threshold:
            await self.trigger_autonomous_action()
            
        # Update Discord status
        await self.discord.update_activity(f"Boredom: {int(self.boredom_score * 100)}%")
```

### 📊 Boredom Reduction

Akce redukují boredom na základě "obtížnosti":

```python
def reduce_boredom(self, amount: float):
    """Reduces boredom score based on action difficulty."""
    self.boredom_score = max(0.0, self.boredom_score - amount)
    self._save_agent_state()
```

**Typické hodnoty:**
- Jednoduchá akce (read file): -0.1
- Střední akce (search web): -0.3
- Komplexní akce (learn new tool): -0.5
- Interakce s uživatelem: -0.8 (reset téměř na 0)

---

## Decision Making

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

### 🎯 Decision Types

**1. Learning Mode** - Procházet learning_queue  
**2. Goal-Oriented** - Pracovat na cílech  
**3. Exploration** - Zkoušet nové nástroje  
**4. Social** - Reagovat na Discord aktivity  
**5. Maintenance** - Cleanup, backup, atd.

---

## Learning Mode

### 📋 Popis

Speciální režim kdy agent systematicky prochází frontu nástrojů k naučení.

### 🔧 Aktivace

```python
# Via !learn command
self.learning_queue = [tool_name]  # nebo list všech
self.is_learning_mode = True
self.boredom_score = 1.0  # Force immediate action
```

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

## Action Execution

### 🔧 Execute Action

```python
async def execute_action(self, action: str):
    """Executes a decided action."""
    
    # Parse action for tool calls
    tool_call = self.llm.parse_tool_call(action)
    
    if tool_call:
        tool_name = tool_call['tool']
        params = tool_call.get('params', {})
        
        tool = self.tools.get_tool(tool_name)
        if tool:
            result = await tool._execute_with_logging(**params)
            
            # Track usage
            self.tool_usage_count[tool_name] += 1
            self.tool_last_used[tool_name] = time.time()
            
            # Store in memory
            self.memory.add_memory(
                content=f"Used {tool_name}: {result[:200]}",
                metadata={"type": "action", "tool": tool_name}
            )
    
    # Add to history
    self._add_to_history(action)
    
    # Reduce boredom
    self.reduce_boredom(0.3)
```

---

## Activity Monitoring

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

## Action History

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

### 💡 Použití

- Context pro LLM rozhodování
- Prevence opakování stejných akcí
- Statistiky pro `!stats`
- Export přes `!export history`

---

## Goals System

### 🎯 Cíle agenta

```python
self.goals = [
    "Learn all available tools",
    "Help users with their questions",
    "Monitor system health"
]
```

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

## Simplified Action Status

### 📋 Discord Status Update

Agent zobrazuje co dělá jako Discord status:

```python
async def _simplify_action(self, action: str) -> str:
    """Simplifies action string for status display."""
    
    # Ask LLM to create short status
    prompt = f"Simplify this action to 2-4 words for status: {action}"
    simplified = await self.llm.generate_response(prompt, system_prompt="Be very brief.")
    
    return simplified[:50]  # Discord limit
```

**Příklady:**
- "Learn and test: web_tool" → "Learning web search"
- "Research: Python tutorial" → "Researching Python"
- "Check system health" → "Monitoring system"

---

## 🔗 Související

- [LLM Integration](llm-integration.md) - Jak LLM rozhoduje
- [Memory System](memory-system.md) - Ukládání zkušeností
- [Boredom Mechanism](../advanced/boredom.md) - Detailní vysvětlení

---

**Poslední aktualizace:** 2025-12-02  
**Verze:** 1.0.0
