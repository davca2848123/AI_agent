# Administrační Příkazy

> **Navigace:** [📂 Dokumentace](../README.md) | [💬 Příkazy](../README.md#commands-příkazy) | [Administrační příkazy](admin.md)

> Admin-only příkazy pro správu a diagnostiku systému.
> **Verze:** Alpha

---

<a name="přístupová-práva"></a>
## ⚠️ Přístupová práva

Všechny příkazy v této sekci jsou **pouze pro administrátory**.

**Ověření:**
```python
if author_id not in config_settings.ADMIN_USER_IDS:
    return "⛔ Access Denied. Only admins can use this command."
```

---

<a name="restart"></a>
## `!restart`

<a name="popis"></a>
### 📋 Popis
Restartuje agenta s graceful shutdown.

<a name="použití"></a>
### ⚙️ Použití
```
!restart
```

<a name="jak-to-funguje"></a>
### 💡 Jak to funguje

1. **Vytvoří restart flag** - S channel_id pro notifikaci
2. **Graceful shutdown** - Timeout 10s
3. **Pokud úspěch** - Restart pomocí `os.execv()`
4. **Pokud selže** - Nabídne Force Restart tlačítko

<a name="příklady"></a>
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

<a name="implementace"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky
- Pouze admin
- Graceful shutdown může selhat pokud jsou zablokované zdroje
- Force restart okamžitě ukončí proces
- Po restartu agent pošle notifikaci do původního kanálu

---

<a name="cmd"></a>
## `!cmd`

<a name="popis"></a>
### 📋 Popis
Spustí shell příkaz přímo na serveru.

<a name="použití"></a>
### ⚙️ Použití
```
!cmd <příkaz>
```

<a name="bezpečnost"></a>
### 💡 Bezpečnost

**⚠️ EXTRÉMNĚ NEBEZPEČNÉ**
- Pouze pro adminy
- Přímé shell execution
- Žádná sanitizace
- Může poškodit systém

<a name="příklady"></a>
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

<a name="varování"></a>
### ⚠️ VAROVÁNÍ
- Použij pouze pokud víš co děláš
- Může bricknout systém
- Nebezpečné příkazy: `rm -rf`, `dd`, `mkfs`, atd.
- Doporučeno pouze pro diagnostiku

---

<a name="monitor"></a>
## `!monitor`

<a name="popis"></a>
### 📋 Popis
Monitoruje systémové zdroje (CPU, RAM, Disk, Swap) v reálném čase.

<a name="použití"></a>
### ⚙️ Použití

**Snapshot (okamžitě):**
```
!monitor
```

**Live monitoring:**
```
!monitor <duration>
```

<a name="formáty-délky"></a>
### 🔧 Formáty délky

Stejné jako `!live logs`:
- `30` - 30 sekund
- `2m` - 2 minuty
- `1h` - 1 hodina

<a name="příklady"></a>
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

<a name="implementace"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky
- Live mode běží jako background task
- Aktualizace každé 2s
- RPI temperature pouze na Raspberry Pi (Linux)

---

<a name="ssh"></a>
## `!ssh`

<a name="popis"></a>
### 📋 Popis
Spravuje SSH tunel pomocí ngrok.

<a name="použití"></a>
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

<a name="příklady"></a>
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

<a name="implementace"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky
- Vyžaduje ngrok nainstalovaný
- Pouze pro admin
- Ngrok může vyžadovat auth token
- Windows network drive vyžaduje WinFsp + SSHFS-Win

---

<a name="debug"></a>
## `!debug`

<a name="popis"></a>
### 📋 Popis
Pokročilá diagnostika systému s detailními kontrolami.

<a name="použití"></a>
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

<a name="oblasti"></a>
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

<a name="příklady"></a>
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

<a name="poznámky"></a>
### ⚠️ Poznámky
- Pouze admin
- Některé testy mohou trvat několik sekund
- `all` může generovat dlouhý output

---

<a name="web"></a>
## `!web`

<a name="popis"></a>
### 📋 Popis
Správa web interface (Flask server + ngrok tunnel).

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

**Start web interface:**
```
User: !web start

Bot: 🌐 Starting web tunnel... please wait.

[5 seconds later]

Bot: ✅ **Web Interface Online!**

Klikněte na tlačítko pro otevření:
[🏠 Dashboard] [📚 Documentation]
```

**Stop:**
```
User: !web stop

Bot: 🛑 Stopping web interface...
     ✅ **Web Interface Stopped**
     
     Ngrok tunel byl ukončen.
```

<a name="implementace"></a>
### 🔧 Implementace

**Komponenty:**
- Flask server (auto port 5001-5020)
- Ngrok tunnel (публічний URL)
- Markdown renderer
- Search functionality (fuzzy + exact)
- Dashboard s real-time stats

<a name="poznámky"></a>
### ⚠️ Poznámky
- Automatický výběr volného portu
- Ngrok tunnel zůstává aktivní i po Flask restart
- Web interface obsahuje dokumentaci + search
- Dashboard auto-refresh (konfigurovatelný interval)

---

<a name="topic"></a>
## `!topic`

<a name="popis"></a>
### 📋 Popis
Správa topics pro autonomous boredom system (admin only).

<a name="použití"></a>
### ⚙️ Použití

**List topics:**
```
!topic
!topic list
```

**Add topic:**
```
!topic add <text>
```

**Remove topic:**
```
!topic remove <index>
```

**Clear all:**
```
!topic clear
```

<a name="příklady"></a>
### 📝 Příklady

**List:**
```
User: !topic

Bot: 📚 **Boredom Topics** (5):
1. Learn about Python decorators
2. Explore new web scraping techniques  
3. Study async programming patterns
4. Research AI model optimization
5. Learn about Docker containers
```

**Add:**
```
User: !topic add Study quantum computing basics

Bot: ✅ Topic added! (6 total topics)
```

**Remove:**
```
User: !topic remove 3

Bot: ✅ Removed topic: "Study async programming patterns"
     (5 remaining topics)
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- **Admin only** - všechny operace
- Topics jsou uloženy v `boredom_topics.json`
- Agent vybere random topic při vysoké boredom
- Topics persistují přes restart

---

<a name="report"></a>
## `!report`

<a name="popis"></a>
### 📋 Popis
Generate report o posledním user command.

<a name="použití"></a>
### ⚙️ Použití
```
!report
```

<a name="příklady"></a>
### 📝 Příklady

```
User: !ask what is Python?

[Agent responds...]

User: !report

Bot: 📊 **Last Command Report:**

**User:** JohnDoe#1234
**Command:** !ask what is Python?
**Timestamp:** 2025-12-04 22:30:15
**Time ago:** 2 minutes ago

**Context:**
- Channel: #general
- Server: My Discord Server
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Admin only
- Sleduje poslední non-report command
- Užitečné pro debugging interakcí
- Data v paměti (nepersistuje přes restart)

---

<a name="upload"></a>
## `!upload`

<a name="popis"></a>
### 📋 Popis
Upload nové release na GitHub (admin only).

<a name="použití"></a>
### ⚙️ Použití
```
!upload
```

<a name="příklady"></a>
### 📝 Příklady

**Successful upload:**
```
User: !upload

Bot: 🚀 **GitHub Release Upload**
     Checking rate limit...
     
     📦 Creating release... (this may take ~30s)
     
     ✅ **GitHub Release Created Successfully!**
     
     📍 Check: https://github.com/davca2848123/AI_agent/releases
     ⏰ Next upload available in: **2 hours**
```

**Rate limited:**
```
User: !upload

Bot: ⏳ **Rate Limit Active**
     
     Uploads are limited to once every 2 hours.
     ⏰ Try again in: **1h 45m**
     
     _This prevents accidental spam and excessive API usage._
```

<a name="implementace"></a>
### 🔧 Implementace

**Rate limiting:**
- Minimální 2 hodiny mezi uploady
- Timestamp uložen v `.last_github_upload`
- Kontrola před uploadem

**GitHub API:**
```python
from scripts.github_release import create_release
create_release(github_token, repo_name, branch, force=False, min_hours=2)
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- **Admin only**
- Vyžaduje `GITHUB_TOKEN` v `config_secrets.py`  
- 2-hour rate limit
- Creates timestamped release
- Asyncio executor pro non-blocking

---

<a name="disable"></a>
## `!disable`

<a name="popis"></a>
### 📋 Popis
Disable interaction pro non-admin uživatele (admin only).

<a name="použití"></a>
### ⚙️ Použití
```
!disable
```

<a name="příklady"></a>
### 📝 Příklady

```
User (Admin): !disable

Bot: 🔒 **Interaction Disabled**
     I will now ignore commands from non-admin users.

[Later]

User (Non-admin): !help

[No response]

User (Admin): !help

Bot: 🤖 **AI Agent - Nápověda Příkazů**...
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- **Admin only**
- Admins můžou vždy použít příkazy
- Global flag: `CommandHandler.global_interaction_enabled`
- 

Non-persistent (reset při restartu)
- Užitečné pro maintenance nebo testing

---

<a name="enable"></a>
## `!enable`

<a name="popis"></a>
### 📋 Popis
Enable interaction pro všechny uživatele (admin only).

<a name="použití"></a>
### ⚙️ Použití
```
!enable
```

<a name="příklady"></a>
### 📝 Příklady

```
User (Admin): !enable

Bot: 🔓 **Interaction Enabled**
     I am now listening to all users.

[Later]

User (Non-admin): !help

Bot: 🤖 **AI Agent - Nápověda Příkazů**...
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- **Admin only**
- Obnova normálního stavu
- Default state je enabled
- Párový příkaz s `!disable`

---

<a name="souhrn"></a>
## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!restart` | Restart agenta | `!restart` |
| `!monitor` | Resource monitoring | `!monitor 30` |
| `!debug` | Diagnostika | `!debug llm` |
| `!ssh` | SSH tunnel správa | `!ssh start` |
| `!cmd` | Shell command | `!cmd ls -la` |
| `!web` | Web interface | `!web start` |
| `!topic` | Manage topics | `!topic add <text>` |
| `!report` | Last command report | `!report` |
| `!upload` | GitHub release | `!upload` |
| `!disable` | Disable non-admin | `!disable` |
| `!enable` | Enable all users | `!enable` |

**Celkem:** 10 admin příkazů (requires `ADMIN_USER_IDS`)

---

<a name="restricted-commands"></a>
## ⛔ Commands Restricted to Admin

Následující shell příkazy jsou v rámci `!cmd` blokovány i pro administrátory, pokud nejsou explicitně povoleny v kódu (bezpečnostní pojistka).

| Příkaz | Důvod |
|--------|-------|
| `shutdown` | Vypnutí serveru |
| `reboot` | Restart serveru |
| `kill` | Ukončení procesů |
| `rm -rf` | Destruktivní mazání |
| `mkfs` | Formátování disku |
| `dd` | Přímý zápis na disk |
| `:(){ :|:& };:` | Fork bomb |

**Konfigurace:**
Seznam je definován v `config_settings.py` jako `ADMIN_RESTRICTED_COMMANDS`.

---
Poslední aktualizace: 2025-12-05  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
