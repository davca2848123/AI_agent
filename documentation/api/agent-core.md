# 🧠 Agent Core API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Agent Core](agent-core.md) | [🔍 Hledat](../INDEX.md#vyhledavani)

Dokumentace pro třídu `AutonomousAgent` v `agent/core.py`.

<a name="přehled"></a>
## 📋 Přehled

`AutonomousAgent` je hlavní třída řídící celý životní cyklus agenta. Spravuje smyčky chování, inicializaci subsystémů a zpracování chyb.

<a name="třída-autonomousagent"></a>
## 🔧 Třída AutonomousAgent

```python
class AutonomousAgent:
    def __init__(self, discord_token: str = None)
```

<a name="hlavní-metody"></a>
### Hlavní Metody

<a name="startself"></a>
#### `start(self)`
Spustí hlavní smyčky agenta (`observation_loop`, `boredom_loop`, `backup_loop`, atd.) a Discord klienta.

<a name="graceful_shutdownself-timeout-int-10"></a>
#### `graceful_shutdown(self, timeout: int = 10)`
Bezpečně ukončí všechny běžící procesy a uloží stav agenta.

<a name="observation_loopself"></a>
#### `observation_loop(self)`
Hlavní smyčka pro sběr dat ze senzorů (Discord aktivity, systémové zdroje) a jejich zpracování.

<a name="boredom_loopself"></a>
#### `boredom_loop(self)`
Simuluje plynutí času a nárůst nudy. Pokud nuda překročí práh, spustí autonomní akci.

<a name="execute_actionself-action-str"></a>
#### `execute_action(self, action: str)`
Vykoná akci rozhodnutou LLM.
- **action**: Textový popis akce nebo tool call.

<a name="report_errorself-error-exception"></a>
#### `report_error(self, error: Exception)`
Ohlásí kritickou chybu administrátorovi přes Discord DM.

<a name="stav-agenta"></a>
### Stav Agenta

<a name="_save_agent_stateself"></a>
#### `_save_agent_state(self)`
Uloží aktuální stav (úroveň nudy, poslední DM ID) do `agent_state.json`.

<a name="_load_agent_stateself"></a>
#### `_load_agent_state(self)`
Načte uložený stav při startu.

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
