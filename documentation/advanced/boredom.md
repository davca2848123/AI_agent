# Boredom Mechanism

> **Navigace:** [📂 Dokumentace](../README.md) | [🔍 Advanced](../README.md#advanced-pokročilé) | [Boredom Mechanism](boredom.md)

> Detailní vysvětlení systému intrinzické motivace (nudy) agenta.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

Boredom Mechanism (mechanismus nudy) je základním stavebním kamenem **autonomního chování** agenta. Tento systém simuluje lidskou potřebu "něco dělat", když není k dispozici externí stimul (příkazy od uživatele). Zajišťuje, že agent nezůstane pasivní, ale sám iniciuje akce, učí se nové věci nebo prozkoumává své okolí.

---

<a name="princip-fungování"></a>
## ⚙️ Princip fungování

Systém funguje na principu **skóre nudy** (Boredom Score), které neustále roste v čase, a **akcí**, které toto skóre snižují.

<a name="boredom-loop"></a>
### 🔄 Boredom Loop

Agent má dedikovanou smyčku (`boredom_loop` v `agent/core.py`), která běží na pozadí:

1.  **Interval:** Každých **5 minut** (300 sekund) se smyčka probudí.
2.  **Decay:** Pokud se nic nestalo, skóre nudy se zvýší o **0.05** (5%).
3.  **Threshold Check:** Pokud skóre překročí **High Threshold (0.4)**, spustí se **Autonomní Akce**.
4.  **Hard Limit:** Skóre nikdy nepřekročí 1.0 (100%).

---

<a name="konfigurace"></a>
## 🔧 Konfigurace

Parametry jsou definovány v `config_settings.py`:

```python
# Boredom System
BOREDOM_INTERVAL = 300  # Sekundy mezi kontrolami (5 min)

BOREDOM_THRESHOLDS = {
    "LOW": 0.2,   # 20% - Agent je spokojený
    "HIGH": 0.4   # 40% - Agent se nudí -> Spouští akci
}

BOREDOM_DECAY_RATE = 0.05  # Růst nudy o 5% za interval
```

---

<a name="stavy-nudy"></a>
## 📊 Stavy Nudy

| Skóre | Stav | Popis |
|-------|------|-------|
| **0.0 - 0.2** | **Content** | Agent je spokojený, nedávno něco dělal. |
| **0.2 - 0.4** | **Restless** | Agent začíná být neklidný, ale ještě nejedná. |
| **> 0.4** | **Bored** | **TRIGGER POINT:** Agent okamžitě iniciuje autonomní akci. |

---

<a name="snižování-nudy"></a>
## 📉 Snižování Nudy

Cílem agenta je udržet nudu nízko. Různé akce snižují nudu o různou hodnotu podle "náročnosti" nebo "zábavnosti":

<a name="typy-akcí"></a>
### Typy akcí a jejich efekt

| Akce | Redukce | Příklad |
|------|---------|---------|
| **Successful Tool Use** | **-0.8** (80%) | Úspěšné použití `web_tool`, `code_tool` atd. |
| **Complex Action** | **-0.5** (50%) | Analýza, reportování, složitější úvaha. |
| **Basic Action** | **-0.2** (20%) | Jednoduchá textová odpověď, status update. |
| **Observation** | **-0.1** (10%) | Zpracování příchozí zprávy na Discordu. |

**Logika:** Použití nástrojů je pro agenta "nejzábavnější" a nejvíce uspokojující, proto nejvíce snižuje nudu.

---

<a name="autonomní-akce"></a>
## 🤖 Autonomní Akce

Když nuda dosáhne trigger pointu (> 0.4), zavolá se `trigger_autonomous_action()`.

<a name="rozhodovací-proces"></a>
### Rozhodovací proces

1.  **Safety Fuse:** Kontrola CPU loadu (>90% skip).
2.  **Learning Mode:** Pokud je aktivní `!learn`, prioritizuje učení z fronty.
3.  **Kontext:** Agent si sestaví kontext (aktuální nuda, cíle, historie).
4.  **LLM Decision:** Zeptá se LLM: *"Based on boredom level X and goals Y, what should I do?"*
    *   Může se rozhodnout použít nástroj (např. vyhledat novinky).
    *   Může se rozhodnout analyzovat své vzpomínky.
    *   Může zkontrolovat aktivitu uživatelů na Discordu.

<a name="force-tool-usage"></a>
### Force Tool Usage
Aby se předešlo smyčce "mluvení naprázdno", agent má počítadlo `actions_without_tools`. Pokud 2x po sobě provede akci bez nástroje, třetí akce má **vynucené** použití nástroje (obvykle `web_tool` pro získání nových informací).

---

<a name="vztah-k-ostatním-systémům"></a>
## 🔗 Vztah k ostatním systémům

- **Goals:** Cíle (`!goals`) ovlivňují, *jakou* akci agent při nudě zvolí.
- **Learning:** Učení nových nástrojů je efektivní způsob redukce nudy.
- **Memory:** Výsledky autonomních akcí se ukládají do paměti (`agent_memory.db`).

---

<a name="související"></a>
## 🔗 Související

- [📖 Autonomous Behavior](../core/autonomous-behavior.md) - Hlavní přehled
- [📖 Config Settings](../configuration/config_settings_reference.md) - Detail konfigurace
- [💬 Příkaz !mood](../commands/interaction.md#mood) - Zobrazení aktuálního stavu
- [🏗️ Architektura](../architecture.md)

---
Poslední aktualizace: 2025-12-06
Verze: Beta - CLOSED
