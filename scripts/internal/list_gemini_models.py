import google.generativeai as genai
import os
import sys

# Add project root to path to find config_secrets
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    import config_secrets
    if not hasattr(config_secrets, 'GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY found in config_secrets.py but is empty or missing.")
        sys.exit(1)
        
    genai.configure(api_key=config_secrets.GEMINI_API_KEY)
    
    print("🔍 Listing available Gemini models...")
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ {m.name}")
            found = True
            
    if not found:
        print("❌ No models found that support 'generateContent'. Check your API key permissions.")
        
except ImportError:
    print("❌ Failed to import config_secrets or google.generativeai. Run this from the project root or check installation.")
except Exception as e:
    print(f"❌ Error listing models: {e}")
