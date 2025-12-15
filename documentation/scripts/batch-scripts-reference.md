# 📜 Batch Scripts Reference

> **Navigace:** [📂 Dokumentace](../README.md) | [📜 Scripts](../README.md#scripts-skripty) | [Batch Scripts Reference](batch-scripts-reference.md)

> Kompletní reference všech Windows batch skriptů pro RPI správu.
> **Verze:** Beta - CLOSED

---

<a name="obsah"></a>
## 📋 Obsah

- [Přehled](#přehled)
- [Konfigurace](#konfigurace)
- [Maintenance Scripts](#maintenance-scripts)
- [Setup Scripts](#setup-scripts)
- [SSH & Connection](#ssh--connection)
- [Advanced Scripts](#advanced-scripts)

---

<a name="overview"></a>

<a name="přehled"></a>
## Přehled

Všechny batch skripty se nacházejí v `scripts/` adresáři a slouží k vzdálené správě Raspberry Pi z Windows počítače přes SSH.

<a name="před-použitím"></a>
### Před Použitím

**1. Nastav SSH připojení:**

V každém `.bat` souboru uprav:
```batch
set RPI_HOST=192.168.1.100    ← IP adresa nebo hostname RPi
set RPI_PORT=22                ← SSH port  
set RPI_USER=davca             ← Tvoje username
```

**2. Zkontroluj SSH klíče:**

Skripty vyžadují passwordless SSH. Viz: `Windows_SSH_Permissions_Fix.md`

---

<a name="configuration"></a>

<a name="konfigurace"></a>
## Konfigurace

<a name="ssh_configbat"></a>
### `ssh_config.bat`

**Účel:** Nastavení SSH connection parametrů

**Použití:**
```batch
ssh_config.bat
```

**Co dělá:**
1. Vytvoří/aktualizuje `.ssh/config`
2. Nastaví  `UserKnownHostsFile` pro známé hosty
3. Konfiguruje connection timeout

**Poznámka:** Spusť jednou před prvním použitím ostatních skriptů.

---

<a name="maintenance-scripts"></a>
## Maintenance Scripts

<a name="rpi_restart_servicebat"></a>
### `rpi_restart_service.bat`

**Účel:** Restartuje AI Agent service na RPi

**Použití:**
```batch
rpi_restart_service.bat
```

**Co dělá:**
```batch
ssh davca@rpi 'sudo systemctl restart rpi-agent.service'
ssh davca@rpi 'sudo systemctl status rpi-agent.service'
```

**Output:**
```
● rpi-agent.service - RPI AI Discord Agent
   Loaded: loaded
   Active: active (running) since...
```

**Kdy použít:**
- Po změně konfigurace
- Po git pull (update kódu)
- Když agent nereaguje

---

<a name="rpi_health_checkbat"></a>
### `rpi_health_check.bat`

**Účel:** Komplexní health check RPi

**Použití:**
```batch
rpi_health_check.bat
```

**Co kontroluje:**
1. **Service status** - Je agent spuštěný?
2. **System resources** - CPU, RAM, Disk
3. **Temperature** - RPI teplota
4. **Last log entries** - Poslední 10 řádků logu

**Příklad outputu:**
```
===== RPI HEALTH CHECK =====

Service Status:
● rpi-agent.service - RPI AI Discord Agent
   Active: active (running)

System Resources:
CPU: 25%
RAM: 1.2G / 3.8G (32%)
Disk: 12G / 28G (43%)

Temperature:
temp=48.2'C

Recent Logs:
[INFO] Boredom loop running...
[INFO] LLM response generated (250ms)
```

**Kdy použít:**
- Pravidelná kontrola (denně)
- Po restartu systému
- Při debuggingu výkonu

---

<a name="rpi_cleanup_logsbat"></a>
### `rpi_cleanup_logs.bat`

**Účel:** Vyčistí staré logy, ponechá pouze posledních 40%

**Použití:**
```batch
rpi_cleanup_logs.bat
```

**Co dělá:**
```python
# Spustí: scripts/internal/task_prune_logs.py
# Odstraní nejstarší 60% řádků z agent.log
```

**Před:**
```
agent.log: 50 MB (500,000 lines)
```

**Po:**
```
agent.log: 20 MB (200,000 lines)
agent.log.old: 30 MB (backup)
```

**Kdy použít:**
- `agent.log` > 50 MB
- Systém je pomalý (high IO)
- Před důležitými operacemi

**⚠️ Poznámka:** Automaticky vytvoří backup jako `agent.log.old`

---

<a name="rpi_cleanup_memorybat"></a>
### `rpi_cleanup_memory.bat`

**Účel:** Vyčistí spam záznamy z memory database

**Použití:**
```batch
rpi_cleanup_memory.bat
```

**Interaktivní:**
```
1) Dry-run (pouze analýza)
2) Cleanup (vyčištění s backupem)
Vyber [1-2]:
```

**Co odstran í:**
- Duplicitní záznamy
- Systémový spam (Discord events)
- Nízko-skóre memorie (< 0.3)

**Příklad:**
```
=== MEMORY CLEANUP ===

Records before: 5,234
Spam records: 2,891
After cleanup: 2,343

Backup created: backup/agent_memory_2025-12-03.db
```

**Kdy použít:**
- Database > 10 MB
- Pomalé queries v `!memory`
- Pravidelně měsíčně

---

<a name="setup-scripts"></a>
## Setup Scripts

<a name="rpi_setup_swapbat"></a>
### `rpi_setup_swap.bat`

**Účel:** Nastaví sudo bez hesla pro SWAP management

**Použití:**
```batch
rpi_setup_swap.bat
```

**⚠️ CRITICAL:** Spusť **pouze jednou** při první konfiguraci!

**Co dělá:**
```bash
# Přidá do /etc/sudoers.d/swap_management:
davca ALL=(ALL) NOPASSWD: /bin/dd, /sbin/mkswap, /sbin/swapon, /sbin/swapoff
```

**Proč je to potřeba:**
- Agent automaticky rozšiřuje SWAP při nízké RAM
- Resource manager potřebuje sudo bez hesla

**Detaily:** Viz `RPI_Sudoers_NOPASSWD_Guide.md`

---

<a name="rpi_setup_ledbat"></a>
### `rpi_setup_led.bat`

**Účel:** Nastaví GPIO LED indikátory

**Použití:**
```batch
rpi_setup_led.bat
```

**Co dělá:**
1. Nastaví GPIO pins pro OUTPUT mode
2. Nainstaluje `RPi.GPIO` Python modul
3. Testuje LED bliknutím

**LEDs:**
- **GPIO 17** - Status LED (zelená)
- **GPIO 27** - Error LED (červená)

**Poznámka:** Vyžaduje fyzické LED připojené k GPIO pinům.

---

<a name="rpi_test_ledbat"></a>
### `rpi_test_led.bat`

**Účel:** Test LED funkcional ity

**Použití:**
```batch
rpi_test_led.bat
```

**Output:**
```
Testing LED on GPI O 17...
LED should blink 3 times
[GPIO 17: ON]
[GPIO 17: OFF]
...
Test complete!
```

---

<a name="setup_rpi_sudoersbat"></a>
### `setup_rpi_sudoers.bat`

**Účel:** Komplexní sudo setup (hlavní  script)

**Použití:**
```batch
setup_rpi_sudoers.bat
```

**Co konfiguruje:**
- SWAP management (`dd`, `mkswap`, `swapon`, `swapoff`)
- Service management (`systemctl`)
- Log rotation (`logrotate`)
- Package updates (`apt-get`)

**⚠️ Bezpečnostní otázka:**
Tento script poskytuje široké sudo permissions. Použij pouze na důvěryhodném RPi!

---

<a name="setup_ssh_passwordlessbat"></a>
### `setup_ssh_passwordless.bat`

**Účel:** Nastaví SSH klíče pro passwordless login

**Použití:**
```batch
setup_ssh_passwordless.bat
```

**Co dělá:**
1. Generuje SSH klíč (pokud neexistuje)
2. Zkopíruje public key na RPi
3. Testuje connectioná

**Interaktivní:**
```
Zadej heslo pro davca@rpi:
********

SSH key uploaded successfully!
Testing connection...
✓ Passwordless SSH works!
```

---

<a name="ssh-connection"></a>
## SSH & Connection

<a name="ssh_connectbat"></a>
### `ssh_connect.bat`

**Účel:** Rychlé SSH připojení k RPi

**Použití:**
```batch
ssh_connect.bat
```

**Co dělá:**
```batch
ssh davca@192.168.1.100
```

Otevře interaktivní SSH session.

**Poznámka:** Pro používání s ngrok upravit na:
```batch
ssh davca@0.tcp.ngrok.io -p 12345
```

---

<a name="advanced-scripts"></a>
## Advanced Scripts

<a name="rpi_rebuild_pythonbat"></a>
### `rpi_rebuild_python.bat`

**Účel:** Přeinstaluje všechny Python závislosti

**Použití:**
```batch
rpi_rebuild_python.bat
```

**Co dělá:**
```bash
cd ~/rpi_ai/rpi_ai
pip3 uninstall -r requirements.txt -y
pip3 install -r requirements.txt --break-system-packages
```

**Kdy použít:**
- Po update Python verze
- Při "ModuleNotFoundError"
- Po přidání nové dependency do `requirements.txt`

**⚠️ Upozornění:** Agent deve být během toho zastaven!

---

<a name="rpi_task_cleanup_boredombat"></a>
### `rpi_task_cleanup_boredom.bat`

**Účel:** Vyčistí boredom topics JSON

**Použití:**
```batch
rpi_task_cleanup_boredom.bat
```

**Co dělá:**
```bash
# Odstraní/resetuje boredom_topics.json
rm boredom_topics.json
echo '{"topics": []}' > boredom_topics.json
```

**Kdy použít:**
- Topics JSON je corrupted
- Chceš resetovat témata

---

<a name="rpi_fix_llmbat"></a>
### `rpi_fix_llm.bat`

**Účel:** Fix LLM loading issues

**Použití:**
```batch
rpi_fix_llm.bat
```

**Co dělá:**
```bash
# Spustí: scripts/fix_llm_fast.py nebo scripts/fix_llm_full.py
# Redownloaduje/rekonfiguruje LLM model
```

**Kdy použít:**
- LLM se nenačte
- "Model file corrupted" error
- Po přerušení staahování modelu

---

<a name="rpi_clear_dmbat"></a>
### `rpi_clear_dm.bat`

**Účel:** Vymaže bot DM zprávy v admin kanálu

**Použití:**
```batch
rpi_clear_dm.bat
```

**Co dělá:**
```python
# Spustí: scripts/internal/task_clear_dm.py
# Smaže všechny bot zprávy kromě poslední "active"
```

**Kdy použít:**
- Admin DM je zahlcený starými zprávami
- Před důležitým reportem
- Při testování DM funkcí

---

<a name="creating-custom-scripts"></a>

<a name="vytvoření-vlastního-scriptu"></a>
## 🔧 Vytvoření Vlastního Scriptu

<a name="template"></a>
### Template

```batch
@echo off
setlocal

REM === KONFIGURACE ===
set RPI_HOST=192.168.1.100
set RPI_PORT=22
set RPI_USER=davca

REM === TVŮJ KÓD ===
echo Connecting to %RPI_USER%@%RPI_HOST%...

ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "
    cd ~/rpi_ai/rpi_ai
    # Tvoje příkazy zde
    echo 'Hello from RPI!'
"

pause
```

<a name="best-practices"></a>
### Best Practices

1. **Vždy používej `cd ~/rpi_ai/rpi_ai`** na začátku remote příkazů
2. **Test nejprve manuálně** přes `ssh_connect.bat`
3. **Přidej error handling:**
   ```batch
   if %ERRORLEVEL% NEQ 0 (
       echo Error occurred!
       pause
       exit /b 1
   )
   ```
4. **Log output** do souboru pokud potřebuješ historii

---

<a name="summary-table"></a>
## 📊 Summary Table

| Script | Kategorie | Použití | Risk |
|--------|-----------|---------|------|
| `rpi_restart_service.bat` | Maintenance | Restart agenta | 🟢 Nízké |
| `rpi_health_check.bat` | Maintenance | Kontrola stavu | 🟢 Nízké |
| `rpi_cleanup_logs.bat` | Maintenance | Cleanup logů | 🟡 Střední |
| `rpi_cleanup_memory.bat` | Maintenance | Cleanup DB | 🟡 Střední |
| `rpi_setup_swap.bat` | Setup | Sudo config | 🔴 Vysoké |
| `rpi_setup_led.bat` | Setup | GPIO LED | 🟢 Nízké |
| `setup_rpi_sudoers.bat` | Setup | Sudo permissions | 🔴 Vy soké |
| `setup_ssh_passwordless.bat` | SSH | SSH keys | 🟡 Střední |
| `ssh_connect.bat` | SSH | SSH session | 🟢 Nízké |
| `rpi_rebuild_python.bat` | Advanced | Reinstall deps | 🟡 Střední |
| `rpi_fix_llm.bat` | Advanced | Fix LLM | 🟡 Střední |
| `rpi_clear_dm.bat` | Advanced | Clear DMs | 🟢 Nízké |

---

<a name="související"></a>
## 🔗 Související

- [📖 Deployment Guide](deployment-guide.md) - Kompletní deployment proces
- [Windows SSH Permissions](Windows_SSH_Permissions_Fix.md) (Markdown)
- [RPI Sudoers Guide](RPI_Sudoers_NOPASSWD_Guide.md) (Markdown)- Detailed sudo setup
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
