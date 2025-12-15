# 🔧 config_settings.py Reference

> **Navigace:** [📂 Dokumentace](../README.md) | [⚙️ Konfigurace](../README.md#konfigurace) | [config_settings.py Reference](config_settings_reference.md)

> Detailní popis všech konfiguračních možností v souboru `config_settings.py`.
> **Verze:** Beta - CLOSED

---

<a name="umístění"></a>
## 📂 Umístění
Soubor se nachází v kořenovém adresáři projektu: `config_settings.py`

---

<a name="core-settings"></a>

<a name="core-settings-základní-nastavení"></a>
## 🔧 Core Settings (Základní Nastavení)

<a name="admin_user_ids"></a>
### `ADMIN_USER_IDS`
Seznam Discord ID uživatelů, kteří mají administrátorská práva (přístup k `!cmd`, `!restart`, `!debug` atd.).
```python
ADMIN_USER_IDS = [512658574875557889]
```

<a name="model_cache_dir"></a>
### `MODEL_CACHE_DIR`
Adresář pro ukládání stažených AI modelů (HuggingFace cache).
```python
MODEL_CACHE_DIR = "./models/"
```

---

<a name="location-settings"></a>

<a name="location-settings-lokace"></a>
## 🌍 Location Settings (Lokace)

<a name="default_location"></a>
### `DEFAULT_LOCATION`
Výchozí lokace pro nástroje jako počasí (`WeatherTool`) nebo čas (`TimeTool`), pokud uživatel nespecifikuje jinak.
```python
DEFAULT_LOCATION = "Frýdek-Místek"
```

---

<a name="resource-management"></a>

<a name="resource-management-správa-zdroju"></a>
## ⚡ Resource Management (Správa Zdroju)

Nastavení prahových hodnot pro 4-úrovňový systém správy paměti (RAM).

| Proměnná | Hodnota | Popis |
|----------|---------|-------|
| `RESOURCE_TIER_1_THRESHOLD` | 80% | **Warning:** Spouští se garbage collection a cleanup. |
| `RESOURCE_TIER_2_THRESHOLD` | 90% | **Active:** Omezuje se kontext LLM, maže se cache. |
| `RESOURCE_TIER_3_THRESHOLD` | 95% | **Emergency:** Kill non-essential procesů, maximální úspora. |

```python
RESOURCE_TIER_1_THRESHOLD = 80
RESOURCE_TIER_2_THRESHOLD = 90
RESOURCE_TIER_3_THRESHOLD = 95
```

<a name="dynamic-swap"></a>
### Dynamic SWAP
Nastavení pro automatické zvětšování SWAP paměti na Raspberry Pi.
```python
ENABLE_DYNAMIC_SWAP = True  # Zapnuto/Vypnuto
SWAP_MIN_SIZE_GB = 2        # Minimální velikost
SWAP_MAX_SIZE_GB = 8        # Maximální velikost při zátěži
```

<a name="llm-resource-adaptation"></a>
### LLM Resource Adaptation
Dynamická změna velikosti kontextového okna (tokenů) podle zatížení systému.
```python
LLM_CONTEXT_NORMAL = 2048   # Běžný provoz
LLM_CONTEXT_TIER1 = 2048    # Při Tier 1 (80% RAM)
LLM_CONTEXT_TIER2 = 1024    # Při Tier 2 (90% RAM) - snížení kvality pro stabilitu
LLM_CONTEXT_TIER3 = 1024    # Při Tier 3 (95% RAM)
```

---

<a name="boredom-system"></a>

<a name="boredom-system-nuda"></a>
## 🥱 Boredom System (Nuda)

Nastavení autonomního chování agenta, když s ním nikdo neinteraguje.

<a name="boredom_interval"></a>
### `BOREDOM_INTERVAL`
Čas v sekundách mezi kontrolami "nudy". Pokud nikdo nepíše, agent se po této době může sám ozvat nebo něco udělat.
```python
BOREDOM_INTERVAL = 300  # 5 minut
```

<a name="topics_file"></a>
### `TOPICS_FILE`
Soubor s tématy, o kterých agent přemýšlí nebo mluví, když se nudí.
```python
TOPICS_FILE = "boredom_topics.json"
```
Pokud soubor existuje, `web_tool` (při autonomním fallbacku) vybírá témata z něj. Pokud ne, použije interní seznam.

---

<a name="discord-activity-settings"></a>
## 🎮 Discord Activity Tool Settings

<a name="discord_activity_ignore_users"></a>
### `DISCORD_ACTIVITY_IGNORE_USERS`
Seznam ID uživatelů, jejichž aktivity (hry, statusy) má agent ignorovat.
```python
DISCORD_ACTIVITY_IGNORE_USERS = []
```

---

<a name="memory-scoring-system"></a>

<a name="memory-scoring-system-paměť"></a>
## 🧠 Memory Scoring System (Paměť)

Konfigurace pro ukládání vzpomínek do dlouhodobé paměti. Určuje, co je "důležité".

| Klíč | Hodnota | Popis |
|------|---------|-------|
| `MIN_SCORE_TO_SAVE` | 70 | Minimální skóre (0-100) pro uložení do DB. |
| `ERROR_PENALTY` | -20 | Penalizace, pokud text obsahuje chyby. |
| `KEYWORD_BONUS` | 10 | Body navíc za každé klíčové slovo. |
| `UNIQUENESS_BONUS` | 30 | Body za unikátní informaci. |
| `UNIQUENESS_THRESHOLD` | 0.90 | Hranice podobnosti (90%) pro určení duplicity. |

**Klíčová slova (`KEYWORDS`):**
`def`, `class`, `api`, `návod`, `fix`, `tool`, `python`, `code`

**Blacklist (`BLACKLIST`):**
`error`, `chyba` (slova, která snižují skóre)

---

<a name="security"></a>

<a name="security-bezpečnost"></a>
## 🔒 Security (Bezpečnost)

<a name="ip_sanitization_enabled"></a>
### `IP_SANITIZATION_ENABLED`
Globální přepínač pro maskování IP adres v logách a Discord zprávách.
```python
IP_SANITIZATION_ENABLED = True
```
Pokud je `True`, všechny IPv4 adresy (např. `192.168.1.20`) budou nahrazeny za `[IP_REDACTED]`.

<a name="shell-restrictions"></a>
### `ONLY_ADMIN_RESTRICTED_COMMANDS`
Seznam shell příkazů, které jsou zakázány pro běžné uživatele (i když by měli přístup k `!cmd`, který je sám o sobě admin-only). Slouží jako extra bezpečnostní vrstva.

Obsahuje nebezpečné operace jako:
- `rm`, `mkfs`, `dd` (destruktivní)
- `nano`, `vim` (interaktivní editory)
- `python`, `bash` (spouštění skriptů)
- `sudo`, `su` (eskalace práv)
- `wget`, `curl` (stahování)
- `git`, `apt`, `systemctl`...

```python
ONLY_ADMIN_RESTRICTED_COMMANDS = [
    "rm -rf", "mkfs", "dd", ...
]
```

---

<a name="web-interface"></a>
## 🌐 Web Interface

Nastavení webového dashboardu a dokumentace.

```python
WEB_DASHBOARD_REFRESH_INTERVAL = 10     # Sekundy (refresh rate)
WEB_SERVER_AUTO_RESTART = True          # Auto-restart při pádu
WEB_INTERFACE_TIMEOUT = 3600            # 1 hodina (auto-shutdown při neaktivitě)
WEB_WEBSOCKET_UPDATE_INTERVAL = 2       # Sekundy (realtime update)
DOCUMENTATION_WEB_URL = "http://localhost:5001/docs"
```

---

<a name="fuzzy-matching"></a>
## 🔍 Fuzzy Matching

Tolerance překlepů v příkazech.

```python
FUZZY_MATCH_DISTANCE_BASE_COMMANDS = 2  # Max chyb pro hlavní příkaz (např. !help)
FUZZY_MATCH_DISTANCE_SUBCOMMANDS = 4    # Max chyb pro sub-příkazy
```

---

<a name="github-release"></a>
## 📦 GitHub Release Management

Účty automatického uploadu verzí.

```python
GITHUB_UPLOAD_MIN_INTERVAL = 7200       # 2 hodiny (min interval)
GITHUB_REPO_NAME = "davca2848123/AI_agent"
```

---

<a name="error-recovery"></a>
## 🛡️ Error Recovery

Nastavení automatické opravy při startech.

```python
STARTUP_RETRY_LIMIT = 3                 # Počet pokusů o restart
STARTUP_FAILURE_WAIT = 21600            # 6 hodin (wait time po selhání)
```

---

<a name="agent-behavior"></a>
## 🤖 Agent Behavior

Detailní nastavení chování agenta (doplňuje Boredom System).

```python
BOREDOM_THRESHOLDS = {
    "LOW": 0.2,
    "HIGH": 0.4
}
BOREDOM_DECAY_RATE = 0.05               # 5% za interval

DEFAULT_AGENT_GOALS = [
    "Learn new things using tools",
    "Try to maintain boredom below 70%",
    "Use diverse tools",
    "Build knowledge base"
]
```

---

<a name="file-paths"></a>
## 📁 File Paths

Cesty k důležitým souborům.

```python
LOG_FILE_MAIN = "agent.log"
LOG_FILE_TOOLS = "agent_tools.log"
CRASH_MARKER_FILE = "crash_marker"
SHUTDOWN_INCOMPLETE_FILE = ".shutdown_incomplete"
GOALS_FILE = "agent_goals.json"
```


<a name="související"></a>
## 🔗 Související

- [🚀 Deployment Guide](../scripts/deployment-guide.md)
- [🆘 Troubleshooting](../troubleshooting.md)
- [📜 Scripts](../scripts/batch-scripts-reference.md)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
