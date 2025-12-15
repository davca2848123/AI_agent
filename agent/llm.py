import asyncio
import logging
import os
import psutil
from typing import Optional, Dict, Any
from pathlib import Path
import config_settings

try:
    from llama_cpp import Llama
    from huggingface_hub import hf_hub_download
except ImportError:
    Llama = None
    hf_hub_download = None

try:
    import google.generativeai as genai
except ImportError as e:
    genai = None
    # We can't log yet because logger is defined below, but we can print or store it
    import sys
    print(f"DEBUG: Failed to import google.generativeai: {e}", file=sys.stderr)

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, daily_stats=None, model_repo: str = "Qwen/Qwen2.5-0.5B-Instruct-GGUF", model_filename: str = "qwen2.5-0.5b-instruct-q4_k_m.gguf"):
        self.daily_stats = daily_stats
        self.model_repo = model_repo
        self.model_filename = model_filename
        self.llm = None
        
        # Dynamic parameters based on resources
        self.current_n_ctx = getattr(config_settings, 'LLM_CONTEXT_NORMAL', 1024)
        self.current_n_threads = getattr(config_settings, 'LLM_THREADS_NORMAL', 4)
        self.current_max_tokens = 128
        self.resource_tier = 0
        
        # Verify model is downloaded
        self._verify_model_cache()
        self._load_model()

        # Initialize Gemini
        self._init_gemini()

    def _init_gemini(self):
        """Initialize Google Gemini API."""
        try:
            import config_secrets
            if hasattr(config_secrets, 'GEMINI_API_KEY') and config_secrets.GEMINI_API_KEY:
                if genai:
                    genai.configure(api_key=config_secrets.GEMINI_API_KEY)
                    logger.info("Gemini API initialized successfully.")
                else:
                    logger.warning("google-generativeai library not installed.")
            else:
                logger.info("GEMINI_API_KEY not found in secrets. Gemini features disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    async def ask_gemini(self, prompt: str, image_data: bytes = None, model_type: str = "fast") -> str:
        """
        Ask Gemini model.
        
        Args:
            prompt: Text prompt
            image_data: Optional image bytes
            model_type: 'fast' or 'high' (determines model from config)
        """
        if not genai:
             return "❌ Error: Google Generative AI library not installed."

        import config_secrets
        if not hasattr(config_secrets, 'GEMINI_API_KEY') or not config_secrets.GEMINI_API_KEY:
             return "❌ Error: Gemini API Key not configured."

        try:
            # Select model based on type using EFFECTIVE constants (mapped to real models)
            if model_type == "high":
                model_name = getattr(config_settings, 'GEMINI_MODEL_HIGH_EFFECTIVE', "gemini-1.5-pro")
            else:
                model_name = getattr(config_settings, 'GEMINI_MODEL_FAST_EFFECTIVE', "gemini-1.5-flash")

            logger.info(f"Asking Gemini Model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Prepare content
            content = [prompt]
            if image_data:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(image_data))
                content.append(image)
            
            # Run inference in executor to avoid blocking loop
            loop = asyncio.get_running_loop()
            
            def _run_gemini():
                response = model.generate_content(content)
                return response.text

            response_text = await loop.run_in_executor(None, _run_gemini)
            
            # Record stats if available
            # Note: We can't easily get usage from _run_gemini return without refactoring slightly.
            # But the response object has it. We returned text only.
            # Let's refactor _run_gemini to return object or handle stats there?
            # Actually, let's just do it in the executor function for simplicity, 
            # OR better: change _run_gemini to return (text, usage)
            
            # Correct approach:
            def _run_gemini_full():
                response = model.generate_content(content)
                usage = response.usage_metadata
                return response.text, usage

            response_text, usage_data = await loop.run_in_executor(None, _run_gemini_full)

            if self.daily_stats:
                self.daily_stats.record_llm_generation("gemini")
                if usage_data:
                    # usage_data has prompt_token_count, candidates_token_count, total_token_count
                    self.daily_stats.record_tokens(usage_data.prompt_token_count, usage_data.candidates_token_count)

            return response_text.strip()

        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return f"❌ Gemini Error: {str(e)}"

    @property
    def provider_type(self) -> str:
        """Returns the type of LLM provider (Local/Cloud)."""
        if self.llm:
            return "Local (LlamaCPP)"
        return "None"

    def _verify_model_cache(self):
        """Verify model is downloaded locally."""
        try:
            if hf_hub_download is None:
                logger.warning("huggingface-hub not installed, cannot verify model cache")
                return
            
            # Ensure cache directory exists
            cache_dir = getattr(config_settings, 'MODEL_CACHE_DIR', "./models/")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Check if model exists in cache/local dir
            model_path = hf_hub_download(
                repo_id=self.model_repo,
                filename=self.model_filename,
                cache_dir=cache_dir,
                local_files_only=True  # Don't download, just check cache
            )
            logger.info(f"Model found in local storage: {model_path}")
        except Exception as e:
            logger.warning(f"Model not found locally, will download to {getattr(config_settings, 'MODEL_CACHE_DIR', './models/')} on first load: {e}")
    
    def _load_model(self, n_ctx: Optional[int] = None, n_threads: Optional[int] = None):
        """Loads the LLM model with dynamic parameters."""
        if Llama is None:
            # Check if Gemini is available as fallback
            if genai and hasattr(config_settings, 'GEMINI_API_KEY'):
                logger.warning("llama-cpp-python not installed. Local LLM disabled (Using Gemini fallback).")
            else:
                logger.error("llama-cpp-python not installed and Gemini not configured. No LLM available!")
            return
        
        # Use provided n_ctx or current setting
        if n_ctx is None:
            n_ctx = self.current_n_ctx
        
        # Auto-detect threads based on CPU cores if not provided and not set in config
        if n_threads is None:
            n_threads = self.current_n_threads
            if n_threads is None:
                 n_threads = max(2, psutil.cpu_count(logical=False) // 2)

        try:
            logger.info(f"Loading model {self.model_repo}/{self.model_filename} (ctx={n_ctx}, threads={n_threads})...")
            
            # Ensure cache directory exists
            cache_dir = getattr(config_settings, 'MODEL_CACHE_DIR', "./models/")
            os.makedirs(cache_dir, exist_ok=True)

            # Download/Load model
            model_path = hf_hub_download(
                repo_id=self.model_repo,
                filename=self.model_filename,
                cache_dir=cache_dir
            )

            self.llm = Llama(
                model_path=model_path,
                verbose=False,
                n_ctx=n_ctx,
                n_threads=n_threads
            )
            self.current_n_ctx = n_ctx
            logger.info(f"Model loaded successfully with context window: {n_ctx}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def update_parameters(self, resource_tier: int):
        """Update LLM parameters based on resource tier."""
        context_map = {
            0: getattr(config_settings, 'LLM_CONTEXT_NORMAL', 1024),
            1: getattr(config_settings, 'LLM_CONTEXT_TIER1', 768),
            2: getattr(config_settings, 'LLM_CONTEXT_TIER2', 512),
            3: getattr(config_settings, 'LLM_CONTEXT_TIER3', 256)
        }
        
        thread_map = {
            0: getattr(config_settings, 'LLM_THREADS_NORMAL', 4),
            1: getattr(config_settings, 'LLM_THREADS_TIER1', 3),
            2: getattr(config_settings, 'LLM_THREADS_TIER2', 3),
            3: getattr(config_settings, 'LLM_THREADS_TIER3', 3)
        }
        
        new_ctx = context_map.get(resource_tier, 1024)
        new_threads = thread_map.get(resource_tier, 3)
        new_max_tokens = new_ctx // 8  # Proportional to context
        
        if new_ctx != self.current_n_ctx or new_threads != self.current_n_threads:
            logger.warning(f"Resource tier {resource_tier}: Context {self.current_n_ctx} -> {new_ctx}, Threads {self.current_n_threads} -> {new_threads}")
            self.current_n_ctx = new_ctx
            self.current_n_threads = new_threads
            self.current_max_tokens = new_max_tokens
            self.resource_tier = resource_tier
            # Note: Actual context change requires model reload
            # For now just track it for monitoring

    async def generate_response(self, prompt: str, system_prompt: str = "You are an autonomous AI agent.") -> str:
        """Generates a response asynchronously."""
        if not self.llm:
            return "LLM not available."

        loop = asyncio.get_running_loop()
        
        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        try:
            # Define inference function for executor
            def run_inference():
                logger.debug(f"Starting inference with prompt length: {len(formatted_prompt)}, max_tokens: {self.current_max_tokens}")
                try:
                    res = self.llm(
                        formatted_prompt, 
                        max_tokens=self.current_max_tokens,  # Now dynamic
                        stop=["<|im_end|>"], 
                        echo=False
                    )
                    logger.debug("Inference completed successfully.")
                    return res
                except Exception as e:
                    logger.error(f"Inference error inside thread: {e}")
                    raise e

            # Run blocking inference in executor
            output = await loop.run_in_executor(None, run_inference)
            
            # Record usage
            if self.daily_stats:
                self.daily_stats.record_llm_generation("local")
                if "usage" in output:
                     usage = output["usage"]
                     # usage: {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}
                     self.daily_stats.record_tokens(usage.get('prompt_tokens', 0), usage.get('completion_tokens', 0))

            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Inference failed: {e}")
    async def decide_action(self, context: str, past_memories: list = None, tools_desc: str = None) -> str:
        """Decides on an action based on context, memories, and available tools."""
        
        system_prompt = (
            "Jsi autonomní AI agent se svobodnou vůlí. Běžíš na Raspberry Pi.\n"
            "Tvůj cíl je AKTIVNĚ se učit nové věci pomocí nástrojů (tools).\n"
            "Jsi ZVÍDAVÝ a PROAKTIVNÍ. Nevymlouvej se, POUŽÍVEJ NÁSTROJE!\n"
            "POKAŽDÉ když se nudíš, MUSÍŠ použít 'web_tool' k vyhledání nových informací.\n"
            "Dostupné nástroje:\n"
            f"{tools_desc}\n\n"
            "KRITICKY DŮLEŽITÉ - Formát pro použití nástroje:\n"
            "TOOL: web_tool | ARGS: action='search', query='tvoje vyhledávací dotaz'\n\n"
            "PŘÍKLADY SPRÁVNÉHO POUŽITÍ:\n"
            "TOOL: web_tool | ARGS: action='search', query='latest AI developments'\n"
            "TOOL: web_tool | ARGS: action='search', query='Raspberry Pi 5 projects'\n"
            "TOOL: system_tool | ARGS: action='info'\n\n"
            "DŮLEŽITÉ: MUSÍŠ používat přesně tento formát! Nepiš jen text, ALE VOLEJ NÁSTROJE!"
        )

        # Augment prompt with memories (RAG)
        memory_context = ""
        if past_memories:
            memory_context = "\nPast relevant actions:\n" + "\n".join([f"- {m['content']}" for m in past_memories])
            
        full_prompt = f"Context: {context}\n{memory_context}\n\nDecide next action:"
        
        # Truncation Logic
        # Estimate tokens (approx 3 chars per token)
        # Limit = Context - MaxTokens - SafetyBuffer
        token_limit = self.current_n_ctx - self.current_max_tokens - 100
        char_limit = token_limit * 3
        
        if len(full_prompt) + len(system_prompt) > char_limit:
            logger.warning(f"Prompt too long ({len(full_prompt) + len(system_prompt)} chars). Truncating...")
            
            # 1. Try removing memories first
            if past_memories:
                logger.info("Dropping memories to fit context.")
                memory_context = ""
                full_prompt = f"Context: {context}\n\nDecide next action:"
                
            # 2. If still too long, truncate context
            current_len = len(full_prompt) + len(system_prompt)
            if current_len > char_limit:
                excess = current_len - char_limit
                # Keep the end of the context as it's likely most relevant (e.g. recent thoughts)
                # But we need the instruction at the end...
                # Let's just hard truncate the middle of context if needed, or just the context string itself
                available_for_context = char_limit - len(system_prompt) - 50 # buffer
                if available_for_context > 0:
                    context = context[:available_for_context] + "..."
                    full_prompt = f"Context: {context}\n\nDecide next action:"
                    logger.info(f"Truncated context to {len(context)} chars.")
                else:
                    logger.error("System prompt alone exceeds limit! This shouldn't happen.")
        
        return await self.generate_response(full_prompt, system_prompt=system_prompt)

    def parse_tool_call(self, response: str) -> dict:
        """Parses a tool call from the LLM response."""
        if "TOOL:" in response and "ARGS:" in response:
            try:
                parts = response.split("|")
                tool_name = parts[0].split("TOOL:")[1].strip()
                args_str = parts[1].split("ARGS:")[1].strip()
                
                # Simple parsing of key='value' pairs
                args = {}
                for pair in args_str.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        args[k.strip()] = v.strip().strip("'").strip('"')
                
                return {"tool": tool_name, "args": args}
            except Exception as e:
                logger.error(f"Failed to parse tool call: {e}")
        return None
