# Administrační Příkazy

> Admin-only příkazy pro správu a diagnostiku systému

## ⚠️ Přístupová práva

Všechny příkazy v této sekci jsou **pouze pro administrátory**.

**Ověření:**
```python
if author_id not in config_settings.ADMIN_USER_IDS:
    return "⛔ Access Denied. Only admins can use this command."
```

---

## `!restart`

### 📋 Popis
Restartuje agenta s graceful shutdown.

### ⚙️ Použití
```
!restart
```

### 💡 Jak to funguje

1. **Vytvoří restart flag** - S channel_id pro notifikaci
2. **Graceful shutdown** - Timeout 10s
3. **Pokud úspěch** - Restart pomocí `os.execv()`
4. **Pokud selže** - Nabídne Force Restart tlačítko

### 📝 Příklady

**Úspěšný restart:**
```
User: !restart

Bot: 🔄 Restarting agent...

[10 seconds later]

Bot: ✅ Agent restarted successfully!
     Uptime: 0 minutes
```

**Neúspěšný shutdown:**
```
User: !restart

Bot: 🔄 Restarting agent...

[After timeout ]

Bot: ⚠️ **Graceful shutdown failed or timed out**

     Some resources may not have closed properly.
     Choose an option:
     
     [Force Restart] [Cancel]
```

### 🔧 Implementace

**Restart flag:**
```python
restart_info = {
    "channel_id": channel_id,
    "author": author,
    "timestamp": time.time()
}
with open(".restart_flag", "w") as f:
    json.dump(restart_info, f)
```

**Graceful shutdown:**
```python
shutdown_success = await agent.graceful_shutdown(timeout=10)
```

**Force restart:**
```python
os.execv(sys.executable, [sys.executable] + sys.argv)
```

### ⚠️ Poznámky
- Pouze admin
- Graceful shutdown může selhat pokud jsou zablokované zdroje
- Force restart okamžitě ukončí proces
- Po restartu agent pošle notifikaci do původního kanálu

---

## `!cmd`

### 📋 Popis
Spustí shell příkaz přímo na serveru.

### ⚙️ Použití
```
!cmd <příkaz>
```

### 💡 Bezpečnost

**⚠️ EXTRÉMNĚ NEBEZPEČNÉ**
- Pouze pro adminy
- Přímé shell execution
- Žádná sanitizace
- Může poškodit systém

### 📝 Příklady

```
User: !cmd ls -la

Bot: 📟 **Command Output:**
```
total 1024
drwxr-xr-x  10 user  group   320 Dec  2 13:00 .
drwxr-xr-x  15 user  group   480 Dec  1 10:00 ..
...
```
```

```
User: !cmd python --version

Bot: 📟 **Command Output:**
```
Python 3.11.5
```
```

### ⚠️ VAROVÁNÍ
- Použij pouze pokud víš co děláš
- Může bricknout systém
- Nebezpečné příkazy: `rm -rf`, `dd`, `mkfs`, atd.
- Doporučeno pouze pro diagnostiku

---

## `!monitor`

### 📋 Popis
Monitoruje systémové zdroje (CPU, RAM, Disk, Swap) v reálném čase.

### ⚙️ Použití

**Snapshot (okamžitě):**
```
!monitor
```

**Live monitoring:**
```
!monitor <duration>
```

### 🔧 Formáty délky

Stejné jako `!live logs`:
- `30` - 30 sekund
- `2m` - 2 minuty
- `1h` - 1 hodina

### 📝 Příklady

**Snapshot:**
```
User: !monitor

Bot: 📊 **System Resources:**

CPU: ▓▓▓▓░░░░░░ 45%
RAM: ▓▓▓▓▓▓▓░░░ 72%
Disk: ▓▓▓░░░░░░░ 28%
Swap: ▓░░░░░░░░░ 12%

Temperature: 52°C
Uptime: 2d 5h 23m
```

**Live monitoring (30s):**
```
User: !monitor 30

Bot: 📊 **Live Resource Monitor** (Ends: 13:05:30)
```yaml
CPU:  ████████░░ 78%
RAM:  ██████░░░░ 65%
Disk: ███░░░░░░░ 28%
Swap: █░░░░░░░░░ 15%

[GPU: N/A]
Temp: 54°C

Last: 13:05:12
```

[Updates every 2s]
```

### 🔧 Implementace

**Resource check:**
```python
cpu = psutil.cpu_percent(interval=0.5)
ram = psutil.virtual_memory().percent
disk = psutil.disk_usage('/').percent
swap = psutil.swap_memory().percent
```

**RPI Temperature:**
```python
# Linux only - vcgencmd
result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True)
temp = result.stdout.decode() # temp=54.2'C
```

### ⚠️ Poznámky
- Live mode běží jako background task
- Aktualizace každé 2s
- RPI temperature pouze na Raspberry Pi (Linux)

---

## `!ssh`

### 📋 Popis
Spravuje SSH tunel pomocí ngrok.

### ⚙️ Použití

**Start tunnel:**
```
!ssh start
```

**Stop tunnel:**
```
!ssh stop
```

**Restart tunnel:**
```
!ssh restart
```

**Status:**
```
!ssh
```

### 📝 Příklady

**Start:**
```
User: !ssh start

Bot: 🌐 Starting ngrok SSH tunnel...

[5 seconds later]

Bot: ✅ **SSH Tunnel Active**

📋 Connection details:
ssh davca@0.tcp.ngrok.io -p 12345

🪟 Windows network drive:
net use Z: \\sshfs\davca@0.tcp.ngrok.io!12345

[Copy SSH] [Copy Net Use]
```

**Stop:**
```
User: !ssh stop

Bot: 🛑 Stopping SSH tunnel...
     ✅ Tunnel stopped
```

**Status:**
```
User: !ssh

Bot: 📡 **SSH Status:**
     • Tunnel: Active
     • Host: 0.tcp.ngrok.io
     • Port: 12345
     • Uptime: 2h 15m
```

### 🔧 Implementace

**Start ngrok:**
```python
process = subprocess.Popen(
    ['ngrok', 'tcp', '22'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
```

**Get public URL:**
```python
async with aiohttp.ClientSession() as session:
    async with session.get('http://localhost:4040/api/tunnels') as resp:
        data = await resp.json()
        public_url = data['tunnels'][0]['public_url']
```

### ⚠️ Poznámky
- Vyžaduje ngrok nainstalovaný
- Pouze pro admin
- Ngrok může vyžadovat auth token
- Windows network drive vyžaduje WinFsp + SSHFS-Win

---

## `!debug`

### 📋 Popis
Pokročilá diagnostika systému s detailními kontrolami.

### ⚙️ Použití

**All checks:**
```
!debug
!debug all
```

**Specific area:**
```
!debug <area>
```

### 🔧 Oblasti

| Area | Co kontroluje |
|------|---------------|
| `all` | Všechny oblasti |
| `quick` | Základní rychlé testy |
| `tools` | Tool registrace a funkčnost |
| `llm` | LLM status a latence |
| `network` | Internet a  DNS |
| `ngrok` | Ngrok tunel status |
| `database` | Memory database health |
| `filesystem` | Disk space a permissions |
| `memory` | Python memory usage |

### 📝 Příklady

**Quick check:**
```
User: !debug quick

Bot: 🔍 **Quick Diagnostic:**

✅ LLM: Online (250ms)
✅ Internet: Connected
✅ Discord: Ready
✅ Database: OK
⚠️ Disk: 85% (15GB free)
```

**LLM detailed:**
```
User: !debug llm

Bot: 🧠 **LLM Diagnostic:**

**Status:** ✅ Online
**Provider:** Local (llama-cpp)
**Model:** Qwen2.5-0.5B-Instruct
**Latency:** 245ms (avg)
**Context Window:** 2048 tokens
**Threads:** 4

**Test Generation:**
Prompt: "ping"
Response: "pong"
Time: 0.245s
✅ Pass
```

**Database check:**
```
User: !debug database

Bot: 💾 **Database Diagnostic:**

**File:** agent_memory.db
**Size:** 1.2 MB
**Tables:** 3 (memories, metadata, fts_index)
**Total Records:** 234
**FTS Index:** ✅ Healthy
**Last Backup:** 2h ago

**Test Query:**
```SELECT COUNT(*) FROM memories``` → 234
✅ Pass
```

### ⚠️ Poznámky
- Pouze admin
- Některé testy mohou trvat několik sekund
- `all` může generovat dlouhý output

---

## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!restart` | Restart agenta | `!restart` |
| `!cmd` | Shell command | `!cmd ls -la` |
| `!monitor` | Resource monitoring | `!monitor 30` |
| `!ssh` | Manage SSH tunnel | `!ssh start` |
| `!debug` | Diagnostika | `!debug llm` |

---

**Poslední aktualizace:** 2025-12-02  
**Platné pro verzi:** 1.0.0
