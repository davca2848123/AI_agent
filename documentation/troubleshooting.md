# 🆘 Troubleshooting Guide

> **Navigace:** [📂 Dokumentace](README.md) | [📄 Přehled (OVERVIEW)](OVERVIEW.md) | [🔍 Index (INDEX)](INDEX.md) | [📋 API Tasklist (SUMMARY)](SUMMARY.md) | [🏗️ Architektura](architecture.md) | [🆘 Troubleshooting](troubleshooting.md)

> Kompletní průvodce řešením problémů RPI AI Agenta.
> **Verze:** Beta - CLOSED

---

<a name="obsah"></a>
## 📋 Obsah

1. [Agent se nespustí](#agent-se-nespustí)
2. [LLM Problémy](#llm-problémy)
3. [Memory & Database](#memory--database)
4. [Discord Connection](#discord-connection)
5. [Resource Issues](#resource-issues)
6. [Network & SSH](#network--ssh)
7. [Command Errors](#command-errors)
8. [Diagnostic Tools](#diagnostic-tools)

---

<a name="quick-diagnostic-checklist"></a>
## 🚨 Quick Diagnostic Checklist

Před detailním troubleshootingem:

```bash
# 1. Service status
sudo systemctl status rpi-agent.service

# 2. Recent logs
sudo journalctl -u rpi-agent.service -n 50

# 3. Resource check
free -h
df -h

# 4. Process check
ps aux | grep python3
```

**Z Windows:**
```batch
scripts\rpi_health_check.bat
```

**Z Discordu:**
```
!status
!debug quick
```

---

<a name="agent-se-nespustí"></a>
## 🔴 Agent se nespustí

<a name="symptom-service-failed-to-start"></a>
### Symptom: Service Failed to Start

**Check:**
```bash
sudo systemctl status rpi-agent.service
```

**Error Output:**
```
● rpi-agent.service - RPI AI Discord Agent
   Loaded: loaded
   Active: failed (Result: exit-code)
```

<a name="solution-1-check-logs"></a>
### Solution 1: Check Logs

```bash
# View full error
sudo journalctl -u rpi-agent.service -n 100 --no-pager

# Common errors:
# - "ModuleNotFoundError" → Missing dependency
# - "FileNotFoundError" → Missing config file
# - "PermissionError" → Wrong file permissions
```

<a name="solution-2-missing-dependencies"></a>
### Solution 2: Missing Dependencies

```bash
cd ~/rpi_ai/rpi_ai

# Reinstall all dependencies
pip3 install -r requirements.txt --break-system-packages

# Check specific module
python3 -c "import discord; print('OK')"
python3 -c "from llama_cpp import Llama; print('OK')"
```

**From Windows:**
```batch
scripts\rpi_rebuild_python.bat
```

<a name="solution-3-config-issues"></a>
### Solution 3: Config Issues

**Check config files exist:**
```bash
cd ~/rpi_ai/rpi_ai

# Should exist:
ls -la config_settings.py
ls -la config_secrets.py

# If missing secrets:
cp config_secrets.py.example config_secrets.py
nano config_secrets.py  # Add your tokens
```

**Verify Discord token:**
```python
# In config_secrets.py
DISCORD_BOT_TOKEN = "YOUR_TOKEN_HERE"  # Must start with "MT..."
ADMIN_USER_IDS = [123456789012345678]  # Your Discord user ID
```

<a name="solution-4-restart-service"></a>
### Solution 4: Restart Service

```bash
# Daemon reload if service file changed
sudo systemctl daemon-reload

# Restart
sudo systemctl restart rpi-agent.service

# Check status
sudo systemctl status rpi-agent.service
```

<a name="solution-5-manual-test"></a>
### Solution 5: Manual Test

```bash
cd ~/rpi_ai/rpi_ai

# Run manually to see errors
python3 main.py

# If it works manually but not as service:
# - Check user permissions in service file
# - Verify WorkingDirectory path
```

---

<a name="llm-problémy"></a>
## 🧠 LLM Problémy

<a name="symptom-llm-not-available"></a>
### Symptom: "LLM not available"

**Discord shows:**
```
!status
📊 Agent Status
• LLM: ❌ Offline (LLM not available)
```

> **Note:** If **Gemini API** is configured, this functionality is downgraded from **ERROR** to **WARNING**. The agent will automatically fallback to Gemini for `!ask` commands even if the local LLM is missing or fails to load. The status might show Offline for Local LLM, but `!ask` will still function via Cloud.

<a name="solution-1-check-model-file"></a>
### Solution 1: Check Model File

```bash
cd ~/rpi_ai/rpi_ai

# Check if model exists
ls -lh models/

# Expected:
# qwen2.5-0.5b-instruct-q4_k_m.gguf (~330 MB)
```

**If missing:**
```bash
python3 scripts/fix_llm_full.py
```

**From Windows:**
```batch
scripts\rpi_fix_llm.bat
```

<a name="solution-2-memory-issues"></a>
### Solution 2: Memory Issues

**LLM needs ~800 MB RAM:**
```bash
free -h

#               total        used        free
# Mem:          3.8Gi       3.2Gi       100Mi  ← TOO LOW!
# Swap:         4.0Gi       1.5Gi       2.5Gi
```

**Fix - Increase SWAP:**
```bash
# Check current
swapon --show

# If no swap or too small:
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096  # 4GB
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**From Windows:**
```batch
scripts\rpi_setup_swap.bat
```

<a name="solution-3-llm-loading-timeout"></a>
### Solution 3: LLM Loading Timeout

**Error in logs:**
```
[ERROR] Failed to load model: timeout
```

**Fix - Increase load timeout:**
```python
# In agent/llm.py - increase timeout
model = Llama(model_path=..., n_ctx=1024, n_threads=2)
```

**Or reduce context window:**
```python
# In config_settings.py
LLM_CONTEXT_NORMAL = 512  # Instead of 1024
```

<a name="solution-4-corrupted-model-file"></a>
### Solution 4: Corrupted Model File

```bash
cd ~/rpi_ai/rpi_ai/models

# Check file size
ls -lh qwen2.5-0.5b-instruct-q4_k_m.gguf

# Should be ~330 MB
# If smaller or 0 bytes:
rm qwen2.5-0.5b-instruct-q4_k_m.gguf

# Re-download
python3 scripts/fix_llm_full.py
```

📖 [Více info v Local Models Guide](configuration/models.md)
```

<a name="solution-5-llama-cpp-python-issue"></a>
### Solution 5: llama-cpp-python Issue

```bash
# Reinstall llama-cpp-python
pip3 uninstall llama-cpp-python -y
pip3 install llama-cpp-python --break-system-packages
```

---

<a name="gemini-issues"></a>
## ☁️ Gemini Problémy

<a name="symptom-404-model-not-found"></a>
### Symptom: 404 Model Not Found

**Chyba:**
```
Gemini Error: 404 models/gemini-1.5-flash is not found
```

**Řešení:**
Váš API klíč pravděpodobně nemá přístup k této specifické verzi modelu.
Použijte aliasy `latest` v `config_settings.py`:
```python
GEMINI_MODEL_FAST = "gemini-flash-latest"
GEMINI_MODEL_HIGH = "gemini-pro-latest"
```

<a name="symptom-api-key-missing"></a>
### Symptom: API Key Missing

**Chyba:**
```
Gemini Error: API Key not configured
```

**Řešení:**
Ykontrolujte `config_secrets.py`:
```python
GEMINI_API_KEY = "AIzaSy..."
```

---

<a name="memory--database"></a>

<a name="memory-database"></a>
## 💾 Memory & Database

<a name="symptom-database-corruption"></a>
### Symptom: Database Corruption

**Errors:**
```
sqlite3.DatabaseError: database disk image is malformed
[ERROR] Database corrupted!
```

<a name="solution-1-auto-recovery"></a>
### Solution 1: Auto-Recovery

Agent should auto-recover:
```
[ERROR] Database corrupted! Auto-recovering...
[INFO] Backed up corrupted DB to agent_memory.db.corrupted
[INFO] Created fresh database
```

**Manual recovery:**
```bash
cd ~/rpi_ai/rpi_ai

# 1. Backup corrupted
mv agent_memory.db agent_memory.db.corrupted

# 2. Restore from backup
cp backup/agent_memory_2025-12-03.db agent_memory.db

# 3. Restart
sudo systemctl restart rpi-agent.service
```

<a name="solution-2-database-too-large"></a>
### Solution 2: Database Too Large

**Check size:**
```bash
ls -lh agent_memory.db

# If > 50 MB, cleanup needed
```

**Cleanup:**
```batch
# From Windows
scripts\rpi_cleanup_memory.bat
```

**Or manually:**
```bash
cd ~/rpi_ai/rpi_ai
python3 scripts/internal/cleanup_memory.py
```

📖 [Manuální správa viz Memory Manager](scripts/memory-manager.md)
```

<a name="solution-3-fts-index-issues"></a>
### Solution 3: FTS Index Issues

**Error:**
```
[ERROR] FTS index corrupted
```

**Fix:**
```bash
cd ~/rpi_ai/rpi_ai

# Rebuild FTS index
sqlite3 agent_memory.db <<EOF
DROP TABLE IF EXISTS memories_fts;
CREATE VIRTUAL TABLE memories_fts USING fts5(content, content=memories, content_rowid=id);
INSERT INTO memories_fts(memories_fts) VALUES('rebuild');
EOF
```

<a name="solution-4-memory-scoring-not-working"></a>
### Solution 4: Memory Scoring Not Working

**Symptoms:**
- All memories rejected
- Score always below 70

**Debug:**
```python
# In memory.py - add debug logging
logger.info(f"Score: {score}, Keywords: {keyword_matches}, Unique: {is_unique}")
```

**Check config:**
```python
# In config_settings.py
MEMORY_CONFIG = {
    'MIN_SCORE_TO_SAVE': 70,  # Try lowering to 50 temporarily
    'KEYWORDS': ['python', 'discord', ...],  # Make sure it's populated
}
```

---

<a name="discord-connection"></a>
## 💬 Discord Connection

<a name="symptom-bot-offline"></a>
### Symptom: Bot Offline

**Discord shows bot as offline**

<a name="solution-1-check-token"></a>
### Solution 1: Check Token

```python
# In config_secrets.py
DISCORD_BOT_TOKEN = "MTx...xyz"  # Must be valid

# Test token validity:
import discord
client = discord.Client(intents=discord.Intents.default())
client.run("YOUR_TOKEN")  # Should connect or show error
```

<a name="solution-2-check-intents"></a>
### Solution 2: Check Intents

**Error:**
```
discord.errors.PrivilegedIntentsRequired
```

**Fix:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot
3. Go to "Bot" tab
4. Enable:
   - ✅ **MESSAGE CONTENT INTENT** (CRITICAL!)
   - ✅ Presence Intent
   - ✅ Server Members Intent

**Then restart:**
```bash
sudo systemctl restart rpi-agent.service
```

<a name="solution-3-network-issues"></a>
### Solution 3: Network Issues

```bash
# Test internet
ping discord.com

# If fails:
# - Check WiFi/Ethernet connection
# - Check router
# - Check DNS: ping 8.8.8.8
```

<a name="symptom-commands-not-responding"></a>
### Symptom: Commands Not Responding

**Bot online but doesn't react to commands**

<a name="solution-1-check-permissions"></a>
### Solution 1: Check Permissions

**In Discord:**
1. Right-click channel → Edit Channel
2. Go to Permissions
3. Find your bot
4. Ensure:
   - ✅ Read Messages
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Attach Files

<a name="solution-2-command-queue-stuck"></a>
### Solution 2: Command Queue Stuck

```bash
# Check logs for queue errors
sudo journalctl -u rpi-agent.service | grep -i "queue"

# Restart to clear queue
sudo systemctl restart rpi-agent.service
```

---

<a name="resource-issues"></a>
## 📊 Resource Issues

<a name="symptom-high-cpu-usage"></a>
### Symptom: High CPU Usage

**CPU at 100% constantly**

<a name="solution-1-check-process"></a>
### Solution 1: Check Process

```bash
# Find CPU hog
top -u davca

# If python3 is 100%:
# - LLM inference stuck?
# - Infinite loop?
# - Check logs for repeating errors
```

<a name="symptom-cant-keep-up"></a>
### Symptom: "Can't keep up" / Heartbeat Blocked

**Logs:**
```
discord.gateway: Can't keep up, shard ID None websocket is 60.4s behind.
shard ID None heartbeat blocked for more than 10 seconds.
```

**Cause:**
System je přetížen (CPU 100%), obvykle kvůli příliš agresivnímu nastavení LLM Threads. Discord klient nedostává CPU čas na udržení spojení.

**Fix:**
Snížit počet vláken pro LLM v `config_settings.py`:
```python
LLM_THREADS_TIER2 = 2
LLM_THREADS_TIER3 = 1  # Critical for stability
```

<a name="solution-2-resource-tier"></a>
### Solution 2: Resource Tier

**Agent should auto-adjust:**
```
[WARNING] Resource tier 3: Context 2048 -> 1024, Threads 4 -> 1
```

**Force lower tier:**
```python
# In config_settings.py
LLM_CONTEXT_NORMAL = 1024  # Lower context = less CPU
```

<a name="symptom-high-ram-usage"></a>
### Symptom: High RAM Usage

**RAM > 90%**

<a name="solution-1-check-swap"></a>
### Solution 1: Check SWAP

```bash
free -h

#               total        used        free
# Mem:          3.8Gi       3.5Gi       300Mi
# Swap:         4.0Gi       2.0Gi       2.0Gi  ← Good, using swap
```

**If no swap:**
```batch
scripts\rpi_setup_swap.bat
```

<a name="solution-2-memory-leaks"></a>
### Solution 2: Memory Leaks

```bash
# Monitor over time
watch -n 5 'free -h'

# If RAM constantly growing:
# - Check logs for repeated actions
# - Restart service daily (temporary fix)
```

<a name="symptom-disk-full"></a>
### Symptom: Disk Full

**Error:**
```
OSError: [Errno 28] No space left on device
```

<a name="solution-1-check-disk"></a>
### Solution 1: Check Disk

```bash
df -h

# Filesystem      Size  Used Avail Use% Mounted on
# /dev/root        28G   27G  1.0G  96% /    ← CRITICAL!
```

<a name="solution-2-cleanup"></a>
### Solution 2: Cleanup

```bash
cd ~/rpi_ai/rpi_ai

# 1. Clean logs
rm agent.log.old
./scripts/task_prune_logs.py

# 2. Clean old backups
rm backup/agent_memory_2025-11-*.db

# 3. Clean temp files
rm -rf __pycache__/
find . -name "*.pyc" -delete
```

**From Windows:**
```batch
scripts\rpi_cleanup_logs.bat
```

---

<a name="network--ssh"></a>

<a name="network-ssh"></a>
## 🌐 Network & SSH

<a name="symptom-cant-ssh-to-rpi"></a>
### Symptom: Can't SSH to RPI

**Error:**
```
ssh: connect to host 192.168.1.100 port 22: Connection refused
```

<a name="solution-1-check-rpi-is-on"></a>
### Solution 1: Check RPI is On

```bash
# Ping RPI
ping 192.168.1.100

# If no response:
# - RPI is off
# - Wrong IP address
# - Network issue
```

<a name="solution-2-find-rpi-ip"></a>
### Solution 2: Find RPI IP

```bash
# Scan network
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry"

# Or check router admin panel
```

<a name="solution-3-ssh-service"></a>
### Solution 3: SSH Service

**If RPI accessible but SSH fails:**
```bash
# Connect via monitor/keyboard
# Then:
sudo systemctl status ssh
sudo systemctl start ssh
```

<a name="symptom-ngrok-tunnel-issues"></a>
### Symptom: ngrok Tunnel Issues

**!ssh start fails**

<a name="solution-1-check-ngrok"></a>
### Solution 1: Check ngrok

```bash
# Is ngrok installed?
which ngrok

# If not:
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
tar xvfz ngrok-v3-stable-linux-arm64.tgz
sudo mv ngrok /usr/local/bin/
```

<a name="solution-2-auth-token"></a>
### Solution 2: Auth Token

```bash
# Set auth token (once)
ngrok config add-authtoken YOUR_TOKEN_HERE
```

<a name="solution-3-port-already-in-use"></a>
### Solution 3: Port Already in Use

**Error:**
```
ERROR: bind: address already in use
```

```bash
# Find and kill existing ngrok
pkill ngrok

# Then restart
!ssh start
```

---

<a name="solution-4-api-unreachable"></a>
### Solution 4: Tunnel API Unreachable

**Symptom:**
```
Tunnel: ⚠️ Cannot reach API
```

**Fix:**
This means ngrok process is running but unresponsive (check failed at http://127.0.0.1:4040/api/tunnels with 5s timeout).
```bash
# Kill all ngrok processes
pkill -9 ngrok

# Restart agent to respawn clean tunnel
sudo systemctl restart rpi-agent.service
```

---

<a name="command-errors"></a>
## ⚠️ Command Errors

<a name="symptom-unknown-command"></a>
### Symptom: "Unknown command"

**Input:**
```
!myscommand
```

**Output:**
```
❓ Unknown command: !myscommand. Use !help for available commands.
```

<a name="solution-1-check-fuzzy-matching"></a>
### Solution 1: Check Fuzzy Matching

**Distance > 2 won't auto-correct:**
```
!xyz     → Too far from any command
!statuses → Too far from !status (distance 2)
```

**Use !help to see valid commands**

<a name="symptom-access-denied"></a>
### Symptom: "Access Denied"

**Input:**
```
!restart
```

**Output:**
```
⛔ Access Denied. Only admins can use this command.
```

<a name="solution-check-admin-status"></a>
### Solution: Check Admin Status

```python
# In config_settings.py
ADMIN_USER_IDS = [
    123456789012345678  # Add your Discord user ID here
]
```

**Get your ID:**
1. Discord Settings → Advanced → Developer Mode: ON
2. Right-click yourself → Copy ID

<a name="symptom-command-queued-but-never-executes"></a>
### Symptom: "Command queued" but never executes

**Output:**
```
Command queued (Position: 3)
...
[Never executes]
```

<a name="solution-queue-stuck"></a>
### Solution: Queue Stuck

```bash
# Check logs for queue errors
sudo journalctl -u rpi-agent.service | grep -i "queue\|command"

# Restart to clear
sudo systemctl restart rpi-agent.service
```

---

<a name="diagnostic-tools"></a>
## 🔍 Diagnostic Tools

<a name="built-in-commands"></a>
### Built-in Commands

```
!status          # Quick check
!debug quick     # Fast diagnostic
!debug all       # Full diagnostic (admin only)
!debug llm       # LLM specific
!debug database  # Database check
!debug network   # Network test
!monitor 30      # Live resource monitoring
```

<a name="system-commands"></a>
### System Commands

```bash
# Service status
sudo systemctl status rpi-agent.service

# Logs (last 100 lines)
sudo journalctl -u rpi-agent.service -n 100

# Follow logs in real-time
sudo journalctl -u rpi-agent.service -f

# Resources
free -h          # RAM
df -h            # Disk

<a name="logging-configuration"></a>
### 📝 Logging Configuration

V rámci optimalizace ("Log Noise Reduction") jsou defaultní úrovně logování pro některé externí knihovny nastaveny na `WARNING`, aby nezahlcovaly `agent.log`.

**Omezené moduly:**
- `discord.gateway`
- `pyngrok`
- `httpcore`
- `httpx`

Pokud potřebujete debugovat tyto moduly, je nutné dočasně změnit úroveň logování v kódu (`agent/core.py` nebo `main.py`).
top              # CPU
vcgencmd measure_temp  # Temperature (RPI only)
```

<a name="windows-scripts"></a>
### Windows Scripts

```batch
# Health check (comprehensive)
scripts\rpi_health_check.bat

# Service restart
scripts\rpi_restart_service.bat

# Debug session
scripts\rpi_connect_debug.bat  (if exists)
```

<a name="database-diagnostics"></a>
### Database Diagnostics

```bash
cd ~/rpi_ai/rpi_ai

# Check integrity
sqlite3 agent_memory.db "PRAGMA integrity_check;"

# Interactive Manager
python3 scripts/internal/memory_manager.py
# 📖 Viz [Memory Manager Guide](scripts/memory-manager.md)

# Count memories
sqlite3 agent_memory.db "SELECT COUNT(*) FROM memories;"

# Check size
sqlite3 agent_memory.db "SELECT 
    COUNT(*) as count,
    SUM(LENGTH(content)) as total_size
FROM memories;"
```

---

<a name="emergency-procedures"></a>
## 🚑 Emergency Procedures

<a name="complete-reset"></a>
### Complete Reset

**⚠️ WARNING: Deletes all data!**

```bash
cd ~/rpi_ai/rpi_ai

# 1. Backup
mkdir -p ~/backup_$(date +%Y%m%d)
cp agent_memory.db ~/backup_$(date +%Y%m%d)/
cp agent.log ~/backup_$(date +%Y%m%d)/

# 2. Stop service
sudo systemctl stop rpi-agent.service

# 3. Reset database
rm agent_memory.db
python3 -c "from agent.memory import VectorStore; VectorStore()"

# 4. Clear logs
> agent.log

# 5. Restart
sudo systemctl start rpi-agent.service
```

<a name="factory-reset-nuclear-option"></a>
### Factory Reset (Nuclear Option)

```bash
# 1. Stop service
sudo systemctl stop rpi-agent.service
sudo systemctl disable rpi-agent.service

# 2. Remove service file
sudo rm /etc/systemd/system/rpi-agent.service
sudo systemctl daemon-reload

# 3. Delete project
rm -rf ~/rpi_ai

# 4. Fresh install
git clone <repo-url>
cd rpi_ai/rpi_ai
# ... follow deployment guide
```

---

<a name="common-error-messages"></a>
## 📝 Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `ModuleNotFoundError: discord` | Missing dependency | `pip3 install -r requirements.txt` |
| `LLM not available` | Model not loaded | Check memory, run fix_llm |
| `Database locked` | SQLite busy | Wait or restart service |
| `Connection refused` | Can't reach Discord | Check internet, verify token |
| `PermissionError` | File access denied | Check file ownership, sudo |
| `Memory allocation failed` | Out of RAM | Add SWAP, reduce LLM context |
| `Timeout` | Operation too slow | Increase timeout, check resources |

---

<a name="related-documentation"></a>
## 🔗 Related Documentation

- [Deployment Guide](scripts/deployment-guide.md) - Setup and configuration
- [Batch Scripts Reference](scripts/batch-scripts-reference.md) - Windows maintenance tools
- [Resource Manager](core/resource-manager.md) - Resource tier system
- [Memory System](core/memory-system.md) - Database internals
- [LLM Integration](core/llm-integration.md) - LLM troubleshooting

---

<a name="tips-best-practices"></a>
## 💡 Tips & Best Practices

<a name="prevent-issues"></a>
### Prevent Issues

1. **Regular Monitoring**
   ```batch
   # Daily health check
   scripts\rpi_health_check.bat
   ```

2. **Periodic Cleanup**
   ```bash
   # Weekly: Clean logs if > 50 MB
   # Monthly: Clean database if > 10 MB
   ```

3. **Keep Backups**
   ```bash
   # Auto-backup daily
   cp agent_memory.db backup/agent_memory_$(date +%Y%m%d).db
   ```

4. **Monitor Resources**
   ```
   !monitor 30    # Check every 30 seconds
   ```

<a name="quick-recovery-steps"></a>
### Quick Recovery Steps

1. **Check !status in Discord** - Fastest diagnostic
2. **Run health check** - Comprehensive view
3. **Check logs** - Identify root cause
4. **Try restart** - Fixes 80% of issues
5. **Restore backup** - If data corruption

<a name="log-analysis"></a>
### Log Analysis

```bash
# Common patterns to grep for:
sudo journalctl -u rpi-agent.service | grep -i "error"
sudo journalctl -u rpi-agent.service | grep -i "exception"
sudo journalctl -u rpi-agent.service | grep -i "failed"
sudo journalctl -u rpi-agent.service | grep -i "warning"
```


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](architecture.md)
- [⚙️ Konfigurace](configuration/complete-configuration-guide.md)
- [📜 Scripts Reference](scripts/batch-scripts-reference.md)
---
Poslední aktualizace: 2025-12-15  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
