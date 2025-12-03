# 🤖 Autonomous AI Agent - Project Context

> **CRITICAL WARNING**: ⚠️ **NEVER RUN `main.py` SCRIPT** ⚠️
> 
> This is a live Discord bot agent running on a Raspberry Pi. Running `main.py` would:
> - Start a duplicate instance of the bot
> - Cause conflicts with the production instance
> - Potentially corrupt the database or cause race conditions
> 
> **For AI Assistants**: You may create test scripts in the `tests/` directory, but NEVER execute `main.py` or any production scripts.

---

## 📋 Project Overview

This is an **Autonomous Embedded AI Agent** designed to run on Raspberry Pi hardware with Discord integration. The agent operates autonomously, responding to commands, managing its own memory, and performing various tasks through an extensive toolkit.

### Platform
- **Target**: Raspberry Pi 4B (Debian/Linux)
- **Development**: Windows prototype environment
- **Runtime**: Async Python with Discord.py

---

## 🏗️ Project Structure

```
rpi_ai/
├── main.py                 # 🚫 MAIN ENTRY POINT - DO NOT RUN
├── config_secrets.py       # Discord token and sensitive data
├── config_settings.py      # Agent configuration
├── requirements.txt        # Python dependencies
│
├── agent/                  # Core agent modules
│   ├── core.py            # Main agent logic and lifecycle
│   ├── commands.py        # Discord command handlers (~100KB)
│   ├── discord_client.py  # Discord integration
│   ├── llm.py             # Local LLM integration (llama-cpp)
│   ├── memory.py          # SQLite memory system
│   ├── tools.py           # Agent toolkit (weather, math, etc.)
│   ├── resource_manager.py # System resource monitoring
│   └── hardware.py        # Hardware interface
│
├── models/                # LLM model files
├── scripts/               # Utility and task scripts
├── tests/                 # Test scripts (safe to create/modify)
├── workspace/             # Agent workspace
└── backup/                # Backups

Database files:
├── agent_memory.db        # Active memory database
├── agent_memory.db-shm    # Shared memory
└── agent_memory.db-wal    # Write-ahead log
```

---

## 🔧 Core Components

### 1. **Agent Core** (`agent/core.py`)
- Main autonomous agent class
- Event loops (observation, boredom, resource monitoring)
- Lifecycle management (startup, shutdown)
- Admin notifications via Discord DM

### 2. **Discord Integration** (`agent/discord_client.py`, `agent/commands.py`)
- Discord bot client
- Extensive command system with `!` prefix
- Admin DM categorization system
- Message tracking and editing

### 3. **LLM Integration** (`agent/llm.py`)
- Local llama-cpp-python integration
- Context management
- Fallback mechanisms when LLM unavailable
- Memory-based response generation

### 4. **Memory System** (`agent/memory.py`)
- SQLite database for persistent storage
- Context-aware memory retrieval
- Relevance scoring and semantic search
- Memory pruning and optimization

### 5. **Toolkit** (`agent/tools.py`)
- Weather API
- Math evaluation
- Translation (deep-translator)
- Wikipedia integration
- Web search (DuckDuckGo)
- Time/timezone
- File operations
- System commands
- Database queries
- RSS feeds
- Git operations
- Code analysis

### 6. **Resource Manager** (`agent/resource_manager.py`)
- CPU, memory, disk monitoring
- Temperature sensors (for RPi)
- Network statistics
- Process management

---

## 💾 Key Files

### Configuration
- **`config_secrets.py`**: Discord bot token, API keys
- **`config_settings.py`**: Agent behavior settings, intervals, thresholds

### Database
- **`agent_memory.db`**: Main SQLite database
  - Tables: `conversations`, `facts`, `skills`, `goals`, `observations`
  - Semantic memory storage
  - Full-text search capability

### Logs
- **`agent.log`**: Comprehensive logging (can be large ~1.8MB)
  - Timestamped events
  - Multi-level logging (DEBUG, INFO, WARNING, ERROR)

---

## 🎯 Main Features

### Discord Commands (prefix: `!`)
Key commands include:
- `!ask <question>` - Query with LLM and tool orchestration
- `!debug` - System verification and diagnostics
- `!live logs [duration]` - Live log viewing
- `!status` - Agent status and health
- `!memory <action>` - Memory management
- `!tools` - Available tools list
- `!git <action>` - Git operations
- `!database <query>` - SQL queries
- `!weather <location>` - Weather information
- `!translate <text>` - Translation
- `!wiki <query>` - Wikipedia search
- Many more in `commands.py`

### Autonomous Behaviors
- **Observation Loop**: Monitors environment every 5 seconds
- **Boredom System**: Generates autonomous actions when idle
- **Resource Monitoring**: Tracks system health
- **Memory Formation**: Stores conversations and observations

---

## 🔄 Development Workflow

### Adding Features
1. Modify relevant module in `agent/` directory
2. Create test scripts in `tests/` directory (safe zone)
3. **NEVER** run `main.py` during development
4. Use test scripts to validate functionality

### Testing
- Create scripts in `tests/` directory
- Use isolated test functions
- Mock Discord client if needed
- Test database operations with separate test DB

### Script Organization
- Production scripts: `scripts/` (e.g., `fix_llm.py`, `ACTION_*.bat`)
- Test scripts: `tests/` (temporary, safe to modify)

---

## ⚙️ Dependencies

Key Python packages:
```
discord.py          # Discord API
llama-cpp-python    # Local LLM
psutil              # System monitoring
aiohttp             # Async HTTP
duckduckgo-search   # Web search
beautifulsoup4      # HTML parsing
feedparser          # RSS feeds
deep-translator     # Translation
wikipedia-api       # Wikipedia
GitPython           # Git operations
numpy               # Numerical operations
```

---

## 🚨 Important Guidelines for AI Assistants

### ✅ ALLOWED
- View and analyze any project files
- Create/modify files in `tests/` directory
- Suggest code improvements
- Create documentation
- Analyze logs and database structure
- Create utility scripts for later manual execution

### ❌ NEVER DO
- **Run `main.py`** - This starts the production bot
- **Run any production scripts** without explicit permission
- **Modify database directly** during bot operation
- **Delete critical files** (config, database, main.py)
- **Execute commands that interact with Discord API** (would duplicate bot)

### 📝 When Creating Scripts
- Save test scripts to `tests/` directory
- Add clear comments and documentation
- Include error handling
- Make scripts standalone and safe
- Indicate if manual execution required

---

## 🔍 Quick Reference

### Current State
- Bot is **RUNNING** on Raspberry Pi
- Database is **ACTIVE** (notice .db-shm and .db-wal files)
- Discord connection is **LIVE**
- Logs are being written continuously

### Important Directories
- `tests/` - Safe zone for development and testing
- `scripts/` - Production utility scripts
- `agent/` - Core bot logic (modify with care)
- `models/` - LLM model files
- `workspace/` - Agent's working directory

### Key Metrics
- Commands file: ~100KB (extensive command system)
- Core logic: ~46KB (main agent brain)
- Memory system: ~16KB (database interface)
- Log file: ~1.8MB (active logging)

---

## 📚 Additional Context

### Recent Optimizations
- Observation loop: 5 second intervals (CPU optimization)
- Boredom loop: 60 second intervals
- Message reception: Reduces boredom by 0.1 (minimal reduction)
- LLM context: Optimized with top-5 relevant memories
- Admin DM: Categorized message system

### Memory Architecture
- **Conversations**: User interactions, Discord messages
- **Facts**: Learned information, stored knowledge
- **Skills**: Agent capabilities and learnings
- **Goals**: Short/long-term objectives
- **Observations**: Environmental data and logs

### Fallback Mechanisms
- LLM unavailable → Use memory-based responses
- Memory search fails → Web search
- Web search fails → Apologetic response
- Tool unavailable → Graceful degradation

---

**Last Updated**: 2025-11-30
**Project Version**: RPi 4B, 2GB ram
**Status**: Active Development & Testing
