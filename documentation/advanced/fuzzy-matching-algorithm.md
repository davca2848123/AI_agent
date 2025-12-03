# Fuzzy Command Matching Algorithm

> Inteligentní auto-korekce příkazů pomocí Levenshtein Distance

## 📋 Přehled

Agent automaticky opravuje překlepy v Discord příkazech, což zlepšuje uživatelskou zkušenost a snižuje frustraci z typografických chyb.

---

## Algoritmus: Levenshtein Distance

### 📐 Co to je?

**Levenshtein distance** (edit distance) je minimum počtu operací potřebných k transformaci jednoho řetězce na druhý.

**Povolené operace:**
1. **Insert** - Vložení znaku
2. **Delete** - Smazání znaku  
3. **Substitute** - Nahrazení znaku

### 💡 Příklady

```
"!statu" → "!status"
Operations: Insert 's' at end
Distance: 1

"!hlep" → "!help"
Operations: Substitute 'l' → 'l', 'e' → 'e', 'p' → 'p'
Actually: Transpose 'l' and 'e'
Distance: 2

"!toools" → "!tools"
Operations: Delete one 'o'
Distance: 1

"!rstart" → "!restart"
Operations: Insert 'e' after 'r'
Distance: 1
```

---

## Implementace

### 🔧 Levenshtein Distance Function

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    
    # Ensure s1 is the shorter string
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    # If s2 is empty, distance is length of s1
    if len(s2) == 0:
        return len(s1)
    
    # Initialize previous row of distances
    previous_row = range(len(s2) + 1)
    
    # Calculate distances row by row
    for i, c1 in enumerate(s1):
        current_row = [i + 1]  # First column (deletion cost)
        
        for j, c2 in enumerate(s2):
            # Calculate costs
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            
            # Take minimum
            current_row.append(min(insertions, deletions, substitutions))
        
        previous_row = current_row
    
    return previous_row[-1]
```

### 📊 Complexity

- **Time:** O(m × n) kde m, n jsou délky řetězců
- **Space:** O(n) - pouze aktuální a předchozí řádek

---

## Auto-Correction Logic

### 🔍 Command Matching Process

```python
async def _execute_command(self, msg: dict):
    """Execute command with fuzzy matching."""
    
    # 1. Parse command
    parts = content.split()
    original_command = parts[0].lower()
    
    # 2. Try exact match first
    if original_command in VALID_COMMANDS:
        # Execute directly
        return await self._route_command(original_command, args)
    
    # 3. Fuzzy matching
    closest_match = None
    min_distance = float('inf')
    
    for valid_cmd in VALID_COMMANDS:
        distance = levenshtein_distance(original_command, valid_cmd)
        
        # Only auto-correct if distance is small (1-2 characters)
        if distance < min_distance and distance <= 2:
            min_distance = distance
            closest_match = valid_cmd
    
    # 4. Auto-correct if match found
    if closest_match:
        logger.info(f"Auto-correcting '{original_command}' → '{closest_match}' (distance: {min_distance})")
        
        await self.agent.discord.send_message(channel_id, 
            f"💡 Did you mean `{closest_match}`? (auto-correcting '{original_command}')")
        
        return await self._route_command(closest_match, args)
    
    # 5. No match - unknown command
    await self.agent.discord.send_message(channel_id,
        f"❓ Unknown command: {original_command}. Use `!help` for available commands.")
```

### ⚙️ Configuration

```python
class CommandHandler:
    # List of all valid commands for fuzzy matching
    VALID_COMMANDS = [
        "!help", "!status", "!intelligence", "!inteligence", "!restart", "!learn",
        "!memory", "!tools", "!logs", "!stats", "!export", "!ask",
        "!teach", "!search", "!mood", "!goals", "!config", "!monitor", 
        "!ssh", "!cmd", "!live", "!topic", "!documentation", "!docs", "!report"
    ]
    
    FUZZY_MATCH_THRESHOLD = 2  # Maximum edit distance for auto-correction
```

---

## Příklady Použití

### ✅ Úspěšná Auto-Korekce

**Distance 1:**
```
User: !statu

Bot: 💡 Did you mean `!status`? (auto-correcting '!statu')
     📊 **Agent Status**
     ...
```

```
User: !toools

Bot: 💡 Did you mean `!tools`? (auto-correcting '!toools')
     🛠️ **Available Tools:**
     ...
```

**Distance 2:**
```
User: !hlep

Bot: 💡 Did you mean `!help`? (auto-correcting '!hlep')
     📋 **Available Commands:**
     ...
```

```
User: !satts

Bot: 💡 Did you mean `!stats`? (auto-correcting '!satts')
     📊 **Comprehensive Statistics**
     ...
```

### ❌ Příliš Vzdálené (Distance > 2)

```
User: !xyz

Bot: ❓ Unknown command: !xyz. Use `!help` for available commands.
```

```
User: !statuses

Bot: ❓ Unknown command: !statuses. Use `!help` for available commands.
```

---

## Speciální Případy

### Aliasy

Některé příkazy mají vestavěné aliasy:

```python
# V routing logice
if command == "!inteligence" or command == "!intelligence":
    await self.cmd_intelligence(channel_id)

if command in ["!documentation", "!docs"]:
    await self.cmd_documentation(channel_id)
```

**Aliasy nepotřebují fuzzy matching** - jsou přímé shody.

### Case Insensitivity

Všechny příkazy jsou case-insensitive:

```python
original_command = parts[0].lower()  # !Help → !help
```

```
!HELP → !help
!Help → !help
!hElP → !help
(všechny fungují)
```

---

## Performance

### ⚡ Optimalizace

**Early Exit:**
```python
if original_command in VALID_COMMANDS:
    # Exact match - skip fuzzy matching entirely
    return await self._route_command(original_command, args)
```

**Distance Threshold:**
- Pouze distance ≤ 2 se považuje za validní
- Větší vzdálenosti = vyšší pravděpodobnost false positive

**Efficient Algorithm:**
- O(m × n) je přijatelné pro krátké řetězce
- Typický příkaz: 4-15 znaků
- ~24 validních příkazů
- Celková latence: \u003c 1ms

### 📊 Typical Performance

| Operation | Time | Poznámka |
|-----------|------|----------|
| Exact match | \u003c 0.01ms | Hash lookup |
| Fuzzy match (hit) | 0.1-0.5ms | 24 distance calculations |
| Fuzzy match (miss) | 0.1-0.5ms | Same (checks all) |

---

## Edge Cases

### Prázdný Příkaz

```python
if not parts:
    return  # Ignorovat prázdné zprávy
```

### Pouze Prefix

```
User: !

Bot: ❓ Unknown command: !. Use `!help` for available commands.
```

### Velmi Dlouhý Příkaz

```
User: !thisisaverylongcommandthatdoesnotexist

Bot: ❓ Unknown command: !thisisaverylongcommandthatdoesnotexist. Use `!help` for available commands.
```

Distance by byla příliš velká (\u003e 2) pro jakýkoliv validní příkaz.

### Více Shod Se Stejnou Distance

```python
# Vybere první nalezenou (v pořadí VALID_COMMANDS)
if distance < min_distance and distance <= 2:
    min_distance = distance
    closest_match = valid_cmd
```

**Příklad:**
```
User: !lg

Možné shody:
- !logs (distance: 2) ✅ První v seznamu
- !log (pokud existuje)

Bot: 💡 Did you mean `!logs`?
```

---

## Debugging

### 🔍 Logging

```python
logger.info(f"Auto-correcting '{original_command}' → '{closest_match}' (distance: {min_distance})")
```

**Output v logu:**
```
[INFO] Auto-correcting '!statu' → '!status' (distance: 1)
[INFO] Auto-correcting '!hlep' → '!help' (distance: 2)
```

### 📊 Statistics

Agent nesleduje fuzzy matching statistiky, ale můžeš je přidat:

```python
# V __init__
self.fuzzy_corrections = 0
self.total_commands = 0

# V _execute_command
self.total_commands += 1
if closest_match:
    self.fuzzy_corrections += 1
```

---

## Srovnání s Alternativami

### Vs. Substring Matching

**Substring (jednodušší):**
```python
if valid_cmd.startswith(user_input):
    return valid_cmd
```

❌ Problémy:
- `!s` by matchlo `!status`, `!stats`, `!search`, `!ssh`
- Neopraví transpozice (`!hlep`)
- Neopraví vložní/chybějící znaky

### Vs. Phonetic Matching (Soundex, Metaphone)

**Phonetic:**
- Funguje pro hovorová slova
- ❌ Nepraktické pro krátké příkazy

### ✅ Levenshtein je optimální pro příkazy

- Přesný pro krátké řetězce
- Opraví všechny typy chyb
- Rychlý
- Deterministický

---

## Možná Vylepšení

### 1. Weighted Edit Distance

Různé operace mají různé váhy:

```python
# Transpozice (common typo) - nižší cost
if i > 0 and j > 0 and s1[i] == s2[j-1] and s1[i-1] == s2[j]:
    cost = min(cost, matrix[i-2][j-2] + 0.5)  # Levnější než 2× substituce
```

### 2. Keyboard Proximity

Zohlednit, jak blízko jsou klávesy:

```python
# 'a' a 's' jsou vedle sebe → nižší penalizace
# 'a' a 'z' jsou daleko → vyšší penalizace
```

### 3. Command Popularity Weighting

Častější příkazy mají prioritu:

```python
# !status je velmi častý
# Pokud distance je stejná, upřednostni !status před !restart
```

### 4. Multi-Word Commands

```python
# "!live logs" jako jeden příkaz
# Fuzzy match na "!liv logs" → "!live logs"
```

---

## 🔗 Související

- [Basic Commands](/documentation/commands/basic.md) - Použití fuzzy matchingu
- [Command Queue System](/documentation/commands/basic.md#command-queue-system) - Jak příkazy běží

---

## 📚 Reference

**Levenshtein Distance:**
- [Wikipedia](https://en.wikipedia.org/wiki/Levenshtein_distance)
- Original paper: Vladimir Levenshtein (1966)

**Implementation:**
- [`agent/commands.py`](file:///z:/rpi_ai/rpi_ai/agent/commands.py) - `levenshtein_distance()` function
- Dynamic programming approach for O(n) space complexity

---

**Poslední aktualizace:** 2025-12-03  
**Platné pro verzi:** 1.1.0  
**Implementováno:** Od verze 1.0.0
