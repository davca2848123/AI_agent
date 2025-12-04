# 🔧 config_settings.py Reference

> Detailní popis všech konfiguračních možností v souboru `config_settings.py`.

## 📂 Umístění
Soubor se nachází v kořenovém adresáři projektu: `config_settings.py`

---

## 🔧 Core Settings (Základní Nastavení)

### `ADMIN_USER_IDS`
Seznam Discord ID uživatelů, kteří mají administrátorská práva (přístup k `!cmd`, `!restart`, `!debug` atd.).
```python
ADMIN_USER_IDS = [512658574875557889]
```

### `MODEL_CACHE_DIR`
Adresář pro ukládání stažených AI modelů (HuggingFace cache).
```python
MODEL_CACHE_DIR = "./models/"
```

---

## 🌍 Location Settings (Lokace)

### `DEFAULT_LOCATION`
Výchozí lokace pro nástroje jako počasí (`WeatherTool`) nebo čas (`TimeTool`), pokud uživatel nespecifikuje jinak.
```python
DEFAULT_LOCATION = "Frýdek-Místek"
```

---

## ⚡ Resource Management (Správa Zdroju)

Nastavení prahových hodnot pro 4-úrovňový systém správy paměti (RAM).

| Proměnná | Hodnota | Popis |
|----------|---------|-------|
| `RESOURCE_TIER_1_THRESHOLD` | 80% | **Warning:** Spouští se garbage collection a cleanup. |
| `RESOURCE_TIER_2_THRESHOLD` | 90% | **Active:** Omezuje se kontext LLM, maže se cache. |
| `RESOURCE_TIER_3_THRESHOLD` | 95% | **Emergency:** Kill non-essential procesů, maximální úspora. |

```python
RESOURCE_TIER_1_THRESHOLD = 80
RESOURCE_TIER_2_THRESHOLD = 90
RESOURCE_TIER_3_THRESHOLD = 95
```

### Dynamic SWAP
Nastavení pro automatické zvětšování SWAP paměti na Raspberry Pi.
```python
ENABLE_DYNAMIC_SWAP = True  # Zapnuto/Vypnuto
SWAP_MIN_SIZE_GB = 2        # Minimální velikost
SWAP_MAX_SIZE_GB = 8        # Maximální velikost při zátěži
```

### LLM Resource Adaptation
Dynamická změna velikosti kontextového okna (tokenů) podle zatížení systému.
```python
LLM_CONTEXT_NORMAL = 2048   # Běžný provoz
LLM_CONTEXT_TIER1 = 2048    # Při Tier 1 (80% RAM)
LLM_CONTEXT_TIER2 = 1024    # Při Tier 2 (90% RAM) - snížení kvality pro stabilitu
LLM_CONTEXT_TIER3 = 1024    # Při Tier 3 (95% RAM)
```

---

## 🥱 Boredom System (Nuda)

Nastavení autonomního chování agenta, když s ním nikdo neinteraguje.

### `BOREDOM_INTERVAL`
Čas v sekundách mezi kontrolami "nudy". Pokud nikdo nepíše, agent se po této době může sám ozvat nebo něco udělat.
```python
BOREDOM_INTERVAL = 300  # 5 minut
```

### `TOPICS_FILE`
Soubor s tématy, o kterých agent přemýšlí nebo mluví, když se nudí.
```python
TOPICS_FILE = "boredom_topics.json"
```

---

## 🧠 Memory Scoring System (Paměť)

Konfigurace pro ukládání vzpomínek do dlouhodobé paměti. Určuje, co je "důležité".

| Klíč | Hodnota | Popis |
|------|---------|-------|
| `MIN_SCORE_TO_SAVE` | 70 | Minimální skóre (0-100) pro uložení do DB. |
| `ERROR_PENALTY` | -20 | Penalizace, pokud text obsahuje chyby. |
| `KEYWORD_BONUS` | 10 | Body navíc za každé klíčové slovo. |
| `UNIQUENESS_BONUS` | 30 | Body za unikátní informaci. |
| `UNIQUENESS_THRESHOLD` | 0.90 | Hranice podobnosti (90%) pro určení duplicity. |

**Klíčová slova (`KEYWORDS`):**
`def`, `class`, `api`, `návod`, `fix`, `tool`, `python`, `code`

**Blacklist (`BLACKLIST`):**
`error`, `chyba` (slova, která snižují skóre)

---

## 🔒 Security (Bezpečnost)

### `IP_SANITIZATION_ENABLED`
Globální přepínač pro maskování IP adres v logách a Discord zprávách.
```python
IP_SANITIZATION_ENABLED = True
```
Pokud je `True`, všechny IPv4 adresy (např. `192.168.1.20`) budou nahrazeny za `[IP_REDACTED]`.
