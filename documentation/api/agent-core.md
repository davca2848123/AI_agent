# 🧠 Agent Core API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Agent Core](agent-core.md)

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

<a name="trigger_autonomous_actionself"></a>
#### `trigger_autonomous_action(self)`
Spustí proces autonomního rozhodování.
1. Sestaví kontext (nuda, cíle).
2. Dotáže se LLM (`decide_action`).
3. Provede tool call NEBO zavolá `execute_action` pro textovou akci.

<a name="execute_actionself-action-str"></a>
#### `execute_action(self, action: str)`
Vykoná textovou akci (pokud LLM nezvolilo žádný nástroj), např. odeslání reportu.
- **action**: Textový popis akce.

<a name="report_errorself-error-exception"></a>
#### `report_error(self, error: Exception)`
Ohlásí kritickou chybu administrátorovi přes Discord DM.

<a name="add_filtered_memoryself-content-str-metadata-dict-none"></a>
#### `add_filtered_memory(self, content: str, metadata: dict = None)`
Inteligentní přidání vzpomínky.
1. Použije LLM k extrakci pouze faktických informací (odstraní "fluff").
2. Uloží vyčištěnou informaci do paměti pomocí `self.memory.add_memory`.
- **content**: Surový text (např. celý obsah webové stránky).
- **metadata**: Metadata (např. `type`, `source`).

<a name="_process_activityself-activity_data-dict"></a>
#### `_process_activity(self, activity_data: dict)`
Zpracuje detekovanou Discord aktivitu uživatele.
- Pokud je aktivita neznámá, provede web search (`WebTool`).
- Uloží shrnutí aktivity do paměti (`activity_knowledge`).

<a name="stav-agenta"></a>
### Stav Agenta

<a name="_save_agent_stateself"></a>
#### `_save_agent_state(self)`
Uloží aktuální stav (úroveň nudy, poslední DM ID) do `agent_state.json`.

<a name="_load_agent_stateself"></a>
#### `_load_agent_state(self)`
Načte uložený stav při startu.


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🧠 Core Documentation](../core/)
- [📂 Source Code](../agent/)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
