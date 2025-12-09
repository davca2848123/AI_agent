# 🧠 Local Models Management

> **Navigace:** [📂 Dokumentace](../README.md) | [⚙️ Konfigurace](../README.md#konfigurace) | [Models Management](models.md)

Tento dokument popisuje, jak agent spravuje a ukládá lokální LLM modely.

<a name="přehled"></a>
## 📋 Přehled

Agent používá knihovnu `llama-cpp-python` pro běh kvantizovaných (GGUF) modelů přímo na zařízení (Raspberry Pi/PC). Modely jsou stahovány z HuggingFace Hubu do lokální cache.

---

<a name="umístění"></a>
## 📂 Umístění

Defaultní cesta k modelům je definována v `config_settings.py`:
```python
MODEL_CACHE_DIR = "./models/"
```

Struktura adresáře:
```
models/
├── .locks/                 # Zámky pro bezpečný stahování
└── models--Qwen--Qwen2.5/  # Cache stažených modelů (HuggingFace formát)
    ├── blobs/              # Samotná data (weights)
    ├── refs/               # Reference na verze
    └── snapshots/          # Konkrétní revize
```

---

<a name="používaný-model"></a>
## 🤖 Používaný Model

Aktuálně nakonfigurovaný model (v `agent/llm.py`):
- **Model ID**: `Qwen/Qwen2.5-0.5B-Instruct-GGUF`
- **Soubor**: `qwen2.5-0.5b-instruct-q4_k_m.gguf`
- **Velikost**: ~350-400 MB
- **Důvod**: Optimalizováno pro rychlou odezvu a nízkou spotřebu paměti na RPi.

---

<a name="správa"></a>
## 🔧 Správa

### První spuštění
Při prvním startu (`LLMClient.__init__`) agent automaticky:
1. Zkontroluje existenci modelu v `models/`.
2. Pokud chybí, stáhne jej pomocí `huggingface_hub`.

### Změna modelu
Pro změnu modelu je nutné upravit `agent/llm.py`:
```python
self.model_id = "path/to/new/model-GGUF"
self.filename = "model-file.gguf"
```
A restartovat agenta. Nový model se stáhne automaticky.

### Čištění
Pro uvolnění místa stačí smazat obsah složky `models/`. Při dalším startu se potřebné soubory stáhnou znovu.


<a name="související"></a>
## 🔗 Související

- [🚀 Deployment Guide](../scripts/deployment-guide.md)
- [🆘 Troubleshooting](../troubleshooting.md)
- [📜 Scripts](../scripts/batch-scripts-reference.md)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
