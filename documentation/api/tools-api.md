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
- **Akce**: `read`, `write`, `list_files`.
- **Bezpečnost**: Omezeno na `agent_workspace` adresář.

<a name="webtool"></a>
### `WebTool`
Vyhledávání na internetu a stahování obsahu.
- **Akce**: `search`, `read`.
- **Lokalizace**: Prioritizuje `cs`, `sk`, `en` obsah.
- **Automatizace**: Při `read` ukládá faktické shrnutí do paměti jako `web_knowledge`.

<a name="systemtool"></a>
### `SystemTool`
Informace o systému.
- **Akce**: `info`, `process_list`.

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

<a name="notetool"></a>
### `NoteTool`
Správa textových poznámek.
- **Akce**: `add`, `list`, `search`.


<a name="databasetool"></a>
### `DatabaseTool`
Provádění SQL dotazů (pouze SELECT) nad pamětí agenta.
- **Akce**: `execute`.

<a name="rsstool"></a>
### `RSSTool`
Čtení RSS kanálů.
- **Akce**: `read_feed`.

<a name="translatetool"></a>
### `TranslateTool`
Překlad textu pomocí Google Translate.
- **Akce**: `translate_text`.

<a name="wikipediatool"></a>
### `WikipediaTool`
Vyhledávání na Wikipedii.
- **Akce**: `search`, `summary`.

<a name="discordactivitytool"></a>
### `DiscordActivityTool`
Monitoring aktivit uživatelů na Discordu.
- **Akce**: `get_activities`.
- **Enrichment**: Automatický web search a uložení infa o aktivitě (`activity_knowledge`) probíhá **na pozadí** (asynchronně), aby neblokoval diagnostiku.


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🧠 Core Documentation](../core/)
- [📂 Source Code](../agent/)

---
Poslední aktualizace: 2025-12-06  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
