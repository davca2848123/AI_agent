# Interakční Příkazy

> **Navigace:** [📂 Dokumentace](../README.md) | [💬 Příkazy](../README.md#commands-příkazy) | [Interakční příkazy](interaction.md)

> Příkazy pro interakci s osobností a cíli agenta.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Tyto příkazy umožňují sledovat náladu agenta, spravovat jeho cíle a prohlížet konfiguraci.

> Příkazy pro interakci s osobností a cíli agenta.
> **Verze:** Beta - CLOSED (Updated 2025-12-11)

---

<a name="ask"></a>
## `!ask`

<a name="popis"></a>
### 📋 Popis
Hlavní příkaz pro dotazy na AI. Používá **Smart Routing** pro výběr nejvhodnějšího modelu.

<a name="logic"></a>
### 🧠 Smart Routing
Agent automaticky rozhoduje, který model použije:

1.  **Gemini (Cloud)** - Použije se pro:
    - Složité dotazy (> 50 znaků)
    - Klíčová slova (`code`, `analyze`, `navrhni`, ...)
    - Zpracování obrázků
    - Pokud lokální model není dostupný (fallback)
    
2.  **Local LLM (Offline)** - Použije se pro:
    - Jednoduché, krátké dotazy
    - Chatování když není potřeba hluboká analýza

<a name="funkce"></a>
### ✨ Funkce
- **File Export**: Pokud je odpověď příliš dlouhá (> 1900 znaků), agent ji automaticky uloží do souboru (`.txt` nebo `.md`) a pošle jako přílohu.
- **Vision**: Podporuje obrázky jako přílohy k dotazu.

---

<a name="mood"></a>
## `!mood`

<a name="popis"></a>
### 📋 Popis
Zobrazí aktuální "náladu" agenta - úroveň nudy (boredom) a kontext.

<a name="použití"></a>
### ⚙️ Použití
```
!mood
```

<a name="co-zobraz-uje"></a>
### 💡 Co zobraz uje

- **Boredom %** - Aktuální úroveň nudy (0-100%)
- **Status** - Co to znamená
- **Next Action Threshold** - Kdy dojde k akci

<a name="příklad"></a>
### 📝 Příklad
```
User: !mood

Bot: 😴 **Current Mood:**

• Boredom: 67%
• Status: Moderately bored - looking for something to do
• Next autonomous action at: 80%

Agent is slightly restless and may decide to act soon.
```

<a name="boredom-levels"></a>
### 🔧 Boredom Levels

- **0-30%** - Content, no need to act
- **30-60%** - Slightly bored, considering options
- **60-80%** - Moderately bored, looking for action
- **80-100%** - Very bored, will act immediately

<a name="související"></a>
### 🔗 Související
- [📖 Autonomous Behavior](../core/autonomous-behavior.md) - Jak funguje nuda

---



<a name="config"></a>
## `!config`

<a name="popis"></a>
### 📋 Popis
Zobrazí aktuální konfiguraci agenta (Settings, LLM params, Boredom thresholds).

<a name="použití"></a>
### ⚙️ Použití
```
!config
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje
- **Boredom System** (Thresholds, Decay rates)
- **LLM Settings** (Model path, Context window, Token limits)
- **Discord Settings** (Activity status, Channels)
- **Resource Limits** (CPU/RAM tiers)

<a name="příklad"></a>
### 📝 Příklad
```
User: !config

Bot: ⚙️ **Current Configuration:**
     • `BOREDOM_THRESHOLD_HIGH`: 0.4
     • `LLM_MODEL`: qwen-2.5-0.5b
     • `MAX_TOKENS`: 256
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Read-only zobrazení `config_settings.py` proměnných
- Hesla a klíče jsou filtrovány

---

<a name="monitor"></a>
## `!monitor`

<a name="popis"></a>
### 📋 Popis
Monitoruje systémové zdroje (CPU, RAM, Disk, Swap) v reálném čase.

<a name="použití"></a>
### ⚙️ Použití

**Snapshot (okamžitě):**
```
!monitor
```

**Live monitoring:**
```
!monitor <duration>
```

<a name="formáty-délky"></a>
### 🔧 Formáty délky
- `30` - 30 sekund
- `2m` - 2 minuty
- `1h` - 1 hodina

<a name="příklady"></a>
### 📝 Příklady

**Snapshot:**
```
User: !monitor

Bot: 📊 **System Resources:**
CPU: ▓▓▓▓░░░░░░ 45%
RAM: ▓▓▓▓▓▓▓░░░ 72%
```

<a name="související"></a>
### 🔗 Související
- [`!stats`](basic.md#stats) - Detailní statistiky
- [`!live logs`](data-management.md#live-logs) - Live logy


---

<a name="souhrn"></a>
## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!mood` | Zobraz náladu | `!mood` |
| `!config` | Zobrazí konfiguraci | `!config` |
| `!monitor` | Resource monitor | `!monitor 30` |


<a name="související"></a>
## 🔗 Související

- [📋 Všechny příkazy](../SUMMARY.md#commands-api)
- [🏗️ Command Architecture](../architecture.md#command-layer)
- [🆘 Troubleshooting](../troubleshooting.md#command-errors)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
