# 🖥️ Hardware Monitor API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Hardware Monitor API](hardware-monitor.md)

Dokumentace pro modul `agent/hardware.py`.

<a name="přehled"></a>
## 📋 Přehled

Poskytuje rozhraní pro čtení systémových senzorů (teplota CPU, využití RAM) a ovládání indikační LED (pouze na Raspberry Pi).

---

<a name="hardwaresonitor"></a>
## 🔧 Třída HardwareMonitor

<a name="get_cpu_temp"></a>
### `get_cpu_temp() -> float`
Získá teplotu CPU ve stupních Celsia.
- **Raspberry Pi**: Používá `vcgencmd measure_temp` nebo sysfs.
- **Windows/Other**: Vrací mock hodnotu (45.0°C).

<a name="get_ram_usage"></a>
### `get_ram_usage() -> float`
Vrátí procentuální využití paměti RAM (0-100%).

<a name="is_safe_to_run"></a>
### `is_safe_to_run() -> bool`
Zkontroluje, zda jsou hodnoty v bezpečných mezích.
- **Thresholds**: 
    - Max Temp: 80°C
    - Max RAM: 90%
- Vrací `False` a loguje varování, pokud je limit překročen.

<a name="get_status"></a>
### `get_status() -> str`
Vrátí formátovaný string pro logy, např.: `"Temp: 45.2°C, RAM: 34.1%"`

---

<a name="ledindicator"></a>
## 💡 Třída LedIndicator

Ovládá systémovou LED (`/sys/class/leds/ACT/brightness`) pro vizuální zpětnou vazbu. Běží v samostatném vlákně.

<a name="stavy"></a>
### Stavy (`set_state`)
- `IDLE`: LED vypnuta (nebo heartbeat, dle OS).
- `BUSY`: Rychlé blikání (zpracování LLM požadavku).
- `ERROR`: Pomalé blikání (chyba).

```python
led = LedIndicator()
led.set_state("BUSY")
```


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [⚙️ Setup LED Script](../scripts/batch-scripts-reference.md#rpi_setup_ledbat)
- [📂 Source Code](../agent/)

---
Poslední aktualizace: 2025-12-06  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
