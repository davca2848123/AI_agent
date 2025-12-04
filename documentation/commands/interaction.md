# Interakční Příkazy

> **Navigace:** [📂 Dokumentace](../README.md) | [💬 Příkazy](../README.md#commands-příkazy) | [Interakční příkazy](interaction.md) | [🔍 Hledat](../INDEX.md#vyhledavani)

> Příkazy pro interakci s osobností a cíli agenta.
> **Verze:** Alpha

---

<a name="přehled"></a>
## 📋 Přehled

Tyto příkazy umožňují sledovat náladu agenta, spravovat jeho cíle a prohlížet konfiguraci.

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

<a name="goals"></a>
## `!goals`

<a name="popis"></a>
### 📋 Popis
Správa cílů agenta - zobrazení, přidání, odebrání.

<a name="použití"></a>
### ⚙️ Použití

**Zobrazit cíle:**
```
!goals
```

**Přidat cíl:**
```
!goals add <popis cíle>
```

**Odebrat cíl:**
```
!goals remove <číslo>
```

**Vymazat všechny:**
```
!goals clear
```

<a name="příklady"></a>
### 📝 Příklady

**Seznam cílů:**
```
User: !goals

Bot: 🎯 **Current Goals:**

1. Learn all available tools
2. Improve response time
3. Help users with Python questions

You can add/remove goals with:
• `!goals add <goal>`
• `!goals remove <number>`
```

**Přidat cíl:**
```
User: !goals add Monitor system health daily

Bot: ✅ Goal added: "Monitor system health daily"
     Total goals: 4
```

**Odebrat cíl:**
```
User: !goals remove 2

Bot: ✅ Removed goal: "Improve response time"
     Remaining goals: 3
```

**Vymazat vše:**
```
User: !goals clear

Bot: 🗑️ All goals cleared.
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Cíle ovlivňují autonomní rozhodování agenta
- Jsou uloženy v paměti
- Agent považuje cíle při choose aktivit

---

<a name="config"></a>
## `!config`

<a name="popis"></a>
### 📋 Popis
Zobrazí aktuální konfiguraci agenta (v budoucnu i modifikace).

<a name="použití"></a>
### ⚙️ Použití
```
!config
```

<a name="co-zobrazuje"></a>
### 💡 Co zobrazuje

- Boredom thresholds
- LLM settings
- Discord settings
- Resource tier limits

<a name="příklad"></a>
### 📝 Příklad
```
User: !config

Bot: ⚙️ **Agent Configuration:**

**Boredom System:**
• Base threshold: 0.8
• Decay rate: 0.02/min

**LLM:**
• Model: Qwen 2.5-0.5B
• Context window: 2048
• Max tokens: 256

🚧 Configuration modification coming soon!
```

<a name="poznámky"></a>
### ⚠️ Poznámky
- Aktuálně read-only
- Modifikace přijde v budoucí verzi

---

<a name="souhrn"></a>
## 📊 Souhrn

| Příkaz | Účel | Příklad |
|--------|------|---------|
| `!mood` | Zobraz náladu | `!mood` |
| `!goals` | Správa cílů | `!goals add Learn Python` |
| `!config` | Zobraz config | `!config` |

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
