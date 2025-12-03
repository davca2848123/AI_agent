# SSH & Maintenance Scripts

Tento adresář obsahuje batch skripty pro Windows pro snadnou správu Raspberry Pi.

## 📂 Struktura:

```
scripts/
├── internal/               # Skripty pro údržbu (spouštěné vzdáleně)
│   ├── setup_swap_sudo.sh
│   └── cleanup_memory.py
│
└── *.bat                   # Windows batch skripty
```

## 🚀 Použití:

### 1. **ssh_connect.bat**
Připojení k Raspberry Pi přes lokální síť.
```batch
ssh_connect.bat
```

### 2. **run_setup_swap.bat**
Nastaví sudo bez hesla pro SWAP managment.
```batch
run_setup_swap.bat
```
⚠️ Spustit **pouze jednou** při první konfiguraci!

### 3. **run_cleanup_memory.bat**
Vyčistí memory databázi od spam záznamů.
```batch
run_cleanup_memory.bat
```

**Volby:**
- `[1]` Dry-run - pouze analýza
- `[2]` Cleanup - vyčištění s automatickým backupem

---

## ⚙️ Nastavení IP adresy:

**PŘED PRVNÍM POUŽITÍM** edituj v každém `.bat` souboru:

```batch
set RPI_HOST=rpi          ← změň na IP nebo hostname
set RPI_PORT=22
set RPI_USER=davca
```

**Příklady:**
- Hostname: `set RPI_HOST=rpi` nebo `set RPI_HOST=raspberrypi`
- IP adresa: `set RPI_HOST=192.168.1.100`

---

## 📝 Poznámky:

- Připojení přes **lokální síť** (ne ngrok)
- Vyžaduje SSH klíče nebo heslo
- Cleanup script vytváří automaticky backup
- Setup swap je třeba spustit jen jednou
