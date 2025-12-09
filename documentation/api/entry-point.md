# 🚪 Main Entry Point API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Entry Point API](entry-point.md)

Dokumentace pro soubor `main.py`, který slouží jako vstupní bod aplikace.

<a name="přehled"></a>
## 📋 Přehled

`main.py` inicializuje prostředí, načítá konfiguraci a spouští hlavního agenta. Zajišťuje také:
- Logging s maskováním citlivých dat.
- Graceful shutdown (obsluha signálů).
- Startup error tracking (prevence boot loopu).

---

<a name="hlavní-komponenty"></a>
## 🔧 Hlavní komponenty

<a name="logging"></a>
### 1. Logging Configuration
- Konfiguruje `logging` pro konzoli (stdout) a soubory.
- Používá `SanitizingFormatter` pro maskování IP adres v konzoli.
- **Log Files**:
    - `agent.log`: Hlavní log aplikace.
    - `agent_tools.log`: Oddělený log pro nástroje (nešpiní hlavní log).

<a name="startup-protection"></a>
### 2. Startup Protection
Používá `agent.startup_tracker` pro prevenci nekonečných restartů.

```python
should_wait, wait_time = check_should_wait(
    retry_limit=config_settings.STARTUP_RETRY_LIMIT,
    wait_hours=config_settings.STARTUP_FAILURE_WAIT // 3600
)
```
Pokud agent spadne 3x (default) po sobě, `main.py` odmítne nastartovat po dobu 6 hodin (default).

<a name="initialization"></a>
### 3. Agent Initialization
1. Načte `config_secrets.py` (tokeny).
2. Importuje `AutonomousAgent`.
3. Inicializuje instanci s tokeny.
4. Volá `agent.start()`.
5. Zaznamená `record_success()` pokud start proběhl v pořádku.

<a name="shutdown"></a>
### 4. Shutdown Handling
Obsluha `SIGTERM` / `SIGINT` (nebo `KeyboardInterrupt` na Windows).
- Volá `shutdown()`, které:
    - Ukončí Discord spojení.
    - Zavře databázi.
    - Zapíše do logu.

---

<a name="spouštění"></a>
## 🚀 Spouštění

```bash
python main.py
```

Skript automaticky detekuje operační systém a přizpůsobí obsluhu signálů (Windows vs Linux).


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🚀 Deployment Guide](../scripts/deployment-guide.md)
- [📂 Source Code](../agent/)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
