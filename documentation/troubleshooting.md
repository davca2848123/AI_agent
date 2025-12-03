# 🆘 Troubleshooting Guide

> Kompletní průvodce řešením problémů RPI AI Agenta

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

## 🔴 Agent se nespustí

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

### Solution 1: Check Logs

```bash
# View full error
sudo journalctl -u rpi-agent.service -n 100 --no-pager

# Common errors:
# - "ModuleNotFoundError" → Missing dependency
# - "FileNotFoundError" → Missing config file
# - "PermissionError" → Wrong file permissions
```

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

### Solution 4: Restart Service

```bash
# Daemon reload if service file changed
sudo systemctl daemon-reload

# Restart
sudo systemctl restart rpi-agent.service

# Check status
sudo systemctl status rpi-agent.service
```

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

## 🧠 LLM Problémy

### Symptom: "LLM not available"

**Discord shows:**
```
!status
📊 Agent Status
• LLM: ❌ Offline (LLM not available)
```

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

### Solution 5: llama-cpp-python Issue

```bash
# Reinstall llama-cpp-python
pip3 uninstall llama-cpp-python -y
pip3 install llama-cpp-python --break-system-packages
```

---

## 💾 Memory & Database

### Symptom: Database Corruption

**Errors:**
```
sqlite3.DatabaseError: database disk image is malformed
[ERROR] Database corrupted!
```

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

## 💬 Discord Connection

### Symptom: Bot Offline

**Discord shows bot as offline**

### Solution 1: Check Token

```python
# In config_secrets.py
DISCORD_BOT_TOKEN = "MTx...xyz"  # Must be valid

# Test token validity:
import discord
client = discord.Client(intents=discord.Intents.default())
client.run("YOUR_TOKEN")  # Should connect or show error
```

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

### Solution 3: Network Issues

```bash
# Test internet
ping discord.com

# If fails:
# - Check WiFi/Ethernet connection
# - Check router
# - Check DNS: ping 8.8.8.8
```

### Symptom: Commands Not Responding

**Bot online but doesn't react to commands**

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

### Solution 2: Command Queue Stuck

```bash
# Check logs for queue errors
sudo journalctl -u rpi-agent.service | grep -i "queue"

# Restart to clear queue
sudo systemctl restart rpi-agent.service
```

---

## 📊 Resource Issues

### Symptom: High CPU Usage

**CPU at 100% constantly**

### Solution 1: Check Process

```bash
# Find CPU hog
top -u davca

# If python3 is 100%:
# - LLM inference stuck?
# - Infinite loop?
# - Check logs for repeating errors
```

### Solution 2: Resource Tier

**Agent should auto-adjust:**
```
[WARNING] Resource tier 2: Context 1024 -> 512
```

**Force lower tier:**
```python
# In config_settings.py
LLM_CONTEXT_NORMAL = 512  # Lower context = less CPU
```

### Symptom: High RAM Usage

**RAM > 90%**

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

### Solution 2: Memory Leaks

```bash
# Monitor over time
watch -n 5 'free -h'

# If RAM constantly growing:
# - Check logs for repeated actions
# - Restart service daily (temporary fix)
```

### Symptom: Disk Full

**Error:**
```
OSError: [Errno 28] No space left on device
```

### Solution 1: Check Disk

```bash
df -h

# Filesystem      Size  Used Avail Use% Mounted on
# /dev/root        28G   27G  1.0G  96% /    ← CRITICAL!
```

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

## 🌐 Network & SSH

### Symptom: Can't SSH to RPI

**Error:**
```
ssh: connect to host 192.168.1.100 port 22: Connection refused
```

### Solution 1: Check RPI is On

```bash
# Ping RPI
ping 192.168.1.100

# If no response:
# - RPI is off
# - Wrong IP address
# - Network issue
```

### Solution 2: Find RPI IP

```bash
# Scan network
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry"

# Or check router admin panel
```

### Solution 3: SSH Service

**If RPI accessible but SSH fails:**
```bash
# Connect via monitor/keyboard
# Then:
sudo systemctl status ssh
sudo systemctl start ssh
```

### Symptom: ngrok Tunnel Issues

**!ssh start fails**

### Solution 1: Check ngrok

```bash
# Is ngrok installed?
which ngrok

# If not:
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
tar xvfz ngrok-v3-stable-linux-arm64.tgz
sudo mv ngrok /usr/local/bin/
```

### Solution 2: Auth Token

```bash
# Set auth token (once)
ngrok config add-authtoken YOUR_TOKEN_HERE
```

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

## ⚠️ Command Errors

### Symptom: "Unknown command"

**Input:**
```
!myscommand
```

**Output:**
```
❓ Unknown command: !myscommand. Use !help for available commands.
```

### Solution 1: Check Fuzzy Matching

**Distance > 2 won't auto-correct:**
```
!xyz     → Too far from any command
!statuses → Too far from !status (distance 2)
```

**Use !help to see valid commands**

### Symptom: "Access Denied"

**Input:**
```
!restart
```

**Output:**
```
⛔ Access Denied. Only admins can use this command.
```

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

### Symptom: "Command queued" but never executes

**Output:**
```
Command queued (Position: 3)
...
[Never executes]
```

### Solution: Queue Stuck

```bash
# Check logs for queue errors
sudo journalctl -u rpi-agent.service | grep -i "queue\|command"

# Restart to clear
sudo systemctl restart rpi-agent.service
```

---

## 🔍 Diagnostic Tools

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
top              # CPU
vcgencmd measure_temp  # Temperature (RPI only)
```

### Windows Scripts

```batch
# Health check (comprehensive)
scripts\rpi_health_check.bat

# Service restart
scripts\rpi_restart_service.bat

# Debug session
scripts\rpi_connect_debug.bat  (if exists)
```

### Database Diagnostics

```bash
cd ~/rpi_ai/rpi_ai

# Check integrity
sqlite3 agent_memory.db "PRAGMA integrity_check;"

# Count memories
sqlite3 agent_memory.db "SELECT COUNT(*) FROM memories;"

# Check size
sqlite3 agent_memory.db "SELECT 
    COUNT(*) as count,
    SUM(LENGTH(content)) as total_size
FROM memories;"
```

---

## 🚑 Emergency Procedures

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

## 🔗 Related Documentation

- [Deployment Guide](deployment-guide.md) - Setup and configuration
- [Batch Scripts Reference](batch-scripts-reference.md) - Windows maintenance tools
- [Resource Manager](../core/resource-manager.md) - Resource tier system
- [Memory System](../core/memory-system.md) - Database internals
- [LLM Integration](../core/llm-integration.md) - LLM troubleshooting

---

## 💡 Tips & Best Practices

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

### Quick Recovery Steps

1. **Check !status in Discord** - Fastest diagnostic
2. **Run health check** - Comprehensive view
3. **Check logs** - Identify root cause
4. **Try restart** - Fixes 80% of issues
5. **Restore backup** - If data corruption

### Log Analysis

```bash
# Common patterns to grep for:
sudo journalctl -u rpi-agent.service | grep -i "error"
sudo journalctl -u rpi-agent.service | grep -i "exception"
sudo journalctl -u rpi-agent.service | grep -i "failed"
sudo journalctl -u rpi-agent.service | grep -i "warning"
```

---

**Last Updated:** 2025-12-03  
**Version:** 1.1.0  
**Covers:** All major subsystems and common issues
