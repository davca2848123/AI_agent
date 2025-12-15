# 🧠 Agent Memory Manager Script

> **Navigace:** [📂 Dokumentace](../README.md) | [📜 Scripts](../README.md#scripts-advanced) | [Memory Manager](memory-manager.md)

Dokumentace pro interaktivní nástroj `scripts/internal/memory_manager.py`.

<a name="přehled"></a>
## 📋 Přehled

`memory_manager.py` je interaktivní CLI nástroj pro správu SQLite databáze agenta (`agent_memory.db`). Umožňuje prohlížet statistiky, mazat chybné záznamy a provádět údržbu bez nutnosti znalosti SQL.

---

<a name="spouštění"></a>
## 🚀 Spouštění

```bash
# Z kořenového adresáře
python scripts/internal/memory_manager.py
```

<a name="hlavní-menu"></a>
## 🔧 Hlavní Menu

1. **Show statistics**: Zobrazí celkový počet vzpomínek, počty chyb a rozdělení podle typu.
2. **Show error memories**: Vypíše vzpomínky označené jako chyby.
3. **Show memories by type**: Filtrování podle typu (např. `interaction`, `action`, `boredom`).
4. **Show memory by ID**: Detail konkrétního záznamu (včetně JSON metadat).
5. **Search memories**: Fulltextové vyhledávání v obsahu.
6. **Delete error memories**: Hromadné smazání všech error logů (bezpečné čištění).
7. **Delete boredom memories**: Odstranění "nudných" záznamů pro uvolnění místa.
8. **Delete memories by type**: Hromadné smazání dle typu.
9. **Delete memory by ID**: Smazání konkrétního řádku.
10. **Delete duplicate memories**: Najde a odstraní duplicity (ponechá nejstarší).

---

<a name="bezpečnost"></a>
## 🛡️ Bezpečnost

- Nástroj vždy vyžaduje potvrzení (`yes/no`) před smazáním dat.
- Pracuje přímo s `agent_memory.db` v rootu projektu.
- Doporučuje se agenta před použitím vypnout, aby nedošlo k zámkům databáze (i když SQLite WAL mód by měl souběh zvládnout).


<a name="související"></a>
## 🔗 Související

- [⚙️ Konfigurace](../configuration/complete-configuration-guide.md)
- [🆘 Troubleshooting](../troubleshooting.md)
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
