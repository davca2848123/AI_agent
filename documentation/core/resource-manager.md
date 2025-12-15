# Resource Manager

> **Navigace:** [📂 Dokumentace](../README.md) | [🧠 Core](../README.md#core-jádro) | [Resource Manager](resource-manager.md)

> 4-tier adaptivní systém pro správu systémových zdrojů.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Resource Manager sleduje využití CPU, RAM, Disk a Swap a automaticky reaguje podle  zatížení pomocí 4-tier systému.

---

<a name="tier-system"></a>
## Tier System

<a name="tier-úrovně"></a>
### 🎯 Tier Úrovně

| Tier | Threshold | Stav | Reakce |
|------|-----------|------|--------|
| **0** | < 85% | Normální | Žádná |
| **1** | 85-89% | Varování | Cleanup, GC (3 threads) |
| **2** | 90-94% | Mitigace | Redukce LLM (1024 ctx, 2 threads), SWAP expansion |
| **3** | 95%+ | Nouzový | Redukce LLM (1024 ctx, 1 thread), Kill processes |

<a name="hystereze"></a>
### 🔧 Hystereze

Tier se nemění okamžitě - používá hysterezi:

```python
def get_tier(self, usage=None):
    """Determine tier with hysteresis."""
    
    max_usage = max(usage.cpu_percent, usage.ram_percent, 
                    usage.disk_percent, usage.swap_percent)
    
    # Determine raw tier
    if max_usage >= 95:
        raw_tier = 3
    elif max_usage >= 90:
        raw_tier = 2
    elif max_usage >= 85:
        raw_tier = 1
    else:
        raw_tier = 0
    
    # Apply hysteresis (prevent flapping)
    if raw_tier > self.current_tier:
        # Escalate immediately
        self.current_tier = raw_tier
    elif raw_tier < self.current_tier:
        # Deescalate only if sustained for 2 minutes
        if time.time() - self.last_tier_change > 120:
            self.current_tier = raw_tier
    
    return self.current_tier
```

---

<a name="tier-1"></a>

<a name="tier-1-warning-cleanup"></a>
## Tier 1: Warning & Cleanup

<a name="akce"></a>
### ⚙️ Akce

```python
async def execute_tier1(self):
    """Tier 1 (85%): Warning & Cleanup."""
    
    # 1. Run garbage collection
    import gc
    gc.collect()
    
    # 2. Trim history
    agent.action_history = agent.action_history[-100:]
    
    # 3. Notify admin
    await agent.send_admin_dm(
        "⚠️ **Resource Warning** (Tier 1)\n"
        f"{details}",
        category="tier"
    )
```

<a name="detaily"></a>
### 📊 Detaily

```python
def get_tier1_details(self):
    usage = self.check_resources()
    return f"""
CPU: {usage.cpu_percent}%
RAM: {usage.ram_percent}%
Disk: {usage.disk_percent}%
Swap: {usage.swap_percent}%

Actions taken:
• Garbage collection
• History trimmed to 100
"""
```

---

<a name="tier-2"></a>

<a name="tier-2-active-mitigation"></a>
## Tier 2: Active Mitigation

<a name="akce"></a>
### ⚙️ Akce

```python
async def execute_tier2(self):
    """Tier 2 (90%): Active Mitigation."""
    
    # 1. Trim history more
    agent.action_history = agent.action_history[-50:]
    
    # 2. Expand SWAP
    await self._expand_swap(force_max=False)
    
    # 3. Reduce LLM context (Medium)
    await self._reduce_llm_resources(tier=2)
    
    # 4. Notify admin
    await agent.send_admin_dm(details, category="tier")
```

<a name="llm-reduction"></a>
### 🔧 LLM Reduction

```python
def update_parameters(self, resource_tier: int):
    """Update LLM parameters based on resource tier."""
    
    # Context Limits
    context_map = {
        0: 2048, # Normal
        1: 1024, # Tier 1
        2: 1024, # Tier 2
        3: 1024  # Tier 3
    }
    
    # Thread Limits
    thread_map = {
        0: 4, # Normal
        1: 3, # Tier 1
        2: 2, # Tier 2 (Stability fix)
        3: 1  # Tier 3 (Max stability)
    }
    
    new_ctx = context_map.get(resource_tier, 1024)
    new_threads = thread_map.get(resource_tier, 3)
    
    # Update LLM
    self.current_n_ctx = new_ctx
    self.current_n_threads = new_threads
```

<a name="swap-expansion"></a>
### 💾 SWAP Expansion

**Linux:**
```bash
# Create/expand swap file (Smart Check implemented)
# Only runs massive I/O if swap doesn't exist or is too small.
# Will NOT shrink swap if it's already larger than target.
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 ...

```

**Windows:**
```powershell
# Expand pagefile (needs admin)
$pagefile = Get-WmiObject -Query "SELECT * FROM Win32_PageFileSetting"
$pagefile.MaximumSize = 4096  # 4GB
$pagefile.Put()
```

---

<a name="tier-3"></a>

<a name="tier-3-emergency-survival"></a>
## Tier 3: Emergency Survival

<a name="akce"></a>
### ⚙️ Akce

```python
async def execute_tier3(self):
    """Tier 3 (95%): Emergency Survival."""
    
    # 1. Minimal history
    agent.action_history = agent.action_history[-10:]
    
    # 2. Max SWAP
    await self._expand_swap(force_max=True)
    
    # 3. Minimal LLM
    await self._reduce_llm_resources(tier=3)
    
    # 4. Kill non-essential processes
    terminated = await self._terminate_non_essential_processes()
    
    # 5. Notify admin (critical)
    await agent.send_admin_dm(details, category="tier")
```

<a name="process-termination"></a>
### ⚠️ Process Termination

```python
def _terminate_non_essential_processes(self):
    """Kill Python processes except protected and self."""
    
    terminated_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        # Skip if protected
        if proc.pid in self.protected_processes:
            continue
        
        # Skip self
        if proc.pid == os.getpid():
            continue
        
        # Only Python processes
        if 'python' in proc.info['name'].lower():
            try:
                proc.terminate()
                terminated_count += 1
                logger.warning(f"Terminated process {proc.pid}: {proc.info['name']}")
            except:
                pass
    
    return terminated_count
```

---

<a name="protected-processes"></a>
## Protected Processes

<a name="registrace"></a>
### 🛡️ Registrace

```python
# Protect Discord bot process
resource_manager.register_protected_process(
    pid=discord_process.pid,
    name="Discord Bot"
)
```

<a name="seznam"></a>
### 📋 Seznam

```python
self.protected_processes = {
    12345: "Discord Bot",
    67890: "ngrok Tunnel",
    # ... self.pid automatically protected
}
```

---

<a name="network-monitor"></a>
## Network Monitor

<a name="connectivity-check"></a>
### 📡 Connectivity Check

```python
async def check_connectivity(self):
    """Check internet by pinging 8.8.8.8."""
    
    try:
        cmd = "ping -c 1 8.8.8.8" if platform.system() != "Windows" else "ping -n 1 8.8.8.8"
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        await proc.wait()
        return proc.returncode == 0
    except:
        return False
```

<a name="disconnect-handling"></a>
### 🔌 Disconnect Handling

```python
async def handle_disconnect(self):
    """Disable internet-dependent tools."""
    
    logger.warning("Internet disconnected! Disabling web tools...")
    
    # Replace web tools with offline stub
    def offline_error(**kwargs):
        return "Error: No internet connection"
    
    self.agent.tools.tools['web_tool'].execute = offline_error
    self.agent.tools.tools['weather_tool'].execute = offline_error
    
    # Notify admin
    await self.agent.send_admin_dm(
        "🔴 **Internet Disconnected**\n"
        "Web-dependent tools disabled.",
        category="tier"
    )
```

<a name="reconnect-handling"></a>
### 🔄 Reconnect Handling

```python
async def handle_reconnect(self):
    """ Restore internet-dependent tools."""
    
    logger.info("Internet reconnected! Restoring web tools...")
    
    # Re-register tools
    self.agent.tools.register(WebTool())
    self.agent.tools.register(WeatherTool())
    
    # Notify admin
    await self.agent.send_admin_dm(
        "🟢 **Internet Reconnected**\n"
        "All tools restored.",
        category="tier"
    )
```

---

<a name="monitoring-loop"></a>
## Monitoring Loop

<a name="continuous-check"></a>
### 🔁 Continuous Check

```python
async def monitor_loop(self):
    """Main monitoring loop."""
    
    while True:
        await asyncio.sleep(30)  # Check every 30s
        
        # Check resources
        usage = self.check_resources()
        new_tier = self.get_tier(usage)
        
        # Tier changed?
        if new_tier != self.current_tier:
            await self.handle_tier_change(new_tier)
        
        # Check internet
        is_online = await self.network_monitor.check_connectivity()
        
        if is_online != self.network_monitor.is_online:
            if is_online:
                await self.network_monitor.handle_reconnect()
            else:
                await self.network_monitor.handle_disconnect()
```

---

<a name="usage-statistics"></a>
## Usage Statistics

<a name="resourceusage-dataclass"></a>
### 📊 ResourceUsage Dataclass

```python
@dataclass
class ResourceUsage:
    """Resource usage snapshot."""
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    swap_percent: float
    timestamp: float
```

<a name="check-resources"></a>
### 🔧 Check Resources

```python
def check_resources(self):
    """Get current resource usage."""
    
    return ResourceUsage(
    return ResourceUsage(
        cpu_percent=psutil.cpu_percent(interval=1.0),
        ram_percent=psutil.virtual_memory().percent,
        disk_percent=psutil.disk_usage('/').percent,
        swap_percent=psutil.swap_memory().percent,
        timestamp=time.time()
    )
```

---

<a name="integration"></a>
## Integration

<a name="v-corepy"></a>
### 🔧 V core.py

```python
# Initialize resource manager
self.resource_manager = ResourceManager(self)

# Start monitoring
asyncio.create_task(self.resource_manager.monitor_loop())

# React to tier changes
async def handle_resource_tier(self, tier: int, usage):
    if tier >= 2:
        # Pause autonomous actions during high load
        self.boredom_threshold = 0.99
    else:
        # Normal threshold
        self.boredom_threshold = 0.8
```

---

<a name="související"></a>
## 🔗 Související

- [📖 LLM Integration](llm-integration.md) - Adaptivní LLM parametry
- [`!monitor`](../commands/admin.md#monitor) - Příkaz pro monitorování
- [📖 Autonomous Behavior](autonomous-behavior.md) - Reakce na tier changes
- [📚 API Reference](../api/agent-core.md)
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-10  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
