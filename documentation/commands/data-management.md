# Správa Dat - Data Management Commands

> **Navigace:** [📂 Dokumentace](../README.md) | [💬 Příkazy](../README.md#commands-příkazy) | [Správa dat](data-management.md)

> Příkazy pro správu logů, paměti a export dat.
> **Verze:** Alpha

---

<a name="přehled"></a>
## 📋 Přehled

Tyto příkazy umožňují monitorovat a spravovat data agenta včetně logů, paměti a exportu statistik.

---

<a name="memory"></a>
## `!memory`

<a name="popis"></a>
### 📋 Popis
Zobrazí statistiky paměťového systému.

<a name="použití"></a>
### ⚙️ Použití
```
!memory
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

- **Total Memories** - Počet vzpomínek v databázi
- **Action History** - Počet uložených akcí

<a name="příklad"></a>
### 📝 Příklad
```
User: !memory

Bot: 💾 **Memory Statistics:**

• Total Memories: 234
• Action History: 100 entries

🚧 More detailed memory stats coming soon!
```

<a name="implementace"></a>
### 🔧 Implementace

```python
mem_count = len(agent.memory.get_recent_memories(limit=1000))
history_count = len(agent.action_history)
```

<a name="související"></a>
### 🔗 Související
- [📖 Memory System](../core/memory-system.md) - Jak paměť funguje
- [VectorStore API](../api/vector-store.md) - Memory API

---

<a name="logs"></a>
## `!logs`

<a name="popis"></a>
### 📋 Popis
Zobrazí nedávné záznamy z logů s možností filtrování.

<a name="použití"></a>
### ⚙️ Použití

**Základní:**
```
!logs
```

**S počtem řádků:**
```
!logs <N>
```

**S filtrem úrovně:**
```
!logs <level>
!logs <N> <level>
```

<a name="parametry"></a>
### 🔧 Parametry

| Parametr | Popis | Příklad |
|----------|-------|---------|
| `N ` | Počet řádků (default 20) | `!logs 50` |
| `level` | ERROR/WARNING/INFO/DEBUG | `!logs error` |
| Combined | Obojí | `!logs 100 error` |

<a name="chování"></a>
### 💡 Chování

**≤ 50 řádků** - Zobrazí v Discord message  
**\> 50 řádků** - Pošle jako soubor (`.txt`)

<a name="příklady"></a>
### 📝 Příklady

**Poslední 20 řádků (default):**
```
User: !logs

Bot: 📋 **Last 20 log entries:**
```[log output]```
```

**Specifický počet:**
```
User: !logs 100

Bot: 📋 **Last 100 log entries:**
     Sending as file...
     [file: logs_100_1733123456.txt]
```

**Filtrováno pouze errors:**
```
User: !logs error

Bot: 📋 **Last 20 log entries (ERROR only):**
```[error logs]```
```

**Kombinace:**
```
User: !logs 50 warning

Bot: 📋 **Last 50 log entries (WARNING only):**
```[warning logs]```
```

<a name="implementace"></a>
### 🔧 Implementace

**Čtení logů:**
```python
with open("agent.log", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Filter by level
if log_level:
    filtered = [line for line in lines if log_level in line]
    recent = filtered[-num_lines:]
else:
    recent = lines[-num_lines:]
```

**Soubor pro velké výstupy:**
```python
if len(recent_lines) > 50:
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    # Send as file
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Log soubor: `agent.log`
- Discord limit: 2000 znaků (truncate pokud více)
- Temp soubory se automaticky mažou po odeslání

<a name="související"></a>
### 🔗 Související
- [`!live logs`](#live-logs) - Live streaming logů
- [`!debug`](admin.md#debug) - Pokročilá diagnostika

---

<a name="live-logs"></a>
## `!live logs`

<a name="popis"></a>
### 📋 Popis
Live stream logů v reálném čase s auto-refresh.

<a name="použití"></a>
### ⚙️ Použití

**Default (60 sekund):**
```
!live logs
```

**S délkou:**
```
!live logs <duration>
```

<a name="formáty-délky"></a>
### 🔧 Formáty délky

| Format | Popis | Příklad |
|--------|-------|---------|
| `N` | N sekund | `!live logs 30` |
| `Ns` | N sekund | `!live logs 45s` |
| `Nm` | N minut | `!live logs 2m` |
| `Nh` | N hodin | `!live logs 1h` |

<a name="jak-to-funguje"></a>
### 💡 Jak to funguje

1. **Vytvoří zprávu** - Placeholder zpráva
2. **Sleduje log soubor** - Tail nové řádky
3. **Aktualizuje zprávu** - Každé 2s edituje Discord message
4. **Filtruje spam** - Discord internal logs
5. **Ukončí po době** - Finální zpráva po timeout

<a name="příklady"></a>
### 📝 Příklady

**1 minuta live:**
```
User: !live logs 1m

Bot: 📡 **System Live Logging** (Ends: 13:01:00)
```yaml
2025-12-02 13:00:15 - INFO - Agent action: Learning web_tool
2025-12-02 13:00:18 - INFO - web_tool: Completed in 0.5s
2025-12-02 13:00:22 - INFO - Memory added: web_tool usage
...
Last Update: 13:00:45
```

[Updates every 2 seconds]

[After 1 minute]

Bot: ✅ **System Live Logging Finished**
```yaml
...final logs...
Last Update: 13:01:00
```
```

<a name="implementace"></a>
### 🔧 Implementace

**Loop:**
```python
while time.time() < end_time:
    # Read new lines
    with open(log_path, 'r') as f:
        f.seek(last_position)
        new_lines = f.readlines()
        last_position = f.tell()
    
    # Filter spam
    for line in new_lines:
        if should_show_log(line):
            log_buffer.append(line)
    
    # Keep buffer trimmed (30 lines max)
    log_buffer = log_buffer[-30:]
    
    # Update message every 2s
    await msg.edit(content=formatted_output)
    await asyncio.sleep(2)
```

**Spam filter:**
```python
def should_show_log(line):
    # Filter Discord internal logs
    discord_markers = ['discord.client', 'discord.gateway', 'WebSocket']
    if any(m in line for m in discord_markers) and "ERROR" not in line:
        return False
    # Skip extremely long lines
    if len(line) > 350:
        return False
    return True
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Běží jako background task (neblokuje další příkazy)
- Max 30 řádků v bufferu
- Aktualizace každé 2s
- Pokud je zpráva smazána, vytvoří novou

<a name="související"></a>
### 🔗 Související
- [`!logs`](#logs) - Statické logy
- [`!monitor`](admin.md#monitor) - Resource monitoring

---

<a name="export"></a>
## `!export`

<a name="popis"></a>
### 📋 Popis
Exportuje data agenta (historie, paměť, statistiky).

<a name="použití"></a>
### ⚙️ Použití

**All data:**
```
!export
!export all
```

**Specific type:**
```
!export <type>
```

<a name="typy"></a>
### 🔧 Typy

| Type | Co exportuje |
|------|--------------|
| `all` | Všechny data |
| `history` | Action history |
| `memory` | Memory dump |
| `stats` | Tool statistics |

<a name="export-formáty"></a>
### 💡 Export formáty

**history** → JSON
```json
{
  "actions": [
    "Learning web_tool",
    "Research: Python tutorial",
    ...
  ],
  "count": 156
}
```

**memory** → JSON
```json
{
  "memories": [
    {
      "id": 1,
      "content": "...",
      "metadata": {...},
      "timestamp": 1733123456
    },
    ...
  ],
  "count": 234
}
```

**stats** → JSON
```json
{
  "tool_usage": {
    "web_tool": 45,
    "time_tool": 38,
    ...
  },
  "intelligence": 487,
  "uptime": 172800
}
```

<a name="příklady"></a>
### 📝 Příklady

```
User: !export memory

Bot: 💾 Exporting memory data...
     [file: memory_export_1733123456.json]
     ✅ Exported 234 memories
```

```
User: !export all

Bot: 📦 Exporting all data...
     [file: agent_export_1733123456.json]
     ✅ Complete export ready
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Soubory se posílají jako Discord attachment
-  Velké exporty mohou trvat několik sekund
- JSON formát pro jednoduchou parsování

---

<a name="souhrn"></a>
## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!memory` | Statistiky paměti | `!memory` |
| `!logs` | Zobraz logy | `!logs 50 error` |
| `!live logs` | Live stream logů | `!live logs 2m` |
| `!export` | Export dat | `!export memory` |

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
