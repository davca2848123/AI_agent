# 🧠 LLM Integration API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [LLM Integration](llm-integration.md) | [🔍 Hledat](../INDEX.md#vyhledavani)

Dokumentace pro `LLMClient` v `agent/llm.py`.

<a name="přehled"></a>
## 📋 Přehled

Zajišťuje komunikaci s lokálním LLM (přes `llama-cpp-python`) nebo cloudovým modelem. Řeší načítání modelu, generování odpovědí a parsování tool calls.

<a name="třída-llmclient"></a>
## 🔧 Třída LLMClient

```python
class LLMClient:
    def __init__(self, model_repo: str, model_filename: str)
```

<a name="hlavní-metody"></a>
### Hlavní Metody

<a name="generate_responseself-prompt-str-system_prompt-str"></a>
#### `generate_response(self, prompt: str, system_prompt: str)`
Vygeneruje textovou odpověď na prompt.
- **prompt**: Vstupní text.
- **system_prompt**: Instrukce pro model.

<a name="decide_actionself-context-str-past_memories-list-tools_desc-str"></a>
#### `decide_action(self, context: str, past_memories: list, tools_desc: str)`
Rozhodne o dalším kroku agenta na základě kontextu.
- Vrací text popisující akci nebo volání nástroje.

<a name="parse_tool_callself-response-str"></a>
#### `parse_tool_call(self, response: str)`
Extrahuje volání nástroje z textové odpovědi LLM.
- **Návratová hodnota**: Dict `{'tool': 'name', 'params': {...}}` nebo `None`.

<a name="update_parametersself-resource_tier-int"></a>
#### `update_parameters(self, resource_tier: int)`
Upraví parametry modelu (např. context window, threads) podle aktuálního vytížení systému (Resource Manager).

<a name="související"></a>
## 🔗 Související
- [📖 LLM Integration Guide](../core/llm-integration.md) - Detailní popis modelu, parametrů a fallbacků

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání

