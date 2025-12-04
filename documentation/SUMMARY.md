# 📋 API Tasklist & Reference

> **Navigace:** [📂 Dokumentace](README.md) | [📄 Přehled (OVERVIEW)](OVERVIEW.md) | [🔍 Index (INDEX)](INDEX.md) | [📋 API Tasklist (SUMMARY)](SUMMARY.md) | [🏗️ Architektura](architecture.md) | [🆘 Troubleshooting](troubleshooting.md) | [🔍 Hledat](INDEX.md#vyhledavani)

> Kompletní checklist implementovaných funkcí, příkazů a API.
> **Verze:** Alpha

---

<a name="agent-core-api"></a>
## 🤖 Agent Core API

<a name="autonomousagentapiagent-coremd-agentcorepy"></a>
### [`AutonomousAgent`](api/agent-core.md) (agent/core.py)
- [x] `__init__(self)` - Inicializace agenta
- [x] `start(self)` - Spuštění hlavní smyčky
- [x] `stop(self)` - Bezpečné ukončení
- [x] `_observation_loop(self)` - Hlavní smyčka pozorování
- [x] `_boredom_loop(self)` - Smyčka pro zvyšování nudy
- [x] `_cleanup_old_tests(self)` - Údržba dočasných souborů
- [x] `handle_autonomous_action(self)` - Vykonání autonomní akce
- [x] `reduce_boredom(self, amount)` - Snížení úrovně nudy

<a name="memorysystemapimemory-systemmd-agentmemorypy"></a>
### [`MemorySystem`](api/memory-system.md) (agent/memory.py)
- [x] `__init__(self, db_path)` - Připojení k SQLite
- [x] `save_interaction(self, user_input, response)` - Uložení konverzace
- [x] `save_action(self, action_type, details)` - Uložení akce
- [x] `get_recent_memories(self, limit)` - Získání kontextu
- [x] `search_memories(self, query)` - FTS5 vyhledávání
- [x] `backup_database(self)` - Vytvoření zálohy

<a name="llmclientapillm-integrationmd-agentllmpy"></a>
### [`LLMClient`](api/llm-integration.md) (agent/llm.py)
- [x] `__init__(self)` - Načtení modelu (llama-cpp)
- [x] `generate_response(self, prompt, system_prompt)` - Generování textu
- [x] `_parse_tool_calls(self, response)` - Detekce volání nástrojů
- [x] `check_availability(self)` - Ping test modelu

<a name="discordclientapidiscord-clientmd-agentdiscord_clientpy"></a>
### [`DiscordClient`](api/discord-client.md) (agent/discord_client.py)
- [x] `__init__(self, token, channel_id)` - Setup klienta
- [x] `start(self)` - Připojení k Gateway
- [x] `send_message(self, channel_id, content)` - Odeslání zprávy
- [x] `update_status(self, status)` - Změna aktivity bota
- [x] `on_message(self, message)` - Event handler

---

<a name="commands-api"></a>
## 💬 Commands API

<a name="basic-commands"></a>
### Basic Commands
- [x] `!help` - Zobrazení nápovědy
- [x] `!status` - Diagnostika systému
- [x] `!stats` - Statistiky agenta
- [x] `!intelligence` - Metriky inteligence
- [x] `!documentation` - Interaktivní dokumentace

<a name="tools-learning"></a>
### Tools & Learning
- [x] `!tools` - Seznam dostupných nástrojů
- [x] `!learn [tool]` - Učení se novým nástrojům
- [x] `!ask [query]` - Dotaz na AI (s kontextem)
- [x] `!teach [content]` - Přímé vkládání do paměti
- [x] `!search [query]` - Webové vyhledávání

<a name="data-management"></a>
### Data Management
- [x] `!memory [dump]` - Statistiky databáze
- [x] `!logs [count]` - Zobrazení logů
- [x] `!live logs` - Real-time stream logů
- [x] `!export [type]` - Export dat (JSON/CSV)

<a name="interaction"></a>
### Interaction
- [x] `!mood` - Zobrazení interního stavu
- [x] `!goals` - Správa cílů agenta
- [x] `!config` - Zobrazení konfigurace

<a name="administration"></a>
### Administration
- [x] `!restart` - Restart procesu agenta
- [x] `!monitor` - Sledování zdrojů (CPU/RAM)
- [x] `!ssh` - Správa SSH tunelu
- [x] `!cmd` - Vykonání shell příkazu
- [x] `!debug` - Hloubková diagnostika
- [x] `!report` - Generování reportů
- [x] `!topic` - Správa témat
- [x] `!web` - Web interface management
- [x] `!upload` - GitHub release upload

---

<a name="tools-apiapitools-apimd"></a>
## 🛠️ [Tools API](api/tools-api.md)

<a name="system-tools"></a>
### System Tools
- [x] `FileTool` - `read_file`, `write_file`, `list_dir`
- [x] `SystemTool` - `get_system_info`, `get_process_list`
- [x] `TimeTool` - `get_current_time`, `get_date`
- [x] `CodeTool` - `execute_python`

<a name="knowledge-tools"></a>
### Knowledge Tools
- [x] `WebTool` - `search`, `read_page`
- [x] `WikipediaTool` - `search`, `summary`
- [x] `RSSTool` - `read_feed`
- [x] `DatabaseTool` - `execute_query`

<a name="utility-tools"></a>
### Utility Tools
- [x] `MathTool` - `calculate`, `convert_units`
- [x] `WeatherTool` - `get_weather`
- [x] `TranslateTool` - `translate_text`
- [x] `NoteTool` - `add_note`, `read_notes`
- [x] `GitTool` - `status`, `log`
- [x] `DiscordActivityTool` - `get_activities`

---

<a name="data-structures"></a>
## 📊 Data Structures

<a name="memory-schema-sqlite"></a>
### Memory Schema (SQLite)
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    type TEXT,          -- 'interaction', 'action', 'observation'
    content TEXT,       -- Hlavní obsah
    metadata TEXT,      -- JSON metadata
    embedding BLOB      -- Vector embedding (volitelné)
);

CREATE VIRTUAL TABLE memories_fts USING fts5(content);
```

<a name="agent-state"></a>
### Agent State
```python
class AgentState:
    boredom: float      # 0.0 - 1.0
    current_task: str   # Popis aktuální činnosti
    mood: str           # 'neutral', 'curious', 'bored'
    last_action: float  # Timestamp
```

    last_action: float  # Timestamp
```

---

<a name="configuration"></a>
## ⚙️ Configuration

- [x] `complete-configuration-guide.md` - Master guide
- [x] `config_settings_reference.md` - Settings reference
- [x] `environment_variables.md` - .env reference
- [x] `config_secrets_template.md` - Secrets template
- [x] `customization-guide.md` - Customization guide

<a name="scripts-advanced"></a>
## 📜 Scripts & Advanced

- [x] `deployment-guide.md` - Deployment instructions
- [x] `maintenance.md` - Maintenance tasks
- [x] `batch-scripts-reference.md` - Batch scripts
- [x] `fuzzy-matching-algorithm.md` - Search algorithm details

---

Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
