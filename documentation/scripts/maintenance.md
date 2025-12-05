# Údržbové Skripty

> **Navigace:** [📂 Dokumentace](../README.md) | [📜 Scripts](../README.md#scripts-skripty) | [Maintenance Scripts](maintenance.md)

> Skripty pro údržbu a správu agenta.
> **Verze:** Alpha

---

<a name="přehled"></a>
## 📝 Přehled

Údržbové skripty slouží k pravidelnému čištění a údržbě AI agenta, včetně správy logů, databáze a systémových zdrojů.

---

<a name="cleanup-logs"></a>

<a name="cleanup_logspy"></a>
## `cleanup_logs.py`

<a name="popis"></a>
### 📋 Popis
Smaže staré logy z obou log souborů (`agent.log` a `agent_tools.log`). Skript automaticky detekuje timestamp v každém řádku logu a smaže záznamy starší než 2 dny.

<a name="použití"></a>
### ⚙️ Použití

**Manuální spuštění na RPI:**
```bash
# Z root adresáře projektu:
python3 scripts/internal/cleanup_logs.py

# Nebo přímo v adresáři:
cd scripts/internal
python3 cleanup_logs.py
```

**Spuštění z Windows (SSH):**
```batch
# Z adresáře scripts:
rpi_cleanup_logs.bat
```

> **Poznámka:** `.bat` skript se automaticky připojí přes SSH na RPI (192.168.1.200) a spustí cleanup script.

<a name="jak-to-funguje"></a>
### 💡 Jak to funguje

1. **Vypočítá cutoff datum** - Dnešní datum - 2 dny (od 00:00)
2. **Načte oba log soubory** - agent.log a agent_tools.log
3. **Parsuje timestamp** - Z každého řádku (formát: `YYYY-MM-DD HH:MM:SS`)
4. **Filtruje řádky** - Odstraní řádky starší než cutoff datum
5. **Přepíše soubory** - S čistými logy

<a name="logika"></a>
### 🔧 Logika

**Cutoff datum:**
```python
cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
```

**Parsování timestampu:**
```python
timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
if timestamp_match:
    log_timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
    if log_timestamp >= cutoff_date:
        kept_lines.append(line)
```

**Zpracované soubory:**
- `agent.log` - Hlavní log agenta
- `agent_tools.log` - Logy použití nástrojů

<a name="příklad-výstupu"></a>
### 📝 Příklad výstupu

```
Deleting log entries older than: 2025-11-30 00:00:00

Processing agent.log...
Total lines: 15234
Deleted lines: 8942
Kept lines: 6292
Done cleaning agent.log

Processing agent_tools.log...
Total lines: 5678
Deleted lines: 2341
Kept lines: 3337
Done cleaning agent_tools.log

All log files processed.
```

<a name="poznámky"></a>
### ⚠️ Poznámky

- **Bezpečné parsování** - Pokud timestamp nelze parsovat, řádek se zachová
- **Multi-line logy** - Pokud řádek nemá timestamp (např. stack trace), zachová se
- **Automatická detekce** - Skript hledá logy v aktuálním adresáři i v parent
- **Pouze ruční spuštění** - Není automatizováno, spouští se manuálně

<a name="související"></a>
### 🔗 Související

- **Zobrazení logů:** `!logs <count>` - [📖 Data Management](../commands/data-management.md#logs)
- **Live logs:** `!live logs <duration>` - [📖 Data Management](../commands/data-management.md#live-logs)
- **Monitoring:** `!monitor` - [📖 Admin Commands](../commands/admin.md#monitor)

---

<a name="future-scripts"></a>

<a name="budoucí-skripty"></a>
## Budoucí Skripty

Plánované utility skripty:

- [ ] `cleanup_memory.py` - Čištění staré databáze vzpomínek
- [ ] `backup_database.py` - Zálohování agent_memory.db
- [ ] `optimize_database.py` - VACUUM a optimalizace SQLite
- [ ] `check_health.py` - Health check celého systému
- [ ] `manage_swap.py` - Správa SWAP souboru

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
