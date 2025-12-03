# LLM Integrace

> Lokální LLM pomocí llama-cpp-python

## 📋 Přehled

Agent používá lokální LLM model (Qwen 2.5) běžící přes `llama-cpp-python` pro rozhodování a generování odpovědí.

---

## LLMClient Class

### 🔧 Inicializace

```python
from agent.llm import LLMClient

llm = LLMClient(
    model_repo="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
    model_filename="qwen2.5-0.5b-instruct-q4_k_m.gguf"
)
```

### 📦 Model Download

Model se automaticky stahuje z Hugging Face:

```python
def _verify_model_cache(self):
    """Verify model is downloaded locally."""
    
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    model_path = os.path.join(cache_dir, f"models--{self.model_repo.replace('/', '--')}")
    
    if not os.path.exists(model_path):
        logger.info(f"Model not found in cache. Downloading {self.model_repo}...")
        
        from huggingface_hub import hf_hub_download
        hf_hub_download(
            repo_id=self.model_repo,
            filename=self.model_filename
        )
```

---

## Model Loading

### 🔧 _load_model()

```python
def _load_model(self, n_ctx=2048, n_threads=4):
    """Loads the LLM model with dynamic parameters."""
    
    if not Llama:
        logger.error("llama-cpp-python not installed!")
        return
    
    # Get model path from cache
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    # ... find model file ...
    
    self.llm = Llama(
        model_path=model_file,
        n_ctx=n_ctx,          # Context window
        n_threads=n_threads,   # CPU threads
        n_batch=512,          # Batch size
        verbose=False
    )
    
    logger.info(f"LLM loaded: {self.model_filename} (ctx={n_ctx}, threads={n_threads})")
```

### ⚙️ Dynamické Parametry

Parametry se mění podle resource tier:

```python
def update_parameters(self, resource_tier: int):
    """Update LLM parameters based on resource tier."""
    
    if resource_tier == 0:  # Normal
        n_ctx, n_threads = 2048, 4
    elif resource_tier == 1:  # Tier 1 (85%)
        n_ctx, n_threads = 1024, 3
    elif resource_tier == 2:  # Tier 2 (90%)
        n_ctx, n_threads = 512, 2
    else:  # Tier 3 (95%)
        n_ctx, n_threads = 256, 1
    
    # Reload model with new params
    self._load_model(n_ctx, n_threads)
```

---

## Generování Odpovědí

### 🔧 generate_response()

```python
response = await llm.generate_response(
    prompt="What is Python?",
    system_prompt="You are a helpful assistant."
)
```

### 💡 Implementace

```python
async def generate_response(self, prompt: str, system_prompt: str = "You are an autonomous AI agent."):
    """Generates a response asynchronously."""
    
    if not self.llm:
        return "LLM not available."
    
    # Build full prompt
    full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
    
    # Run in thread pool (blocking operation)
    def run_inference():
        output = self.llm(
            full_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["User:", "\n\n"],
            echo=False
        )
        return output['choices'][0]['text'].strip()
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, run_inference)
    
    return response
```

### ⚙️ Parametry Generování

| Parametr | Hodnota | Popis |
|----------|---------|-------|
| `max_tokens` | 256 | Max délka odpovědi |
| `temperature` | 0.7 | Kreativita (0-1) |
| `top_p` | 0.9 | Nucleus sampling |
| `stop` | `["User:",  "\n\n"]` | Stop sekvence |

---

## Rozhodování o Akcích

### 🎯 decide_action()

```python
action = await llm.decide_action(
    context="Boredom: 85%, No recent actions",
    past_memories=memories,
    tools_desc=tools_description
)
```

### 🔧 Implementace

```python
async def decide_action(self, context: str, past_memories=None, tools_desc=None):
    """Decides on an action based on context, memories, and tools."""
    
    # Build system prompt
    system_prompt = """You are an autonomous AI agent. 
You can use tools to interact with the world.
Decide what action to take based on your current state."""
    
    if tools_desc:
        system_prompt += f"\n\nAvailable tools:\n{tools_desc}"
    
    # Build prompt
    prompt = f"Current status:\n{context}\n\n"
    
    if past_memories:
        prompt += "Recent memories:\n"
        for m in past_memories[:5]:
            prompt += f"- {m['content']}\n"
    
    prompt += "\nWhat should I do next? Be specific."
    
    # Generate decision
    decision = await self.generate_response(prompt, system_prompt)
    
    return decision
```

---

## Tool Call Parsing

### 🔧 parse_tool_call()

Extrahuje tool call z LLM odpovědi:

```python
tool_call = llm.parse_tool_call(response)
# Returns: {"tool": "web_tool", "params": {"action": "search", "query": "Python"}}
```

### 💡 Implementace

```python
def parse_tool_call(self, response: str):
    """Parses a tool call from the LLM response."""
    
    # Look for TOOL_CALL pattern
    if "TOOL_CALL:" in response:
        lines = response.split('\n')
        tool_name = None
        params = {}
        
        for line in lines:
            if line.startswith("TOOL_CALL:"):
                tool_name = line.split(":", 1)[1].strip()
            elif line.startswith("ARGS:"):
                args_str = line.split(":", 1)[1].strip()
                try:
                    params = json.loads(args_str)
                except:
                    pass
        
        if tool_name:
            return {"tool": tool_name, "params": params}
    
    # Try JSON extraction
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            if 'tool' in data:
                return data
    except:
        pass
    
    return None
```

---

## Provider Type

### 🔧 provider_type Property

```python
@property
def provider_type(self):
    """Returns the type of LLM provider (Local/Cloud)."""
    if self.llm:
        return "Local"
    return "Unavailable"
```

Použití v `!status`:
```
LLM: ✅ Online (245ms) [Local]
```

---

## Error Handling

### ⚠️ Graceful Degradation

```python
if not self.llm:
    logger.warning("LLM not available!")
    return "LLM not available."
```

Pokud LLM selže:
1. Vrátí "LLM not available."
2. Agent použije fallback (např. web search)
3. Admin je notifikován

---

## Performance

### 📊 Typické Latence

| Operace | Latence | Poznámka |
|---------|---------|----------|
| Simple prompt | 200-300ms | Krátká odpověď |
| Decision making | 500-800ms | Komplexní prompt |
| Tool selection | 300-500ms | JSON output |
| Long response | 1-2s | Max tokens |

### ⚡ Optimalizace

**CPU Threads:**
- Více threads = rychlejší, ale více CPU
- Default: 4 threads
- Tier 3: 1 thread (úsporný režim)

**Context Window:**
- Větší window = více paměti
- Default: 2048 tokens
- Tier 3: 256 tokens (minimum)

---

## Model Specs

### 📊 Qwen 2.5-0.5B-Instruct

| Vlastnost | Hodnota |
|-----------|---------|
| Parameters | 0.5 billion |
| Quantization | Q4_K_M (4-bit) |
| File Size | ~330 MB |
| RAM Usage | ~500-800 MB |
| Vocabulary | 151,936 tokens |
| Max Context | 32,768 tokens (omezeno na 2048) |

### 🎯 Proč Qwen 2.5?

- **Malý** - Běží na RPI
- **Rychlý** - 200-500ms latence
- **Chytrý** - Dobré porozumění
- **Multijazyčný** - Čeština + Angličtina
- **Instrukční** - Optimalizovaný pro příkazy

---

## 🔗 Související

- [Autonomous Behavior](autonomous-behavior.md) - Jak agent používá LLM
- [`!ask`](../commands/tools-learning.md#ask) - Příkaz s LLM
- [Resource Manager](resource-manager.md) - Adaptivní parametry LLM

---

**Poslední aktualizace:** 2025-12-02  
**Verze:** 1.0.0
