#!/usr/bin/env python3
"""
RPI AI Agent - System Health Check
Checks dependencies, permissions, and configuration
Run this before starting the agent to verify everything is set up correctly.
"""

import sys
import os
import importlib
import platform

def check_dependencies():
    """Check all required and optional dependencies"""
    print("=" * 60)
    print("  DEPENDENCY CHECK")
    print("=" * 60)
    print()
    
    required = {
        'discord': 'discord.py',
        'psutil': 'psutil',
        'aiohttp': 'aiohttp',
        'llama_cpp': 'llama-cpp-python',
        'bs4': 'beautifulsoup4',
    }
    
    optional = {
        'duckduckgo_search': 'duckduckgo-search (web_tool)',
        'feedparser': 'feedparser (rss_tool)',
        'deep_translator': 'deep-translator (translate_tool)',
        'wikipediaapi': 'wikipedia-api (wikipedia_tool)',
        'nacl': 'PyNaCl (Discord voice - optional)',
    }
    
    print("Required Dependencies:")
    all_required_ok = True
    for module, package in required.items():
        try:
            importlib.import_module(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING (pip install {package})")
            all_required_ok = False
    
    print()
    print("Optional Dependencies:")
    for module, desc in optional.items():
        try:
            importlib.import_module(module)
            print(f"  ✅ {desc}")
        except ImportError:
            print(f"  ⚠️  {desc} - Not installed (optional)")
    
    print()
    return all_required_ok

def check_files():
    """Check if required files exist"""
    print("=" * 60)
    print("  FILE CHECK")
    print("=" * 60)
    print()
    
    required_files = [
        'agent/core.py',
        'agent/tools.py',
        'agent/commands.py',
        'agent/llm.py',
        'agent/memory.py',
        'agent/discord_client.py',
        'config_settings.py',
    ]
    
    all_files_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_files_ok = False
    
    print()
    return all_files_ok

def check_model():
    """Check if LLM model exists"""
    print("=" * 60)
    print("  MODEL CHECK")
    print("=" * 60)
    print()
    
    # Try to find model file
    possible_paths = [
        'models/gemma-2-2b-jpn-it-Q4_K_M.gguf',
        '../models/gemma-2-2b-jpn-it-Q4_K_M.gguf',
        'gemma-2-2b-jpn-it-Q4_K_M.gguf',
    ]
    
    model_found = False
    for path in possible_paths:
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  ✅ Model found: {path}")
            print(f"     Size: {size_mb:.1f} MB")
            model_found = True
            break
    
    if not model_found:
        print("  ⚠️  LLM model not found in standard locations")
        print("     Check config_settings.py for MODEL_PATH")
    
    print()
    return model_found

def check_permissions():
    """Check file permissions and write access"""
    print("=" * 60)
    print("  PERMISSION CHECK")
    print("=" * 60)
    print()
    
    # Check write access to current directory
    test_file = '.health_check_test'
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("  ✅ Write access to current directory")
    except Exception as e:
        print(f"  ❌ Cannot write to current directory: {e}")
        return False
    
    # Check if agent.log exists and is writable
    if os.path.exists('agent.log'):
        if os.access('agent.log', os.W_OK):
            print("  ✅ agent.log is writable")
        else:
            print("  ⚠️  agent.log exists but not writable")
    else:
        print("  ℹ️  agent.log will be created on first run")
    
    print()
    return True

def check_system_info():
    """Display system information"""
    print("=" * 60)
    print("  SYSTEM INFO")
    print("=" * 60)
    print()
    
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Hostname: {platform.node()}")
    
    # Memory info (if psutil available)
    try:
        import psutil
        mem = psutil.virtual_memory()
        print(f"  RAM: {mem.total / (1024**3):.1f} GB (Available: {mem.available / (1024**3):.1f} GB)")
    except:
        print("  RAM: Unknown (psutil not available)")
    
    print()

def main():
    """Run all health checks"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "RPI AI AGENT HEALTH CHECK" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    check_system_info()
    
    deps_ok = check_dependencies()
    files_ok = check_files()
    model_ok = check_model()
    perms_ok = check_permissions()
    
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print()
    
    if deps_ok and files_ok and perms_ok:
        print("  ✅ ALL CRITICAL CHECKS PASSED")
        if not model_ok:
            print("  ⚠️  Model not found - verify MODEL_PATH in config")
        print()
        print("  You can start the agent with: python main.py")
        return 0
    else:
        print("  ❌ SOME CHECKS FAILED")
        if not deps_ok:
            print("     - Install missing required dependencies")
        if not files_ok:
            print("     - Ensure all agent files are present")
        if not perms_ok:
            print("     - Fix file permissions")
        print()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
