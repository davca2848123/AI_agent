# Interakční Příkazy

> Příkazy pro interakci s osobností a cíli agenta

## `!mood`

### 📋 Popis
Zobrazí aktuální "náladu" agenta - úroveň nudy (boredom) a kontext.

### ⚙️ Použití
```
!mood
```

### 💡 Co zobraz uje

- **Boredom %** - Aktuální úroveň nudy (0-100%)
- **Status** - Co to znamená
- **Next Action Threshold** - Kdy dojde k akci

### 📝 Příklad
```
User: !mood

Bot: 😴 **Current Mood:**

• Boredom: 67%
• Status: Moderately bored - looking for something to do
• Next autonomous action at: 80%

Agent is slightly restless and may decide to act soon.
```

### 🔧 Boredom Levels

- **0-30%** - Content, no need to act
- **30-60%** - Slightly bored, considering options
- **60-80%** - Moderately bored, looking for action
- **80-100%** - Very bored, will act immediately

---

## `!goals`

### 📋 Popis
Správa cílů agenta - zobrazení, přidání, odebrání.

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

### ⚠️ Poznámky
- Cíle ovlivňují autonomní rozhodování agenta
- Jsou uloženy v paměti
- Agent považuje cíle při choose aktivit

---

## `!config`

### 📋 Popis
Zobrazí aktuální konfiguraci agenta (v budoucnu i modifikace).

### ⚙️ Použití
```
!config
```

### 💡 Co zobrazuje

- Boredom thresholds
- LLM settings
- Discord settings
- Resource tier limits

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

### ⚠️ Poznámky
- Aktuálně read-only
- Modifikace přijde v budoucí verzi

---

**Poslední aktualizace:** 2025-12-02
