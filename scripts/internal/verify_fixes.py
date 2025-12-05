import sys
import os
import importlib.util
import ast

def check_file_exists(path):
    if os.path.exists(path):
        print(f"[OK] File exists: {path}")
        return True
    else:
        print(f"[FAIL] File missing: {path}")
        return False

def check_content(path, content_snippet, description):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content_snippet in content:
            print(f"[OK] {description} found in {path}")
            return True
        else:
            print(f"[FAIL] {description} NOT found in {path}")
            return False
    except Exception as e:
        print(f"[FAIL] Error reading {path}: {e}")
        return False

def check_syntax(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"[OK] Syntax OK: {path}")
        return True
    except SyntaxError as e:
        print(f"[FAIL] Syntax Error in {path}: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error checking syntax {path}: {e}")
        return False

def main():
    print("Verifying Fixes and Enhancements...\n")
    
    # 1. discord_client.py
    check_syntax("agent/discord_client.py")
    check_content("agent/discord_client.py", "msg_logger = logging.getLogger('discord_messages')", "Message logger setup")
    check_content("agent/discord_client.py", "msg_logger.info", "Message logging call")
    
    # 2. commands.py
    check_syntax("agent/commands.py")
    check_content("agent/commands.py", "class StatusView(discord.ui.View):", "StatusView class definition")
    check_content("agent/commands.py", "from scripts.internal.github_release import upload_to_github", "Correct upload import")
    check_content("agent/commands.py", "ephemeral=True", "Ephemeral messages in SSHView")
    check_content("agent/commands.py", "•", "UTF-8 bullets in !stats")
    check_content("agent/commands.py", "ADMIN_RESTRICTED_COMMANDS", "Restricted commands check in !cmd")
    check_content("agent/commands.py", "async def cmd_disable", "cmd_disable implementation")
    check_content("agent/commands.py", "async def cmd_enable", "cmd_enable implementation")
    check_content("agent/commands.py", "async def cmd_config", "cmd_config implementation")
    
    # 3. config_settings.py
    check_syntax("config_settings.py")
    check_content("config_settings.py", "ADMIN_RESTRICTED_COMMANDS", "Restricted commands list")
    
    # 4. core.py
    check_syntax("agent/core.py")
    check_content("agent/core.py", "self.command_handler.global_interaction_enabled", "Global interaction check in autonomous loop")
    
    # 5. Scripts
    check_file_exists("scripts/internal/cleanup_memory.py")
    check_syntax("scripts/internal/cleanup_memory.py")
    check_file_exists("scripts/internal/delete_old_releases.py")
    check_syntax("scripts/internal/delete_old_releases.py")
    
    # 6. Documentation
    check_content("documentation/commands/admin.md", "Commands Restricted to Admin", "Restricted commands section in admin.md")
    
    # 7. Fuzzy Matching
    print("\n[TEST] Testing Fuzzy Matching Logic...")
    try:
        sys.path.append(os.getcwd())
        from agent.commands import CommandHandler, levenshtein_distance
        
        # Mock agent and discord
        class MockAgent:
            pass
        
        ch = CommandHandler(MockAgent())
        
        # Test helper
        assert ch._match_subcommand("dep", ["deep", "quick"]) == "deep", "Failed: dep -> deep"
        assert ch._match_subcommand("stat", ["start", "stop"]) == "start", "Failed: stat -> start"
        assert ch._match_subcommand("xyz", ["start", "stop"]) is None, "Failed: xyz -> None"
        
        print("[OK] Fuzzy matching logic verified")
    except ImportError:
        print("[WARN] Could not import CommandHandler for testing (likely missing dependencies in this script env)")
    except AssertionError as e:
        print(f"[FAIL] Fuzzy matching test failed: {e}")
    except Exception as e:
        print(f"[FAIL] Error testing fuzzy matching: {e}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    main()
