# Scripts - Přehled

> Utility skripty pro správu RPI AI agenta přes SSH a lokální setup

## 📁 Struktura

```
scripts/
├── rpi_*.bat           # Operace na RPI (přes SSH)
├── setup_*.bat         # Setup/konfigurace
├── ssh_connect.bat     # Přímé SSH připojení
├── internal/           # Python/Shell utility skripty
└── *.md                # Dokumentace
```

## 🚀 Kategorie skriptů

### RPI Operace (`rpi_*.bat`)
Tyto skripty se připojují přes SSH na RPI a vykonávají operace:

| Skript | Popis | Spouští |
|--------|-------|---------|
| `rpi_cleanup_logs.bat` | Smaže logy starší než 2 dny | `cleanup_logs.py` |
| `rpi_cleanup_memory.bat` | Plnohodnotný DB cleanup (analýza + smazání) | `cleanup_memory.py` |
| `rpi_task_cleanup_boredom.bat` | Rychlé mazání boredom/error memories | `task_cleanup_memory.py` |
| `rpi_clear_dm.bat` | Smaže bot zprávy v Admin DM | `task_clear_dm.py` |
| `rpi_fix_llm.bat` | Instalace LLM závislostí | `fix_llm.sh` |
| `rpi_rebuild_python.bat` | Rebuild Python 3.12 na RPI | `fix_python_build.sh` |
| `rpi_restart_service.bat` | Restart systemd služby agenta | systemctl restart |
| `rpi_health_check.bat` | Health check agenta | `health_check.py` |
| `rpi_setup_swap.bat` | Setup SWAP souboru | `setup_swap_sudo.sh` |

### Setup Skripty (`setup_*.bat`)
Jednorázové setup/konfigurační skripty:

| Skript | Popis |
|--------|-------|
| `setup_ssh_passwordless.bat` | Nastaví SSH passwordless login |
| `setup_rpi_sudoers.bat` | Opraví RPI sudoers pro NOPASSWD |

### Ostatní

| Skript | Popis |
|--------|-------|
| `ssh_connect.bat` | Jednoduché SSH připojení na RPI |

## 📝 Použití

### Příklad: Cleanup logů
```batch
cd z:\rpi_ai\rpi_ai\scripts
rpi_cleanup_logs.bat
```

### Příklad: Health check
```batch
cd z:\rpi_ai\rpi_ai\scripts
rpi_health_check.bat
```

### Příklad: Setup SSH
```batch
cd z:\rpi_ai\rpi_ai\scripts
setup_ssh_passwordless.bat
```

## 🔧 Konfigurace SSH Připojení

### Centrální konfigurační soubor: `ssh_config.bat`

Všechny batch skripty načítají SSH nastavení z **`ssh_config.bat`**, což umožňuje změnit připojení na jednom místě.

**Upravte tento soubor pro vaše nastavení:**

```batch
@echo off
REM Raspberry Pi SSH Settings
set RPI_USER=davca
set RPI_HOST=192.168.1.200
set RPI_PORT=22

REM Path to project on RPI
set RPI_PROJECT_PATH=/home/davca/rpi_ai/rpi_ai
```

### Jak změnit konfiguraci:

1. Otevřete `scripts/ssh_config.bat`
2. Upravte hodnoty podle vašeho RPI:
   - **RPI_USER** - vaše uživatelské jméno na RPI
   - **RPI_HOST** - IP adresa nebo hostname RPI
   - **RPI_PORT** - SSH port (výchozí: 22)
   - **RPI_PROJECT_PATH** - cesta k projektu na RPI
3. Uložte soubor
4. Všechny .bat skripty automaticky použijí nové nastavení

> **Poznámka:** Nemusíte upravovat jednotlivé .bat skripty - všechny automaticky načítají `ssh_config.bat`!

## 📂 Internal složka

Složka `internal/` obsahuje Python a Shell skripty, které jsou spouštěny .bat skripty:

### Python skripty:
- `cleanup_logs.py` - Cleanup logů (podle data)
- `cleanup_memory.py` - Komplexní DB cleanup
- `task_cleanup_memory.py` - Rychlý cleanup task
- `task_clear_dm.py` - Clear DM task
- `health_check.py` - System health check
- `task_test_location.py` - Test lokace

### Shell skripty:
- `fix_llm.sh` - LLM dependencies install
- `fix_python_build.sh` - Python rebuild
- `setup_swap_sudo.sh` - SWAP setup

## ⚙️ Pojmenování konvence

- **`rpi_`** - Operace na RPI přes SSH
- **`setup_`** - Setup/konfigurační skripty
- **`task_`** (v internal/) - Jednoduché task skripty
- **`ssh_`** - SSH utility

---

**Poslední aktualizace:** 2025-12-06  
**Verze:** 2.0 (po přejmenování)
