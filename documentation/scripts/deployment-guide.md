# 🚀 Deployment Guide

> **Navigace:** [📂 Dokumentace](../README.md) | [📜 Scripts](../README.md#scripts-skripty) | [Deployment Guide](deployment-guide.md) | [🔍 Hledat](../INDEX.md#vyhledavani)

> Komplexní průvodce nasazením AI Agenta na Raspberry Pi.
> **Verze:** Alpha

---

<a name="obsah"></a>
## 📋 Obsah

1. [Požadavky](#požadavky)
2. [Počáteční Nastavení](#počáteční-nastavení) 
3. [Instalační Kroky](#instalační-kroky)
4. [Konfigurace Autostart](#konfigurace-autostart)
5. [Údržba a Monitoring](#údržba-a-monitoring)
6. [Troubleshooting](#troubleshooting)

---

<a name="requirements"></a>

<a name="požadavky"></a>
## Požadavky

<a name="hardware"></a>
### Hardware
- **Raspberry Pi 4B** (4GB+ RAM doporučeno)
- **SD karta** 32GB+ (Class 10)
- **Internetovépřipojení** (Ethernet nebo WiFi)

<a name="software"></a>
### Software
- **OS:** Debian/Raspberry Pi OS (64-bit)
- **Python:** 3.10+
- **Git** pro klonování projektu

<a name="účty-tokeny"></a>
### Účty & Tokeny
- Discord Bot Token
- Discord Admin User ID
- (Volitelně) Ngrok Auth Token pro SSH tunelování

---

<a name="initial-setup"></a>

<a name="počáteční-nastavení"></a>
## Počáteční Nastavení

<a name="1-příprava-raspberry-pi"></a>
### 1. Příprava Raspberry Pi

```bash
# Aktualizace systému
sudo apt update && sudo apt upgrade -y

# Instalace požadovaných balíčků
sudo apt install -y python3 python3-pip git

# Instalace systémových závislostí
sudo apt install -y build-essential cmake

# (Volitelně) Nastavit LED indikátory
# viz scripts/rpi_setup_led.bat
```

<a name="2-klonování-projektu"></a>
### 2. Klonování Projektu

```bash
cd ~
git clone https://github.com/your-username/rpi_ai.git
cd rpi_ai/rpi_ai
```

<a name="3-konfigurace-secrets"></a>
### 3. Konfigurace Secrets

Vytvoř `config_secrets.py`:

```python
# config_secrets.py
DISCORD_BOT_TOKEN = "tvůj_discord_bot_token_zde"
ADMIN_USER_IDS = [123456789012345678]  # Tvoje Discord User ID
NGROK_AUTH_TOKEN = "tvůj_ngrok_token"  # Volitelné
```

⚠️ **Nikdy necommituj tento soubor do Gitu!**

<a name="4-instalace-python-závislostí"></a>
### 4. Instalace Python Závislostí

```bash
# Vytvoř virtuální prostředí (doporučeno)
python3 -m venv venv
source venv/bin/activate

# Instalace závislostí
pip3 install -r requirements.txt --break-system-packages
```

**Poznámka:** Flag  `--break-system-packages` je nutný na novějších verzích Debian/RPi OS.

---

<a name="installation-steps"></a>

<a name="instalační-kroky"></a>
## Instalační Kroky

<a name="krok-1-test-funkčnosti"></a>
### Krok 1: Test Funkčnosti

Před konfigurací autostartu otestuj, že agent funguje:

```bash
cd ~/rpi_ai/rpi_ai
python3 main.py
```

Očekávaný output:
```
[INFO] Discord client initialized
[INFO] LLM loading...
[INFO] Tools registered: 14
[INFO] Agent started successfully
```

Zastavit: `Ctrl+C`

<a name="krok-2-nastavení-swap-kritické"></a>
### Krok 2: Nastavení SWAP (Kritické!)

Agent vyžaduje dostatek paměti. Nastav SWAP:

**Z Windows:**
```batch
scripts\rpi_setup_swap.bat
```

**Nebo přímo na RPi:**
```bash
# Vytvoř 4GB swap file
sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Permanentní aktivace (přidej do /etc/fstab)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

<a name="krok-3-sudo-bez-hesla-pro-resource-management"></a>
### Krok 3: Sudo bez Hesla (Pro Resource Management)

Agent potřebuje rozšiřovat SWAP automaticky:

**Z Windows:**
```batch
scripts\setup_rpi_sudoers.bat
```

**Nebo ručně:**
```bash
sudo visudo
```

Přidej na konec:
```
davca ALL=(ALL) NOPASSWD: /bin/dd, /sbin/mkswap, /sbin/swapon, /sbin/swapoff
```

Detaily viz: `scripts/RPI_Sudoers_NOPASSWD_Guide.md`

<a name="krok-4-systemd-service-autostart"></a>
### Krok 4: Systemd Service (Autostart)

Vytvoř systemd service pro automatický start:

```bash
sudo nano /etc/systemd/system/rpi-agent.service
```

Obsah:
```ini
[Unit]
Description=RPI AI Discord Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=davca
WorkingDirectory=/home/davca/rpi_ai/rpi_ai
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 /home/davca/rpi_ai/rpi_ai/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Aktivace:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rpi-agent.service
sudo systemctl start rpi-agent.service
```

Kontrola stavu:
```bash
sudo systemctl status rpi-agent.service
```

---

<a name="autostart-configuration"></a>

<a name="konfigurace-autostart"></a>
## Konfigurace Autostart

<a name="restart-po-c-rashi"></a>
### Restart po C rashi

Service je nakonfigurovaný s `Restart=always` a `RestartSec=10`, takže:
- Při jakémkoliv pádu se agent automaticky restartuje za 10s
- Při restartu systému se service automaticky spustí

<a name="viewing-logs"></a>
### Viewing Logs

**Real-time logy:**
```bash
sudo journalctl -u rpi-agent.service -f
```

**Poslední 50 řádků:**
```bash
sudo journalctl -u rpi-agent.service -n 50
```

**Vč včera:**
```bash
sudo journalctl -u rpi-agent.service --since yesterday
```

---

<a name="maintenance-monitoring"></a>

<a name="údržba-a-monitoring"></a>
## Údržba a Monitoring

<a name="windows-batch-skripty"></a>
### Windows Batch Skripty

Z Windows můžeš spravovat RPi pomocí batch skriptů v `scripts/`:

| Script | Účel |
|--------|------|
| `rpi_restart_service.bat` | Restart agenta |
| `rpi_health_check.bat` | Kontrola stavu |
| `rpi_cleanup_logs.bat` | Vyčištění starých logů |
| `rpi_cleanup_memory.bat` | Vyčištění paměti database |

**Před použitím**: Nastav IP adresu v každém `.bat`:
```batch
set RPI_HOST=192.168.1.100
set RPI_USER=davca
```

<a name="discord-příkazy"></a>
### Discord Příkazy

Z Discordu:
- `!status` - Kontrola, že agent ží je
- `!debug quick` - Rychlá diagnostika
- `!monitor 30` - Live monitoring zdrojů
- `!restart` - Restart agenta (admin)

<a name="pravidelná-údržba"></a>
### Pravidelná Údržba

**Týdenně:**
- Zkontroluj `!stats` - Ověř, že agent se učí
- Proveď memory cleanup pokud databáze \u003e 10 MB

**Měsíčně:**
- System update: `sudo apt update && sudo apt upgrade`
- Backup memory database: `cp agent_memory.db backup/`

---

<a name="troubleshooting"></a>
## Troubleshooting

<a name="agent-se-nespustí"></a>
### Agent se nespustí

**1. Zkontroluj logy:**
```bash
sudo journalctl -u rpi-agent.service -n 100
```

**2. Zkontroluj Python závislosti:**
```bash
cd ~/rpi_ai/rpi_ai
pip3 list | grep -E "discord|llama"
```

**3. Test manuálně:**
```bash
cd ~/rpi_ai/rpi_ai
python3 main.py
```

<a name="llm-se-nenačte"></a>
### LLM se nenačte

**Problém:** Nedostatek RAM

**Řešení:**
```bash
# Zkontroluj SWAP
free -h

# Pokud SWAP = 0, nastav podle Krok 2 výše
```

<a name="discord-connection-failed"></a>
### Discord Connection Failed

**1. Ověř token:**
```python
# V config_secrets.py
print(DISCORD_BOT_TOKEN)  # Měl by začínat s "MT..."
```

**2. Zkontroluj internet:**
```bash
ping discord.com
```

**3. Zkontroluj bot permissions:**
- Bot potřebuje "MESSAGE_CONTENT" Intent v Discord Developer Portal

<a name="service-se-nerestartuje"></a>
### Service se nerestartuje

```bash
# Zkontroluj service status
sudo systemctl status rpi-agent.service

# Zobraz error logy
sudo journalctl -u rpi-agent.service --since "10 minutes ago"

# Reload if needed
sudo systemctl daemon-reload
sudo systemctl restart rpi-agent.service
```

<a name="memory-database-corruption"></a>
### Memory Database Corruption

**Symptom:** Agent hlásí database errors

**Řešení:**
```bash
cd ~/rpi_ai/rpi_ai

# 1. Backup current
cp agent_memory.db agent_memory.db.backup

# 2. Test integrity
sqlite3 agent_memory.db "PRAGMA integrity_check;"

# 3. Pokud corrupted, restore from backup
cp backup/agent_memory_YYYY-MM-DD.db agent_memory.db

# 4. Restart agent
sudo systemctl restart rpi-agent.service
```

---

<a name="security"></a>

<a name="bezpečnost"></a>
## 🔒 Bezpečnost

<a name="ssh-hardening"></a>
### SSH Hardening

```bash
# Disable password auth (use keys only)
sudo nano /etc/ssh/sshd_config
```

Nastav:
```
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
```

<a name="firewall"></a>
### Firewall

```bash
sudo apt install ufw
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

<a name="pravidelné-updatesá"></a>
### Pravidelné Updatesá

```bash
# Setup automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

<a name="související-dokumentace"></a>
## 📚 Související Dokumentace

- [Batch Scripts Reference](batch-scripts-reference.md) - Detaily všech `.bat` skriptů
- [RPI Sudoers Guide](../scripts/RPI_Sudoers_NOPASSWD_Guide.md) - Sudo bez hesla
- [Configuration Guide](../configuration/customization-guide.md) - Konfigurace nastavení

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
