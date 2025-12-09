# 🧹 Sanitizer API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Sanitizer API](utils-sanitizer.md)

Dokumentace pro modul `agent/sanitizer.py`.

<a name="přehled"></a>
## 📋 Přehled

Modul slouží k maskování citlivých údajů (IP adresy, MAC adresy) v logách a výstupech, které agent posílá na Discord nebo ukládá.

---

<a name="funkce"></a>
## 🔧 Funkce

<a name="sanitize_outputtext"></a>
### `sanitize_output(text: str) -> str`

Hlavní a jediná veřejná funkce modulu. Prohledá vstupní text pomocí regulárních výrazů a nahradí citlivé údaje.

#### Podporované maskování:
1. **IPv4 Adresy**: `192.168.1.1` -> `192.168.*.*`
   - Maskuje poslední dva oktety.
2. **IPv6 Adresy**: `2001:0db8:85a3:0000:0000:8a2e:0370:7334` -> `2001:0db8:*:*:*:*`
   - Maskuje druhou polovinu adresy.
   - Podporuje i zkrácený zápis `::`.
3. **MAC Adresy**: `00:1A:2B:3C:4D:5E` -> `00:1A:2B:*:*:*`
   - Maskuje poslední 3 oktety (identifikace zařízení), ponechává OUI (výrobce).

#### Příklad:
```python
from agent.sanitizer import sanitize_output

raw = "Connected to 192.168.0.105 via 00:11:22:33:44:55"
safe = sanitize_output(raw)
print(safe)
# Výstup: "Connected to 192.168.*.* via 00:11:22:*:*:*"
```


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🧠 Core Documentation](../core/)
- [📂 Source Code](../agent/)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
