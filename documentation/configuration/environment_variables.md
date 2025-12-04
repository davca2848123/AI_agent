# 🌍 Environment Variables

> Možnosti konfigurace pomocí proměnných prostředí (Environment Variables).

Tyto proměnné mají přednost před nastavením v `config_settings.py`. Jsou užitečné pro Docker, Systemd služby nebo dočasné změny chování.

## 📋 Seznam Proměnných

| Proměnná | Popis | Příklad |
|----------|-------|---------|
| `MODEL_CACHE_DIR` | Cesta k adresáři s modely | `/home/user/models` |
| `LLM_CONTEXT_NORMAL` | Velikost kontextového okna | `2048` |
| `LOG_LEVEL` | Úroveň logování (DEBUG, INFO, WARNING) | `DEBUG` |
| `LOG_FILE` | Název souboru s logy | `custom_agent.log` |
| `RAM_TIER1_THRESHOLD` | Práh pro Tier 1 správu paměti (%) | `80` |

## 💻 Použití v Terminálu

Můžete nastavit proměnné před spuštěním skriptu:

```bash
# Linux / macOS
export LOG_LEVEL="DEBUG"
python3 main.py

# Windows (PowerShell)
$env:LOG_LEVEL="DEBUG"
python main.py
```

## ⚙️ Použití v Systemd Service

Pro trvalé nastavení na Raspberry Pi upravte soubor služby:

`/etc/systemd/system/rpi-agent.service`

```ini
[Service]
Environment="MODEL_CACHE_DIR=/home/davca/models"
Environment="LOG_LEVEL=INFO"
ExecStart=/usr/bin/python3 /home/davca/rpi_ai/main.py
```

Po změně nezapomeňte reloadnout daemona:
```bash
sudo systemctl daemon-reload
sudo systemctl restart rpi-agent
```
