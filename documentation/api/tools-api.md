# 🛠️ Tools API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Tools API](tools-api.md)

Dokumentace pro systém nástrojů v `agent/tools.py`.

<a name="přehled"></a>
## 📋 Přehled

Modul definuje abstraktní třídu `Tool` a konkrétní implementace nástrojů, které agent používá pro interakci se světem.

<a name="base-class-tool"></a>
## 🔧 Base Class Tool

```python
class Tool(ABC):
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    def description(self) -> str: ...
    
    @abstractmethod
    def execute(self, **kwargs) -> str: ...
```

<a name="metody"></a>
### Metody

<a name="_execute_with_loggingself-kwargs"></a>
#### `_execute_with_logging(self, **kwargs)`
Wrapper pro `execute`, který zajišťuje:
- Logging vstupu a výstupu.
- Ošetření chyb (try-except).
- Měření času běhu.

<a name="dostupné-nástroje"></a>
## 📦 Dostupné Nástroje

<a name="filetool"></a>
### `FileTool`
Práce se souborovým systémem.
- **Akce**: `read`, `write`, `list`, `delete`.
- **Bezpečnost**: Omezeno na workspace adresář.

<a name="webtool"></a>
### `WebTool`
Vyhledávání na internetu a stahování obsahu.
- **Akce**: `search`, `read_page`.

<a name="systemtool"></a>
### `SystemTool`
Informace o systému.
- **Akce**: `info`, `processes`.

<a name="timetool"></a>
### `TimeTool`
Práce s časem.
- **Akce**: `now`, `timer`, `diff`.

<a name="mathtool"></a>
### `MathTool`
Matematické výpočty a převody jednotek.
- **Akce**: `calculate`, `convert`.

<a name="codetool"></a>
### `CodeTool`
Spouštění Python kódu (sandbox).
- **Akce**: `execute`.

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
