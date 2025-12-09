# ⚙️ Configuration Guide

> **Navigace:** [📂 Dokumentace](../README.md) | [⚙️ Konfigurace](../README.md#konfigurace) | [Configuration Guide](complete-configuration-guide.md)

> Kompletní průvodce konfigurací RPI AI Agenta.
> **Verze:** Beta - CLOSED

---

<a name="obsah"></a>
## 📋 Obsah

1. [config_settings.py](#config_settingspy)
2. [config_secrets.py](#config_secretspy)
3. [Environment Variables](#environment-variables)
4. [LLM Configuration](#llm-configuration)
5. [Memory Configuration](#memory-configuration)
6. [Resource Manager](#resource-manager-configuration)
7. [Discord Configuration](#discord-configuration)
8. [Advanced Settings](#advanced-settings)

---

<a name="config-settings"></a>

<a name="config_settingspy"></a>
## 🔧 config_settings.py

<a name="hlavní-nastavení"></a>
### Hlavní Nastavení

```python
# config_settings.py

# === ADMIN CONFIGURATION ===
ADMIN_USER_IDS = [
    123456789012345678  # Tvoje Discord User ID
]

# === LLM CONFIGURATION ===
LLM_CONTEXT_NORMAL = 1024      # Normal tier context window
LLM_CONTEXT_TIER1 = 768        # Tier 1 (85% RAM usage)
LLM_CONTEXT_TIER2 = 512        # Tier 2 (90% RAM usage)
LLM_CONTEXT_TIER3 = 256        # Tier 3 (95% RAM usage)

MODEL_CACHE_DIR = "./models/"  # Where to store LLM model

# === MEMORY CONFIGURATION ===
MEMORY_CONFIG = {
    # Scoring thresholds
    'MIN_SCORE_TO_SAVE': 70,           # Minimum score to save memory
    'ERROR_PENALTY': -20,               # Points lost for error detection
    'KEYWORD_BONUS': 10,                # Points per keyword match
    'UNIQUENESS_BONUS': 30,             # Points if content is unique
    'UNIQUENESS_THRESHOLD': 0.90,       # 90% similarity = not unique
    
    # Keywords (important terms)
    'KEYWORDS': [
        'python', 'discord', 'tool', 'learned', 'user',
        'command', 'function', 'error', 'fix', 'create',
        'deploy', 'install', 'configure', 'system', 'agent'
    ],
    
    # Blacklist (auto-reject)
    'BLACKLIST': [
        'discord.gateway',
        'discord.client',
        'Keep Alive',
        'WebSocket',
        'Heartbeat',
        'gateway event'
    ]
}

# === RESOURCE MANAGER ===
RESOURCE_CHECK_INTERVAL = 60   # Seconds between resource checks

# RAM thresholds (percentage)
RAM_TIER1_THRESHOLD = 85
RAM_TIER2_THRESHOLD = 90
RAM_TIER3_THRESHOLD = 95

# === BOREDOM SYSTEM ===
BOREDOM_INCREASE_RATE = 0.5    # % per minute when idle
BOREDOM_THRESHOLD_ACTION = 70  # Start autonomous actions at 70%
MESSAGE_BOREDOM_REDUCTION = 0.1  # Reduce 10% on message

# === LOGGING ===
LOG_LEVEL = "INFO"             # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "agent.log"
LOG_MAX_SIZE_MB = 50          # Max log file size before rotation

# === DISCORD ===
COMMAND_PREFIX = "!"
FUZZY_MATCH_THRESHOLD = 2     # Max edit distance for auto-correction

# === PATHS ===
WORKSPACE_DIR = "."           # FileTool workspace
BACKUP_DIR = "./backup/"      # Database backups
```

<a name="získání-discord-user-id"></a>
### Získání Discord User ID

**Metoda 1: Discord Settings**
1. Discord → Settings (⚙️)
2. Advanced → Developer Mode: **ON**
3. Right-click yourself → **Copy ID**

**Metoda 2: Z agenta**
```
!debug quick
```
Najdi sekci "User Info"

---

<a name="config-secrets"></a>

<a name="config_secretspy"></a>
## 🔐 config_secrets.py

<a name="template"></a>
### Template

```python
# config_secrets.py
# ⚠️ NIKDY NECOMMITUJ DO GITU!

# === DISCORD BOT TOKEN ===
DISCORD_BOT_TOKEN = "MTxxxxxxxxxxxxxxxxx.xxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxx"
#                     ↑ Musí začínat "MT"
#                     Získej z: https://discord.com/developers/applications

# === ADMIN USER IDS ===
ADMIN_USER_IDS = [
    123456789012345678  # Tvoje Discord User ID
]

# === NGROK (Optional) ===
NGROK_AUTH_TOKEN = "your_ngrok_token_here"
# Získej z: https://dashboard.ngrok.com/get-started/your-authtoken

# === API KEYS (Optional) ===
# Add any future API keys here
```

<a name="získání-discord-bot-tokenu"></a>
### Získání Discord Bot Tokenu

1. **Jdi na:** https://discord.com/developers/applications
2. **Vytvoř aplikaci:** "New Application"
3. **Bot tab:** Add Bot
4. **Token:** Reset Token → **Copy**
5. **Intents:** ZAPNI všechny:
   - ✅ **MESSAGE CONTENT INTENT** (CRITICAL!)
   - ✅ Presence Intent
   - ✅ Server Members Intent
6. **OAuth2:** Generate invite URL s permissions:
   - `bot`
   - `applications.commands`
   - Permissions: `Send Messages`, `Read Messages`, `Embed Links`, `Attach Files`

<a name="security-best-practices"></a>
### Security Best Practices

```bash
# .gitignore MUST contain:
config_secrets.py
*.db
agent.log
```

**Template file:**
```bash
# Vytvoř template (bez secrets)
cp config_secrets.py config_secrets.py.example

# V .example nahraď tokeny za placeholder:
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

---

<a name="environment-variables"></a>
## 🌍 Environment Variables

<a name="systémové-proměnné"></a>
### Systémové Proměnné

```bash
# Optional - pokud chceš overridovat config_settings.py

# LLM
export MODEL_CACHE_DIR="/custom/path/models"
export LLM_CONTEXT_NORMAL=2048

# Logging
export LOG_LEVEL="DEBUG"
export LOG_FILE="custom_agent.log"

# Resource Management
export RAM_TIER1_THRESHOLD=80
```

<a name="v-systemd-service"></a>
### V Systemd Service

```ini
# /etc/systemd/system/rpi-agent.service

[Service]
Environment="MODEL_CACHE_DIR=/home/davca/models"
Environment="LOG_LEVEL=INFO"
```

---

<a name="llm-configuration"></a>
## 🧠 LLM Configuration

<a name="model-selection"></a>
### Model Selection

```python
# agent/llm.py

class LLMClient:
    def __init__(
        self,
        model_repo="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        model_filename="qwen2.5-0.5b-instruct-q4_k_m.gguf"
    ):
```

**Změna modelu:**

1. **Najdi model:** https://huggingface.co/models?library=gguf
2. **Uprav:** `agent/llm.py` constructor
3. **Smaž starý:** `rm models/*.gguf`
4. **Restart:** Agent automaticky stáhne nový

<a name="context-window-tuning"></a>
### Context Window Tuning

```python
# config_settings.py

# Pro více RAM (snižší rychlost):
LLM_CONTEXT_NORMAL = 2048   # Vyšší context = více paměti

# Pro méně RAM (rychlejší):
LLM_CONTEXT_NORMAL = 512    # Nižší context = méně paměti
```

**Dopad:**
- **2048 tokens:** ~1.5 GB RAM, ~500ms latence
- **1024 tokens:** ~800 MB RAM, ~250ms latence
- **512 tokens:** ~400 MB RAM, ~150ms latence

<a name="thread-configuration"></a>
### Thread Configuration

```python
# agent/llm.py - _load_model()

# Auto-detect (default):
n_threads = max(2, psutil.cpu_count(logical=False) // 2)

# Manual override:
n_threads = 4  # Use 4 CPU threads
```

---

<a name="memory-configuration"></a>
## 💾 Memory Configuration

<a name="scoring-parameters"></a>
### Scoring Parameters

```python
# config_settings.py

MEMORY_CONFIG = {
    'MIN_SCORE_TO_SAVE': 70,  # Lower = save more (e.g., 50)
                               # Higher = save less (e.g., 90)
}
```

**Příklady:**

| Setting | Effect | Use Case |
|---------|--------|----------|
| `MIN_SCORE: 50` | Uloží více vzpomínek | Testing, learning |
| `MIN_SCORE: 70` | Balanced | **Production** |
| `MIN_SCORE: 90` | Jen vysoká kvalita | Low storage |

<a name="keyword-customization"></a>
### Keyword Customization

```python
MEMORY_CONFIG = {
    'KEYWORDS': [
        # Add your domain-specific keywords
        'minecraft',
        'game',
        'server',
        'plugin'
    ]
}
```

<a name="blacklist-expansion"></a>
### Blacklist Expansion

```python
MEMORY_CONFIG = {
    'BLACKLIST': [
        'discord.gateway',  # Default
        'typing indicator', # Add custom
        'presence update',
        'your_custom_spam'
    ]
}
```

---

<a name="resource-manager-configuration"></a>
## 📊 Resource Manager Configuration

<a name="ram-tiers"></a>
### RAM Tiers

```python
# config_settings.py

# Tier 1: Moderate reduction
RAM_TIER1_THRESHOLD = 85  # When RAM > 85%
LLM_CONTEXT_TIER1 = 768   # Reduce context to 768

# Tier 2: Significant reduction  
RAM_TIER2_THRESHOLD = 90
LLM_CONTEXT_TIER2 = 512

# Tier 3: Minimal (emergency)
RAM_TIER3_THRESHOLD = 95
LLM_CONTEXT_TIER3 = 256
```

**Flow:**
```
RAM 84% → Normal (1024 tokens)
RAM 86% → Tier 1 (768 tokens)  
RAM 91% → Tier 2 (512 tokens)
RAM 96% → Tier 3 (256 tokens)
```

<a name="check-interval"></a>
### Check Interval

```python
RESOURCE_CHECK_INTERVAL = 60  # Check every 60 seconds

# More frequent (higher load):
RESOURCE_CHECK_INTERVAL = 30

# Less frequent (lower overhead):
RESOURCE_CHECK_INTERVAL = 120
```

---

<a name="discord-configuration"></a>
## 💬 Discord Configuration

<a name="command-prefix"></a>
### Command Prefix

```python
# config_settings.py

COMMAND_PREFIX = "!"  # Default

# Change to:
COMMAND_PREFIX = "?"  # ?help, ?status
COMMAND_PREFIX = "."  # .help, .status
```

<a name="fuzzy-matching"></a>
### Fuzzy Matching

```python
FUZZY_MATCH_THRESHOLD = 2  # Max 2 character difference

# More lenient:
FUZZY_MATCH_THRESHOLD = 3  # !statusss → !status (3 chars)

# Stricter:
FUZZY_MATCH_THRESHOLD = 1  # Only 1 char typos
```

<a name="activity-status"></a>
### Activity Status

```python
# agent/core.py - DiscordClient.set_activity()

# Custom status:
await client.change_presence(
    activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="!help for commands"  # ← Customize here
    )
)
```

**Activity Types:**
- `playing` → "Playing ..."
- `watching` → "Watching ..."
- `listening` → "Listening to ..."
- `streaming` → "Streaming ..."

---

<a name="boredom-system-configuration"></a>
## 🤖 Boredom System Configuration

<a name="rates-thresholds"></a>
### Rates & Thresholds

```python
# config_settings.py

BOREDOM_INCREASE_RATE = 0.5     # +0.5% per minute idle
BOREDOM_THRESHOLD_ACTION = 70   # Start actions at 70%
MESSAGE_BOREDOM_REDUCTION = 0.1 # -10% on message

# Examples:

# More active agent:
BOREDOM_INCREASE_RATE = 1.0     # Rychlejší nuda
BOREDOM_THRESHOLD_ACTION = 50   # Akce dříve

# More passive agent:
BOREDOM_INCREASE_RATE = 0.2     # Pomalejší nuda
BOREDOM_THRESHOLD_ACTION = 90   # Akce později
```

<a name="action-frequency"></a>
### Action Frequency

```python
# agent/core.py - boredom_loop()

await asyncio.sleep(60)  # Check every 60s

# More frequent:
await asyncio.sleep(30)  # Check every 30s

# Less frequent:
await asyncio.sleep(120) # Check every 2min
```

---

<a name="advanced-settings"></a>
## 🔍 Advanced Settings

<a name="database-optimization"></a>
### Database Optimization

```python
# agent/memory.py - VectorStore._initialize_db()

self.conn.execute("PRAGMA journal_mode=WAL")
self.conn.execute("PRAGMA synchronous=NORMAL")  # NORMAL | FULL
self.conn.execute("PRAGMA cache_size=10000")    # 10MB cache
self.conn.execute("PRAGMA temp_store=MEMORY")
```

**Tuning:**

```python
# More performance (less safety):
PRAGMA synchronous=NORMAL
PRAGMA cache_size=20000  # 20MB

# More safety (less performance):
PRAGMA synchronous=FULL
PRAGMA cache_size=5000   # 5MB
```

<a name="command-queue"></a>
### Command Queue

```python
# agent/commands.py - CommandHandler.__init__()

self.queue = asyncio.Queue(maxsize=100)  # Max 100 queued commands

# Larger queue:
maxsize=200

# Smaller queue:
maxsize=50
```

<a name="logging-verbosity"></a>
### Logging Verbosity

```python
# config_settings.py

LOG_LEVEL = "INFO"  # Standard

# Debug mode (verbose):
LOG_LEVEL = "DEBUG"  # Shows everything

# Production (quiet):
LOG_LEVEL = "WARNING"  # Only warnings/errors
```

---

<a name="file-structure"></a>
## 📁 File Structure

```
rpi_ai/rpi_ai/
├── config_settings.py      ← Main configuration
├── config_secrets.py        ← Tokens & secrets (gitignored)
├── config_secrets.py.example ← Template
├── agent/
│   ├── core.py             ← Boredom, observation loops
│   ├── llm.py              ← LLM parameters
│   ├── memory.py           ← Memory scoring
│   ├── commands.py         ← Command prefix, fuzzy matching
│   └── tools.py            ← Tool settings
└── models/                  ← LLM model cache
```

---

<a name="common-customizations"></a>
## 🎯 Common Customizations

<a name="1-change-admin"></a>
### 1. Change Admin

```python
# config_secrets.py
ADMIN_USER_IDS = [
    999888777666555444  # New admin ID
]
```

<a name="2-reduce-memory-usage"></a>
### 2. Reduce Memory Usage

```python
# config_settings.py
LLM_CONTEXT_NORMAL = 512  # Lower context
RAM_TIER1_THRESHOLD = 80  # Earlier resource reduction
```

<a name="3-more-selective-memory"></a>
### 3. More Selective Memory

```python
MEMORY_CONFIG = {
    'MIN_SCORE_TO_SAVE': 90,  # Save only high-quality
}
```

<a name="4-faster-responses"></a>
### 4. Faster Responses

```python
# agent/llm.py
self.current_max_tokens = 64  # Instead of 128
```

<a name="5-custom-command-prefix"></a>
### 5. Custom Command Prefix

```python
COMMAND_PREFIX = "$"  # $help, $status, $ask
```

---

<a name="applying-changes"></a>
## 🔄 Applying Changes

<a name="option-1-restart-service"></a>
### Option 1: Restart Service

```bash
sudo systemctl restart rpi-agent.service
```

<a name="option-2-manual-restart"></a>
### Option 2: Manual Restart

```bash
# Stop
sudo systemctl stop rpi-agent.service

# Start manually (see logs)
cd ~/rpi_ai/rpi_ai
python3 main.py

# Ctrl+C to stop
# Then restart service:
sudo systemctl start rpi-agent.service
```

<a name="option-3-from-discord-admin"></a>
### Option 3: From Discord (Admin)

```
!restart
```

---

<a name="configuration-validation"></a>
## 🆘 Configuration Validation

<a name="check-syntax"></a>
### Check Syntax

```bash
# Validate Python syntax
python3 -c "import config_settings; print('OK')"
python3 -c "import config_secrets; print('OK')"
```

<a name="test-discord-token"></a>
### Test Discord Token

```python
import discord

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await client.close()

# Run (should connect):
client.run("YOUR_TOKEN_HERE")
```

<a name="verify-intents"></a>
### Verify Intents

```bash
# Should NOT error:
python3 -c "
import discord
intents = discord.Intents.default()
intents.message_content = True
print('Intents OK')
"
```

---

<a name="environment-specific-configs"></a>
## 📝 Environment-Specific Configs

<a name="development"></a>
### Development

```python
# config_settings_dev.py
LOG_LEVEL = "DEBUG"
BOREDOM_INCREASE_RATE = 5.0  # Fast boredom for testing
MIN_SCORE_TO_SAVE = 30       # Save everything
```

<a name="production"></a>
### Production

```python
# config_settings_prod.py
LOG_LEVEL = "INFO"
BOREDOM_INCREASE_RATE = 0.5
MIN_SCORE_TO_SAVE = 70
```

**Switching:**
```bash
# Symlink to active config
ln -sf config_settings_prod.py config_settings.py
```

---

<a name="související"></a>
## 🔗 Související

- [📖 Deployment Guide](../scripts/deployment-guide.md) - Initial setup
- [🆘 Troubleshooting](../troubleshooting.md) - Common config issues
- [📖 Memory System](../core/memory-system.md) - Memory scoring details
- [📖 Resource Manager](../core/resource-manager.md) - Tier system
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
