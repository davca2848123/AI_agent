import logging
import asyncio
from typing import Optional
import time
import psutil
import datetime
import re
import subprocess
import platform
import aiohttp
import config_settings
import os
import json
try:
    import discord
except ImportError:
    discord = None

try:
    from pyngrok import ngrok
except ImportError:
    ngrok = None

try:
    from scripts.internal.github_release import upload_to_github
except ImportError:
    upload_to_github = None

logger = logging.getLogger(__name__)
tools_logger = logging.getLogger('agent.tools')  # For tool-related logging

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

class SSHView(discord.ui.View):
    def __init__(self, ssh_command, net_use_command):
        super().__init__(timeout=None)
        self.ssh_command = ssh_command
        self.net_use_command = net_use_command

    @discord.ui.button(label="Zkopírovat SSH", style=discord.ButtonStyle.success, emoji="📋")
    async def copy_ssh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Admin check
        if interaction.user.id not in config_settings.ADMIN_USER_IDS:
             await interaction.response.send_message("⛔ Access Denied.", ephemeral=True)
             return
        await interaction.response.send_message(f"```\n{self.ssh_command}\n```", ephemeral=True)

    @discord.ui.button(label="Zkopírovat Net Use", style=discord.ButtonStyle.secondary, emoji="🪟")
    async def copy_net_use(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Admin check
        if interaction.user.id not in config_settings.ADMIN_USER_IDS:
             await interaction.response.send_message("⛔ Access Denied.", ephemeral=True)
             return
        await interaction.response.send_message(f"```\n{self.net_use_command}\n```", ephemeral=True)

    @discord.ui.button(label="Zobrazit detailní statistiky", style=discord.ButtonStyle.primary, emoji="📊")
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the response first to avoid timeout
        await interaction.response.defer(ephemeral=True)
        # Execute !stats command in the channel (visible to everyone)
        # Note: cmd_stats sends a public message. If we want it ephemeral, we'd need to change cmd_stats.
        # For now, let's keep stats public but maybe restrict button?
        # User request was specifically about SSH commands visibility.
        await self.command_handler.cmd_stats(interaction.channel_id)

# === Documentation Views ===

import io

async def check_interaction_allowed(interaction, view) -> bool:
    """
    Check if interaction is allowed based on global_interaction_enabled.
    Returns True if allowed, False if blocked (and sends error message).
    Admins always bypass.
    """
    # Admin bypass
    if interaction.user.id in config_settings.ADMIN_USER_IDS:
        return True
    
    # Try to get command_handler from various sources
    command_handler = None
    if hasattr(view, 'command_handler'):
        command_handler = view.command_handler
    elif hasattr(view, 'parent_view') and hasattr(view.parent_view, 'command_handler'):
        command_handler = view.parent_view.command_handler
    
    # If we found command_handler, check global_interaction_enabled
    if command_handler and not command_handler.global_interaction_enabled:
        await interaction.response.send_message(
            "⛔ **Interakce zakázána** - Agent je v režimu \"disabled\".",
            ephemeral=True
        )
        return False
    
    return True


async def send_clean_md_file(interaction, path):
    """Helper to read MD file, strip HTML, and send as file."""
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Remove specific Navigation lines (custom pattern in your docs)
            # Removes lines starting with > **Navigace or > [Index] or similar common navigation patterns
            cleaned_content = re.sub(r'(?m)^[> ]*\*\*Navigace:?\*\*.*$', '', content)
            cleaned_content = re.sub(r'(?m)^.*\|.*\|.*$', '', cleaned_content) # Separator based nav
            
            # 2. Remove HTML Anchors specifically likely <a name="..."></a> which might be missed if simple regex is too weak
            # This handles <a ...></a> pairs even if empty content
            cleaned_content = re.sub(r'<a\s+[^>]*>.*?</a>', '', cleaned_content, flags=re.DOTALL)
            
            # 3. Remove ALL remaining HTML tags (self closing or standard)
            cleaned_content = re.sub(r'<[^>]+>', '', cleaned_content)
            
            # 4. Remove internal documentation links [Text](path/to/doc.md) replacement
            def link_replacer(match):
                text = match.group(1)
                link = match.group(2)
                if link.startswith('http'):
                     return match.group(0)
                return text

            cleaned_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replacer, cleaned_content)
            
            # 5. Remove horizontal rules that might have separated nav
            cleaned_content = re.sub(r'(?m)^---+\s*$', '', cleaned_content)
            
            # 6. Trim multiple newlines matched
            cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content).strip()
            
            # Create in-memory file
            fp = io.BytesIO(cleaned_content.encode('utf-8'))
            filename = os.path.basename(path)
            
            await interaction.response.send_message(file=discord.File(fp, filename=filename), ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Soubor {path} nebyl nalezen.", ephemeral=True)
    except Exception as e:
        # Avoid crashing if interaction already responded
        try:
             await interaction.response.send_message(f"❌ Chyba při odesílání: {e}", ephemeral=True)
        except:
             logger.error(f"Failed to send error message for {path}: {e}")

class CommandsView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @discord.ui.button(label="📋 Basic", style=discord.ButtonStyle.secondary)
    async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/commands/basic.md")

    @discord.ui.button(label="🎓 Tools & Learning", style=discord.ButtonStyle.secondary)
    async def tools(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/commands/tools-learning.md")

    @discord.ui.button(label="💾 Data", style=discord.ButtonStyle.secondary)
    async def data(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/commands/data-management.md")

    @discord.ui.button(label="💬 Interaction", style=discord.ButtonStyle.secondary)
    async def interaction_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/commands/interaction.md")

    @discord.ui.button(label="⚙️ Admin", style=discord.ButtonStyle.secondary)
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/commands/admin.md")

class CoreView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @discord.ui.button(label="🤖 Autonomous", style=discord.ButtonStyle.secondary)
    async def autonomous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/core/autonomous-behavior.md")

    @discord.ui.button(label="🧠 Memory", style=discord.ButtonStyle.secondary)
    async def memory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/core/memory-system.md")

    @discord.ui.button(label="🗣️ LLM", style=discord.ButtonStyle.secondary)
    async def llm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/core/llm-integration.md")

    @discord.ui.button(label="💻 Resources", style=discord.ButtonStyle.secondary)
    async def resources(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/core/resource-manager.md")
    
    @discord.ui.button(label="🔌 Discord", style=discord.ButtonStyle.secondary)
    async def discord_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/core/discord-client.md")

    @discord.ui.button(label="📊 Reporting", style=discord.ButtonStyle.secondary)
    async def reporting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/core/reporting.md")

class AdvancedView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @discord.ui.button(label="🔍 Fuzzy Matching", style=discord.ButtonStyle.secondary)
    async def fuzzy_matching(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/advanced/fuzzy-matching-algorithm.md")

class ScriptsView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @discord.ui.button(label="🚀 Deployment", style=discord.ButtonStyle.secondary)
    async def deployment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/scripts/deployment-guide.md")

    @discord.ui.button(label="📜 Batch Scripts", style=discord.ButtonStyle.secondary)
    async def batch_scripts(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/scripts/batch-scripts-reference.md")

    @discord.ui.button(label="🧹 Maintenance", style=discord.ButtonStyle.secondary)
    async def maintenance(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/scripts/maintenance.md")

    @discord.ui.button(label="🧠 Memory Manager", style=discord.ButtonStyle.secondary)
    async def memory_manager(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/scripts/memory-manager.md")

class ConfigurationView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @discord.ui.button(label="🔧 Settings Reference", style=discord.ButtonStyle.secondary)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/configuration/config_settings_reference.md")

    @discord.ui.button(label="🔐 Secrets Template", style=discord.ButtonStyle.secondary)
    async def secrets(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/configuration/config_secrets_template.md")

    @discord.ui.button(label="🌍 Env Variables", style=discord.ButtonStyle.secondary)
    async def env_vars(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/configuration/environment_variables.md")

    @discord.ui.button(label="⚙️ Customization Guide", style=discord.ButtonStyle.secondary)
    async def guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/configuration/customization-guide.md")

    @discord.ui.button(label="📚 Complete Guide", style=discord.ButtonStyle.primary)
    async def complete_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/configuration/complete-configuration-guide.md")

class ApiView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=300)
        self.parent_view = parent_view

    @discord.ui.button(label="🧠 Agent Core", style=discord.ButtonStyle.secondary)
    async def agent_core(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/api/agent-core.md")

    @discord.ui.button(label="💾 Memory System", style=discord.ButtonStyle.secondary)
    async def memory_system(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await self._send_file(interaction, "documentation/api/memory-system.md")

    @discord.ui.button(label="🛠️ Tools API", style=discord.ButtonStyle.secondary)
    async def tools_api(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await self._send_file(interaction, "documentation/api/tools-api.md")

    @discord.ui.button(label="🔌 Discord Client", style=discord.ButtonStyle.secondary)
    async def discord_client(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await self._send_file(interaction, "documentation/api/discord-client.md")

    @discord.ui.button(label="🗣️ LLM Integration", style=discord.ButtonStyle.secondary)
    async def llm_integration(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await self._send_file(interaction, "documentation/api/llm-integration.md")

class DocumentationView(discord.ui.View):
    def __init__(self, command_handler):
        super().__init__(timeout=300)
        self.command_handler = command_handler

    @discord.ui.button(label="📖 Overview", style=discord.ButtonStyle.primary)
    async def overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/OVERVIEW.md")

    @discord.ui.button(label="🏛️ Architecture", style=discord.ButtonStyle.secondary)
    async def architecture(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/architecture.md")

    @discord.ui.button(label="🔍 Index", style=discord.ButtonStyle.secondary)
    async def index(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/INDEX.md")

    @discord.ui.button(label="📋 API Tasklist", style=discord.ButtonStyle.secondary)
    async def summary(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/SUMMARY.md")

    @discord.ui.button(label="💬 Commands", style=discord.ButtonStyle.secondary)
    async def commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.send_message("Vyber kategorii příkazů:", view=CommandsView(self), ephemeral=True)

    @discord.ui.button(label="🛠️ Tools", style=discord.ButtonStyle.secondary)
    async def tools(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/tools/all-tools.md")

    @discord.ui.button(label="🧠 Core", style=discord.ButtonStyle.secondary)
    async def core(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.send_message("Vyber sekci Core:", view=CoreView(self), ephemeral=True)

    @discord.ui.button(label="📜 Scripts", style=discord.ButtonStyle.secondary)
    async def scripts(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.send_message("Vyber Scripts dokumentaci:", view=ScriptsView(self), ephemeral=True)

    @discord.ui.button(label="🎓 Advanced", style=discord.ButtonStyle.secondary)
    async def advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.send_message("Vyber Advanced téma:", view=AdvancedView(self), ephemeral=True)

    @discord.ui.button(label="🆘 Troubleshooting", style=discord.ButtonStyle.danger)
    async def troubleshooting(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await send_clean_md_file(interaction, "documentation/troubleshooting.md")

    @discord.ui.button(label="⚙️ Configuration", style=discord.ButtonStyle.secondary)
    async def configuration(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.send_message("Vyber Configuration dokumentaci:", view=ConfigurationView(self), ephemeral=True)

    @discord.ui.button(label="📚 API Reference", style=discord.ButtonStyle.secondary)
    async def api_ref(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.send_message("Vyber API dokumentaci:", view=ApiView(self), ephemeral=True)
    
    @discord.ui.button(label="🌐 Zapnout Web Interface", style=discord.ButtonStyle.success, row=2)
    async def start_web_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_interaction_allowed(interaction, self):
            return
        await interaction.response.defer(ephemeral=True)
        await self.command_handler.cmd_web(interaction.channel_id, [], interaction.user.id)

class StatusView(discord.ui.View):
    def __init__(self, agent):
        super().__init__(timeout=None)
        self.agent = agent
        
    @discord.ui.button(label="🔄 Refresh Status", style=discord.ButtonStyle.primary, custom_id="refresh_status")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Get fresh status
        status_text = await self.agent.command_handler.get_status_text()
        
        # Update message
        await interaction.message.edit(content=status_text, view=self)

class CommandHandler:
    """Handles Discord bot commands."""
    
    # List of all valid commands for fuzzy matching
    VALID_COMMANDS = [
        # Basic commands
        "!help", "!status", "!intelligence", "!intel", "!inteligence", "!restart", "!learn",
        "!memory", "!tools", "!logs", "!stats", "!export", "!ask",
        "!teach", "!search", "!mood", "!goals", "!config", "!monitor", "!ssh", "!cmd", "!live", "!topic",
        "!documentation", "!docs", "!report", "!web", "!upload", "!debug", "!info",
        "!enable", "!disable",
        
        # !web subcommands
        "!web start", "!web stop", "!web restart",
        
        # !ssh subcommands
        "!ssh start", "!ssh stop", "!ssh status",
        
        # !monitor subcommands  
        "!monitor cpu", "!monitor ram", "!monitor disk", "!monitor network",
        
        # !debug subcommands
        "!debug quick", "!debug deep", "!debug tools", "!debug compile",
        
        # !goals subcommands
        "!goals add", "!goals remove", "!goals clear",
        
        # !topic subcommands
        "!topic add", "!topic remove", "!topic clear", "!topic list",
        
        # !learn subcommands
        "!learn all", "!learn stop", "!learn queue",
        
        # !export subcommands
        "!export history", "!export memory", "!export stats", "!export all",
        
        # !live subcommands
        "!live logs",
        
        # !memory subcommands
        "!memory dump"
    ]
    
    def __init__(self, agent):
        self.agent = agent
        self.ngrok_process = None  # Track running ngrok process
        self.queue = asyncio.Queue()
        self.is_processing = False # Track if a command is currently being processed
        self.worker_task = None # Will be set by start()
        self.is_running = False # Will be set by start()
        self.last_user_command = None # Track last command for reporting
        self.global_interaction_enabled = True # Control global interaction (admin only override)

    def _match_subcommand(self, raw_input: str, valid_options: list) -> Optional[str]:
        """Helper to match subcommand with fuzzy logic."""
        if raw_input in valid_options:
            return raw_input
            
        best_match = None
        min_distance = float('inf')
        
        for option in valid_options:
            dist = levenshtein_distance(raw_input, option)
            if dist < min_distance and dist <= 2: # Max 2 typos for subcommands
                min_distance = dist
                best_match = option
                
        return best_match

    def start(self):
        """Start the command processing worker."""
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("CommandHandler worker started.")

    async def _worker_loop(self):
        """Background task to process commands from queue."""
        logger.info("Command queue worker running...")
        while self.is_running:
            try:
                # Wait for command
                msg = await self.queue.get()
                
                # Process it
                try:
                    self.is_processing = True # Set processing flag
                    await self._execute_command(msg)
                except Exception as e:
                    logger.error(f"Error executing command: {e}", exc_info=True)
                    channel_id = msg.get('channel_id')
                    if channel_id:
                        await self.agent.discord.send_message(channel_id, f"✖️ Internal error executing command: {e}")
                finally:
                    self.is_processing = False # Clear processing flag
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in command worker loop: {e}")
                await asyncio.sleep(1)

    async def handle_command(self, msg: dict):
        """Enqueue a command for processing."""
        q_size = self.queue.qsize()
        channel_id = msg.get('channel_id')
        
        # Send thinking indicator - DISABLED globally to prevent spam
        # specific commands will handle it themselves
        # if channel_id:
        #     await self.agent.discord.send_message(channel_id, "🤔 Thinking...")
        
        # Add to queue
        await self.queue.put(msg)
        
        # Feedback if queue is busy
        # Feedback if queue is busy
        q_size = self.queue.qsize()  # Get specific queue size first
        if 'id' in msg:
            try:
                if q_size > 0:
                    logger.info(f"Command queued (Position: {q_size + 1})")
                await self.agent.discord.add_reaction(msg['id'], msg['channel_id'], "👀")
            except Exception as e:
                logger.warning(f"Failed to add reaction: {e}")
        else:
             logger.warning("Message ID missing, skipping reaction.")
             if q_size > 0:
                  logger.info(f"Command queued (Position: {q_size + 1})")

    async def _execute_command(self, msg: dict):
        """Execute the command logic (internal)."""
        content = msg['content'].strip()
        channel_id = msg['channel_id']
        author = msg['author']
        author_id = msg.get('author_id', 0)
        
        # Check global interaction lock
        if not self.global_interaction_enabled:
            # Allow admins to bypass
            if author_id not in config_settings.ADMIN_USER_IDS:
                logger.info(f"Ignoring command from {author} (Interaction Disabled)")
                return

        logger.info(f"Executing command from {author} ({author_id}): {content}")
        
        # Track command for reporting (unless it's !report itself)
        if not content.lower().startswith("!report"):
            self.last_user_command = {
                "user": author,
                "user_id": author_id,
                "command": content,
                "timestamp": time.time()
            }
            # Clear message history for new command
            if hasattr(self.agent.discord, 'clear_message_history'):
                self.agent.discord.clear_message_history()
        
        # Parse command and args
        parts = content.split()
        original_command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Try fuzzy matching if command not recognized
        # First try matching the full command with first argument (for subcommands)
        full_command = f"{original_command} {args[0]}" if args else original_command
        command = original_command
        
        # Check if full command with subcommand matches
        if full_command in self.VALID_COMMANDS:
            # Found exact match for command + subcommand
            command = original_command
            # Keep args as is
        elif command not in self.VALID_COMMANDS:
            # Fuzzy Matching Logic: Find best match among all valid commands
            candidates = []
            
            # 1. Check ALL commands against full input (e.g. "!ssh start")
            for valid_cmd in self.VALID_COMMANDS:
                dist = levenshtein_distance(full_command, valid_cmd)
                threshold = config_settings.FUZZY_MATCH_DISTANCE_SUBCOMMANDS if ' ' in valid_cmd else config_settings.FUZZY_MATCH_DISTANCE_BASE_COMMANDS
                
                if dist <= threshold:
                    candidates.append({
                        "cmd": valid_cmd,
                        "distance": dist,
                        "type": "full"
                    })

            # 2. Check BASE commands against base input (e.g. "!ssh")
            # Only if the valid command is a base command (no spaces)
            for valid_cmd in self.VALID_COMMANDS:
                if ' ' not in valid_cmd:
                    dist = levenshtein_distance(command, valid_cmd)
                    if dist <= config_settings.FUZZY_MATCH_DISTANCE_BASE_COMMANDS:
                        candidates.append({
                            "cmd": valid_cmd,
                            "distance": dist,
                            "type": "base" 
                        })
            
            # Sort candidates:
            # 1. By Distance (Ascending)
            # 2. By Type (Full match preferred over Base match if distance is equal)
            # 3. By Length (Longer matches preferred? No, shorter distance is key)
            if candidates:
                # Sort by distance first
                candidates.sort(key=lambda x: x['distance'])
                
                # Get the best one
                best_candidate = candidates[0]
                
                # If there are multiple with same minimal distance, prefer 'full' (subcommand) match if input had args
                best_candidates = [c for c in candidates if c['distance'] == best_candidate['distance']]
                if len(best_candidates) > 1 and args:
                     # Check if any is 'full' type
                    full_matches = [c for c in best_candidates if c['type'] == 'full']
                    if full_matches:
                        best_candidate = full_matches[0]
                
                closest_match = best_candidate['cmd']
                min_distance = best_candidate['distance']
            else:
                closest_match = None
                
            if closest_match:
                # Auto-correct the command
                corrected_input = full_command if ' ' in closest_match else original_command
                logger.info(f"Auto-correcting '{corrected_input}' → '{closest_match}' (distance: {min_distance})")
                await self.agent.discord.send_message(channel_id, 
                    f"💊 Did you mean `{closest_match}`? (auto-correcting '{corrected_input}')")
                
                # If closest match has subcommand, split it
                if ' ' in closest_match:
                    match_parts = closest_match.split(' ', 1)
                    command = match_parts[0]
                    # Adjust args: new subcommand + remaining args
                    # If original had args, we replace the first arg (which was part of fuzzy match) with correct subcommand
                    sub_arg = match_parts[1]
                    if args:
                         args[0] = sub_arg
                    else:
                         args = [sub_arg]
                else:
                    command = closest_match
        
        # Route to appropriate handler
        if command == "!help":
            await self.cmd_help(channel_id)
        elif command == "!status":
            await self.cmd_status(channel_id)
        elif command in ["!inteligence", "!intelligence", "!intel"]:
            await self.cmd_intelligence(channel_id)
        elif command == "!restart":
            await self.cmd_restart(channel_id, author, author_id)
        elif command == "!learn":
            await self.cmd_learn(channel_id, args)
        elif command == "!memory":
            await self.cmd_memory(channel_id)
        elif command == "!tools":
            await self.cmd_tools(channel_id)
        elif command == "!mood":
            await self.cmd_mood(channel_id)
        elif command == "!goals":
            await self.cmd_goals(channel_id, args, author_id)
        elif command == "!config":
            await self.cmd_config(channel_id, args, author_id)
        elif command == "!monitor":
            await self.cmd_monitor(channel_id, args)
        elif command == "!ssh":
            await self.cmd_ssh(channel_id, author_id, args)
        elif command == "!cmd":
            await self.cmd_cmd(channel_id, ' '.join(args), author_id)
        elif command == "!info":
            await self.cmd_info(channel_id)
        elif command == "!logs":
            await self.cmd_logs(channel_id, args)
        elif command == "!stats":
            await self.cmd_stats(channel_id)
        elif command == "!export":
            await self.cmd_export(channel_id, args)
        elif command == "!ask":
            await self.cmd_ask(channel_id, ' '.join(args))
        elif command == "!teach":
            await self.cmd_teach(channel_id, ' '.join(args))
        elif command == "!search":
            await self.cmd_search(channel_id, ' '.join(args))
        elif command == "!debug":
            await self.cmd_debug(channel_id, args, author_id)
        elif command == "!live":
            await self.cmd_live(channel_id, args)
        elif command == "!shutdown":
            await self.cmd_shutdown(channel_id, author_id)
        elif command == "!topic":
            await self.cmd_topic(channel_id, args, author_id)
        elif command in ["!documentation", "!docs"]:
            await self.cmd_documentation(channel_id)
        elif command == "!report":
            await self.cmd_report(channel_id, author_id)
        elif command == "!web":
             await self.cmd_web(channel_id, args, author_id)
        elif command == "!upload":
            await self.cmd_upload(channel_id, author_id)
        elif command == "!disable":
            await self.cmd_disable(channel_id, author_id)
        elif command == "!enable":
            await self.cmd_enable(channel_id, author_id)
        else:
            await self.agent.discord.send_message(channel_id, f"❓ Unknown command: {command}. Use `!help` for available commands.")
    
    async def cmd_info(self, channel_id: int):
        """Display detailed system and agent information (Matching Web Dashboard)."""
        import platform
        import psutil
        import time
        import datetime
        import config_settings
        import discord
        import re

        # --- Helper Functions from WebInterface ---
        def get_os_info():
            sys_name = platform.system()
            release = platform.release().replace("+rpt-rpi-v8", "")
            distro = ""
            if sys_name == "Linux":
                try:
                    if os.path.exists('/etc/os-release'):
                        with open('/etc/os-release') as f:
                            content = f.read()
                            match = re.search(r'^ID=["\']?([^"\'\n\r]+)["\']?', content, re.MULTILINE)
                            if match:
                                distro = f"({match.group(1)}) "
                except:
                    pass
            return f"{sys_name} {distro}{release}"

        def get_hardware_info():
            try:
                # Raspberry Pi check
                if os.path.exists('/proc/device-tree/model'):
                    with open('/proc/device-tree/model', 'r') as f:
                        model = f.read().strip()
                        # Simplify: "Raspberry Pi 4 Model B Rev 1.5" -> "Raspberry Pi 4B"
                        simple_model = re.sub(r' Model ([A-Z]) Rev [\d\.]+', r'\1', model)
                        total_ram_gb = round(psutil.virtual_memory().total / (1024**3))
                        return f"{simple_model} ({total_ram_gb}GB)"
                return platform.machine()
            except:
                return "Unknown Hardware"

        def get_llm_display_name():
            # Parses model filename to friendly name
            filename = getattr(self.agent.llm, 'model_filename', 'Unknown')
            if filename == 'Unknown':
                 return getattr(self.agent.llm, 'model_repo', 'Unknown')
            
            try:
                name = filename.lower()
                if 'qwen' in name:
                    clean_name = name.replace('.gguf', '').replace('-q4_k_m', '')
                    if 'qwen' in clean_name:
                        parts = clean_name.split('-')
                        base = parts[0]
                        version_match = re.search(r'qwen([\d\.]+)', base)
                        ver = version_match.group(1) if version_match else ""
                        rest = " - ".join(parts[1:])
                        return f"QWEN {ver} {rest}".strip()
                return filename
            except:
                return filename

        def to_gb(bytes_val):
            return f"{bytes_val / (1024**3):.1f} GB"

        # --- Data Collection ---

        # 1. System Resources
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        ram_used = to_gb(ram.used)
        ram_total = to_gb(ram.total)
        disk_used = to_gb(disk.used)
        disk_total = to_gb(disk.total)

        system_resources = (
            f"**CPU:** {cpu_percent}%\n"
            f"**RAM:** {ram.percent}% ({ram_used} / {ram_total})\n"
            f"**Disk:** {disk.percent}% ({disk_used} / {disk_total})"
        )

        # 2. System Info
        os_text = get_os_info()
        hw_text = get_hardware_info()
        python_ver = platform.python_version()
        llm_model = get_llm_display_name()
        project_ver = getattr(config_settings, 'AGENT_VERSION', 'Beta - CLOSED')

        system_info = (
            f"**OS:** {os_text} running on {hw_text}\n"
            f"**Python:** {python_ver}\n"
            f"**LLM Model:** {llm_model}\n"
            f"**Project Version:** {project_ver}"
        )

        # 3. Agent Status
        uptime_seconds = int(time.time() - self.agent.start_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        boredom = f"{self.agent.boredom_score * 100:.1f}%"
        tools_learned = len([t for t, c in self.agent.tool_usage_count.items() if c > 0])
        total_tools = len(self.agent.tools.tools)
        
        agent_status = (
            f"**Status:** 🟢 Running\n"
            f"**Boredom:** {boredom}\n"
            f"**Uptime:** {uptime_str}\n"
            f"**Tools Learned:** {tools_learned} / {total_tools}"
        )
        
        # 4. Environment / Discord
        latency = f"{self.agent.discord.client.latency * 1000:.0f}ms" if self.agent.discord.client else "N/A"
        local_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Build Embed ---
        embed = discord.Embed(title="ℹ️ System & Agent Information", color=0x5865F2) # Discord Blurple to match UI? Or Green 0x34A853? Keeping Green/Blue.
        
        # Row 1: Status & Resources (Side by Side if possible, but distinct blocks)
        # Discord fields inline=True puts them side-by-side. 3 fit in a row on desktop.
        
        # The web has: Status Card, Resources Card, System Info Card.
        # User requested cutting down dynamic/stats info (Status & Resources) from !info
        # Leaving only static info.
        
        # System Info needs to be wide for long strings
        embed.add_field(name="System Info", value=system_info, inline=False)

        # Extra info (Discord/Env) - Maybe combine into footer or small field
        env_info = f"**Discord Latency:** {latency}\n**Local Time:** {local_time}"
        embed.add_field(name="Environment", value=env_info, inline=False)
        
        embed.add_field(name="About", value="Created in collaboration with [Antigravity](https://antigravity.google/)\nPowered by Discord, ngrok, and local LLMs.", inline=False)
        
        await self.agent.discord.send_message(channel_id, embed=embed)

    async def cmd_status(self, channel_id: int):
        """Simple status command - shows if agent is running."""
        uptime = time.time() - self.agent.start_time
        uptime_str = f"{int(uptime // 60)}m {int(uptime % 60)}s"
        
        status_msg = (
            f"🤖 **Agent Status**\n\n"
            f"**Status:** 🟢 Running\n"
            f"**Uptime:** {uptime_str}\n"
            f"**Boredom:** {self.agent.boredom_score * 100:.1f}%"
        )
        
        await self.agent.discord.send_message(channel_id, status_msg)

    async def cmd_web(self, channel_id: int, args: list, author_id: int):
        """Start, stop, or restart the web interface. Usage: !web [start|stop|restart]"""
        import discord
        import config_settings

        # Admin check
        if author_id not in config_settings.ADMIN_USER_IDS:
             await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can manage the web interface.")
             return
        
        # Parse subcommand
        raw_subcommand = args[0].lower() if args else "start"
        valid_subcommands = ["start", "stop", "restart"]
        
        subcommand = self._match_subcommand(raw_subcommand, valid_subcommands)
        
        if not subcommand:
            await self.agent.discord.send_message(
                channel_id,
                "❓ **Usage:** `!web [start|stop|restart]`\n\n"
                "- **start** - Spustit web interface (výchozí)\n"
                "- **stop** - Zastavit web interface a ngrok tunel\n"
                "- **restart** - Restartovat web interface"
            )
            return
            
        if subcommand != raw_subcommand:
             await self.agent.discord.send_message(channel_id, f"💡 Did you mean `{subcommand}`? Executing...")
        
        # Handle stop
        if subcommand == "stop":
            await self.agent.discord.send_message(channel_id, "🛑 Stopping web interface...")
            self.agent.web_server.stop()
            await self.agent.discord.send_message(
                channel_id,
                "✅ **Web Interface Stopped**\n\nNgrok tunel byl ukončen."
            )
            return
        
        # Handle restart
        if subcommand == "restart":
            await self.agent.discord.send_message(channel_id, "🔄 Restarting web interface...")
            # Use gentle stop to preserve SSH tunnel if possible
            self.agent.web_server.disconnect_web_tunnel()
            
            # Kill any processes holding web interface ports (5001-5051)
            try:
                import psutil
                import os
                
                killed_pids = set()
                current_pid = os.getpid()
                
                for port in range(5001, 5051):
                    for conn in psutil.net_connections():
                        if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                            if conn.pid and conn.pid != current_pid and conn.pid not in killed_pids:
                                try:
                                    logger.warning(f"Killing process {conn.pid} holding port {port}")
                                    proc = psutil.Process(conn.pid)
                                    proc.terminate() # SIGTERM
                                    killed_pids.add(conn.pid)
                                except psutil.NoSuchProcess:
                                    pass
                                except Exception as e:
                                    logger.error(f"Failed to kill process {conn.pid}: {e}")
                
                if killed_pids:
                    logger.info(f"Killed {len(killed_pids)} processes holding web ports")
                    await asyncio.sleep(0.5) # Give OS time to release ports
            except Exception as e:
                logger.error(f"Error cleaning up ports: {e}")
            
            # Reload module to pick up code changes
            try:
                import importlib
                import agent.web_interface
                importlib.reload(agent.web_interface)
                self.agent.web_server = agent.web_interface.WebServer(self.agent)
            except Exception as e:
                logger.error(f"Failed to reload web interface module: {e}")
                await self.agent.discord.send_message(channel_id, f"⚠️ Failed to reload module: {e}")

            import asyncio
            await asyncio.sleep(2)  # Short wait as we preserve ngrok process
            # Fall through to start
        
        # Handle start (or continue from restart)
        # Check if there's already a tunnel running
        existing_url = None
        try:
            from pyngrok import ngrok
            tunnels = ngrok.get_tunnels()
            for t in tunnels:
                if t.config['addr'].endswith(str(self.agent.web_server.port)):
                    existing_url = t.public_url
                    break
        except Exception:
            pass  # Ignore errors, will try to create new tunnel
        
        if existing_url:
            await self.agent.discord.send_message(channel_id, "🔍 Found existing web tunnel...")
        else:
            await self.agent.discord.send_message(channel_id, "🌐 Starting web tunnel... please wait.")
        
        url = self.agent.web_server.start_ngrok()
        
        if url:
            # Create view with link buttons for dashboard and docs
            view = discord.ui.View(timeout=None)
            
            # Add link buttons using Button constructor (not decorator)
            dashboard_button = discord.ui.Button(
                label="🏠 Dashboard",
                style=discord.ButtonStyle.link,
                url=url
            )
            docs_button = discord.ui.Button(
                label="📚 Documentation",
                style=discord.ButtonStyle.link,
                url=f"{url}/docs"
            )
            
            view.add_item(dashboard_button)
            view.add_item(docs_button)
            
            # Add Restart Button
            restart_button = discord.ui.Button(
                label="🔄 Restart web",
                style=discord.ButtonStyle.primary,
                custom_id="web_restart_btn"
            )
            
            async def restart_callback(interaction):
                await interaction.response.defer()
                await self.cmd_web(interaction.channel_id, ["restart"], interaction.user.id)
                
            restart_button.callback = restart_callback
            view.add_item(restart_button)
            
            # Different message based on whether tunnel existed or was created
            if existing_url:
                title = "🔗 Web Interface Connected!"
                color = 0x34A853 # Green
            elif subcommand == "restart":
                title = "🔄 Web Interface Restarted!"
                color = 0xFAA61A # Orange
            else:
                title = "✅ Web Interface Online!"
                color = 0x34A853 # Green
                
            embed = discord.Embed(
                title=title, 
                description="Klikněte na tlačítko níže pro otevření dashboardu.", 
                color=color
            )
            embed.set_footer(text="🔒 Poznámka: Při prvním otevření odkazu může ngrok vyžadovat bezpečnostní potvrzení (klikněte na 'Visit Site'). Toto se děje pouze jednou na zařízení.")
            
            await self.agent.discord.send_message(
                channel_id, 
                embed=embed,
                view=view
            )
        else:
            await self.agent.discord.send_message(channel_id, "❌ Failed to start web tunnel. Check logs.")

    async def cmd_upload(self, channel_id: int, author_id: int):
        """Upload new release to GitHub (Admin only)."""
        # Admin check
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can upload releases to GitHub.")
            return
        
        await self.agent.discord.send_message(channel_id, "🚀 **GitHub Release Upload**\nChecking rate limit...")
        
        try:
            # Import GitHub release module
            from scripts.internal.github_release import create_release, check_rate_limit
            import config_secrets
            
            github_token = config_secrets.GITHUB_TOKEN
            repo_name = "davca2848123/AI_agent"
            
            # Check rate limit
            allowed, time_remaining = check_rate_limit(min_hours=2)
            
            if not allowed:
                hours = int(time_remaining // 3600)
                minutes = int((time_remaining % 3600) // 60)
                await self.agent.discord.send_message(
                    channel_id, 
                    f"⏳ **Rate Limit Active**\n\n"
                    f"Uploads are limited to once every 2 hours.\n"
                    f"⏰ Try again in: **{hours}h {minutes}m**\n\n"
                    f"_This prevents accidental spam and excessive API usage._"
                )
                return
            
            # Proceed with upload
            await self.agent.discord.send_message(channel_id, "📦 Creating release... (this may take ~30s)")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                create_release,
                github_token,
                repo_name,
                "main",
                False,  # force=False
                2       # min_hours=2
            )
            
            if success:
                await self.agent.discord.send_message(
                    channel_id,
                    "✅ **GitHub Release Created Successfully!**\n\n"
                    "📍 Check: https://github.com/davca2848123/AI_agent/releases\n"
                    "⏰ Next upload available in: **2 hours**"
                )
            else:
                await self.agent.discord.send_message(
                    channel_id,
                    "❌ **Release Creation Failed**\n\n"
                    "Check `agent.log` for details."
                )
                
        except ImportError as e:
            await self.agent.discord.send_message(channel_id, f"❌ **Configuration Error:** Missing config_secrets.py or GITHUB_TOKEN\n{e}")
        except Exception as e:
            logger.error(f"!upload command error: {e}", exc_info=True)
            await self.agent.discord.send_message(channel_id, f"❌ **Error:** {e}")

    async def cmd_disable(self, channel_id: int, author_id: int):
        """Disable interaction for non-admin users."""
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can disable interaction.")
            return
            
        self.global_interaction_enabled = False
        await self.agent.discord.send_message(channel_id, "🔒 **Interaction Disabled**\nI will now ignore commands from non-admin users.")
        logger.warning(f"Global interaction disabled by admin {author_id}")

    async def cmd_enable(self, channel_id: int, author_id: int):
        """Enable interaction for all users."""
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can enable interaction.")
            return
            
        self.global_interaction_enabled = True
        await self.agent.discord.send_message(channel_id, "🔓 **Interaction Enabled**\nI am now listening to all users.")
        logger.info(f"Global interaction enabled by admin {author_id}")

    async def cmd_debug(self, channel_id: int, args: list, author_id: int):
        """Enhanced debug diagnostics with strict checking (Admin only)."""
        import config_settings
        import time
        import asyncio
        
        # Admin check
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can use debug commands.")
            return
        
        # Parse mode
        mode = args[0].lower() if args else "quick"
        
        if mode not in ["quick", "deep", "tools", "compile"]:
            await self.agent.discord.send_message(
                channel_id,
                "❓ **Usage:** `!debug [quick|deep|tools|compile]`\n\n"
                "- **quick**: Fast health check\n"
                "- **deep**: Comprehensive diagnostics\n"
                "- **tools**: Tool validation\n"
                "- **compile**: Python syntax check"
            )
            return
        
        await self.agent.discord.send_message(channel_id, f"🔍 Running **{mode}** diagnostics...")
        
        results = []
        
        # === QUICK MODE ===
        if mode in ["quick", "deep"]:
            # 1. LLM Check
            try:
                if self.agent.llm and self.agent.llm.llm:
                    start = time.time()
                    resp = await self.agent.llm.generate_response("ping", system_prompt="Reply: pong")
                    latency = (time.time() - start) * 1000
                    if resp and "pong" in resp.lower():
                        results.append(f"✅ **LLM**: Online ({latency:.0f}ms)")
                    else:
                        results.append(f"⚠️ **LLM**: Responding but unexpected output")
                else:
                    results.append("🔴 **LLM**: Not initialized")
            except Exception as e:
                results.append(f"❌ **LLM**: Error - {e}")
            
            # 2. Discord Check
            if self.agent.discord and self.agent.discord.client:
                results.append(f"✅ **Discord**: Connected ({self.agent.discord.client.user.name})")
            else:
                results.append("🔴 **Discord**: Not connected")
            
            # 3. Database Check
            try:
                mem_count = len(self.agent.memory.get_recent_memories(limit=1))
                results.append(f"✅ **Database**: Accessible ({mem_count}+ memories)")
            except Exception as e:
                results.append(f"❌ **Database**: Error - {e}")
            
            # 4. Tools Check
            tool_count = len(self.agent.tools.tools)
            results.append(f"✅ **Tools**: {tool_count} registered")
        
        # === DEEP MODE ===
        if mode == "deep":
            # 5. File System Check
            import os
            checks = [
                ("agent.log", os.path.exists("agent.log")),
                ("config_secrets.py", os.path.exists("config_secrets.py")),
                ("agent/core.py", os.path.exists("agent/core.py")),
                ("scripts/", os.path.isdir("scripts"))
            ]
            fs_ok = all(c[1] for c in checks)
            if fs_ok:
                results.append("✅ **Filesystem**: All critical files present")
            else:
                missing = [c[0] for c in checks if not c[1]]
                results.append(f"⚠️ **Filesystem**: Missing: {', '.join(missing)}")
            
            # 6. Network Check
            import subprocess
            import platform
            try:
                cmd = "ping -c 1 8.8.8.8" if platform.system() != "Windows" else "ping -n 1 8.8.8.8"
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                if proc.returncode == 0:
                    results.append("✅ **Network**: Internet accessible")
                else:
                    results.append("⚠️ **Network**: No internet connection")
            except:
                results.append("❓ **Network**: Check failed")
            
            # 7. Resource Check
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            results.append(
                f"📊 **Resources**:\n"
                f"  - CPU: {cpu}%\n"
                f"  - RAM: {mem.percent}% ({mem.available / 1024**3:.1f}GB free)\n"
                f"  - Disk: {disk.percent}% ({disk.free / 1024**3:.1f}GB free)"
            )
        
        # === TOOLS MODE ===
        if mode == "tools":
            results.append("🛠️ **Tool Validation:**\n")
            for tool_name, tool in self.agent.tools.tools.items():
                try:
                    # Basic validation
                    has_desc = bool(tool.description)
                    has_func = callable(tool.function)
                    usage = self.agent.tool_usage_count.get(tool_name, 0)
                    
                    status = "✅" if (has_desc and has_func) else "⚠️"
                    results.append(f"{status} `{tool_name}` - Used {usage}x")
                except Exception as e:
                    results.append(f"❌ `{tool_name}` - Error: {e}")
        
        # === COMPILE MODE ===
        if mode == "compile":
            results.append("🔧 **Python Syntax Check:**\n")
            files_to_check = [
                "main.py",
                "agent/core.py",
                "agent/commands.py",
                "agent/tools.py",
                "agent/llm.py"
            ]
            
            for filepath in files_to_check:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                    compile(code, filepath, 'exec')
                    results.append(f"✅ `{filepath}`")
                except SyntaxError as e:
                    results.append(f"❌ `{filepath}` - Line {e.lineno}: {e.msg}")
                except FileNotFoundError:
                    results.append(f"⚠️ `{filepath}` - Not found")
                except Exception as e:
                    results.append(f"❌ `{filepath}` - {e}")
        
        # Send results
        output = "\n".join(results)
        await self.agent.discord.send_message(
            channel_id,
            f"🔍 **Debug Report - {mode.upper()}**\n\n{output}"
        )

    async def cmd_documentation(self, channel_id: int):
        """Shows project documentation with interactive buttons."""
        overview_path = "documentation/OVERVIEW.md"
        try:
            if not discord:
                await self.agent.discord.send_message(channel_id, "❌ Discord module not available.")
                return

            # Send initial message with embed
            embed = discord.Embed(
                title="📚 AI Agent Dokumentace",
                description="Zde naleznete kompletní dokumentaci k systému. Vyberte sekci pomocí tlačítek níže:",
                color=0x3498db
            )
            embed.add_field(name="📖 Overview", value="Základní přehled systému, architektura a rychlý start.", inline=False)
            embed.add_field(name="💬 Commands", value="Seznam všech 24 příkazů rozdělený do kategorií.", inline=False)
            embed.add_field(name="🛠️ Tools", value="Detailní popis všech 14 dostupných nástrojů a jejich použití.", inline=False)
            embed.add_field(name="🧠 Core", value="Dokumentace jádra systému (Autonomní chování, Paměť, LLM, atd.).", inline=False)
            embed.add_field(name="📜 Scripts", value="Deployment guide, Batch scripts reference, RPI setup a údržba.", inline=False)
            embed.add_field(name="⚙️ Configuration", value="Nastavení, secrets, environment variables.", inline=False)
            embed.add_field(name="🎓 Advanced", value="Pokročilá témata: Fuzzy matching algoritmus, Queue system, atd.", inline=False)
            embed.add_field(name="🆘 Troubleshooting", value="Řešení problémů: Agent, LLM, Database, Discord, Resources, Network.", inline=False)
            
            await self.agent.discord.send_message(channel_id, embed=embed, view=DocumentationView(self))

        except Exception as e:
            logger.error(f"Documentation error: {e}")

            if os.path.exists(overview_path):
                try:
                    with open(overview_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if len(content) > 1000:
                        content = content[:1000] + "\n\n... (pokračování v tlačítkách)"
                except:
                    content = "(Chyba při náhledu)"
            
            view = DocumentationView(self)
            await self.agent.discord.send_message(channel_id, f"📚 **AI Agent Dokumentace**\n\n{content}", view=view)



    async def cmd_help(self, channel_id: int):
        """Show all available commands with friendly formatting and categories."""
        
        # View for documentation button
        class HelpView(discord.ui.View):
            def __init__(self, command_handler):
                super().__init__(timeout=120)
                self.command_handler = command_handler
            
            @discord.ui.button(label="📜 Dokumentace k příkazům", style=discord.ButtonStyle.primary, emoji="📚")
            async def docs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Open CommandsView directly (ephemeral)
                await interaction.response.send_message("Vyber kategorii příkazů:", view=CommandsView(parent_view=None), ephemeral=True)

        help_text = """
🤖 **AI Agent - Nápověda Příkazů** (25 příkazů)

📋 **BASIC**
`!help` - Zobrazení nápovědy
`!status` - Stav agenta + diagnostika
`!stats` - Detailní statistiky
`!info` - Systémové a HW informace
`!intelligence` - Intelligence metriky
`!documentation` / `!docs` - Interaktivní dokumentace
`!web [start|stop|restart]` - Web interface + docs

🎓 **LEARNING & TOOLS**
`!learn [tool|all|stop|queue]` - Naučí nástroje
`!tools` - Seznam všech 14 nástrojů
`!ask <otázka>` - Zeptej se AI (LLM + nástroje)
`!teach <text>` - Nauč AI něco nového
`!search <dotaz>` - Vyhledej informace

💾 **DATA MANAGEMENT**
`!memory [dump]` - Statistiky paměti
`!logs [počet] [ERROR|WARNING|INFO]` - Zobraz logy
`!live logs [1m|5m|15m]` - Živý stream logů
`!export [history|memory|stats|all]` - Export dat

💬 **INTERACTION**
`!mood` - Zobraz náladu agenta
`!config` - Zobrazení konfigurace
`!monitor [1m|5m|15m]` - Resource monitoring

⚙️ **ADMIN**
`!restart` - Restart agenta
`!shutdown` - Bezpečné vypnutí agenta
`!debug [quick|all|deep|tools|compile]` - Pokročilá diagnostika
`!ssh [start|stop|status]` - SSH tunel správa
`!cmd <příkaz>` 👤(omezené) - Shell příkazy (Linux-Debian)
`!topic [list|add|remove|clear]` 👤(omezené) - Témata pro boredom
`!goals [add|remove|clear] [text]` 👤(omezené) - Správa cílů
`!report` 👤 - Report posledního příkazu
`!upload` - GitHub release upload
`!disable` / `!enable` - Globální interakce on/off

💡 **Syntaxe:** <povinné> [nepovinné|možnosti]
👤 **Poznámka:** Příkazy označené 👤 mohou používat i běžní uživatelé.
📚 **Web Docs:** Použij `!web` pro přístup k webové dokumentaci
        """
        
        view = HelpView(self)
        await self.agent.discord.send_message(channel_id, help_text.strip(), view=view)
    
    async def get_status_text(self):
        """Generates the status text for the agent."""
        import platform
        import time
        import asyncio
        import psutil

        hostname = platform.node()
        os_name = platform.system()
        
        status_text = f"📊 **Agent Status**\n\n"
        status_text += f"🖥️ **Host:** `{hostname}` ({os_name})\n"
        status_text += f"✅ **Running**\n\n"
        
        # --- Health Checks ---
        status_text += "**🩺 Diagnostics:**\n"
        
        # 1. LLM Check
        start_time = time.time()
        llm_status = "🔴 Unavailable"
        
        if self.agent.llm and self.agent.llm.llm:
            try:
                # Quick generation test
                response = await self.agent.llm.generate_response("ping", system_prompt="Reply with 'pong'.")
                latency = (time.time() - start_time) * 1000
                if response and "LLM not available" not in response:
                    provider = getattr(self.agent.llm, 'provider_type', 'Unknown')
                    llm_status = f"✅ Online ({latency:.0f}ms) [{provider}]"
                else:
                    llm_status = "⚠️ Error (No response)"
            except Exception as e:
                llm_status = f"🔴 Error: {e}"
        else:
            llm_status = "🔴 Not Initialized"
            
        status_text += f"• **LLM:** {llm_status}\n"
        
        # 2. Internet Check
        try:
            cmd = "ping -c 1 8.8.8.8" if platform.system() != "Windows" else "ping -n 1 8.8.8.8"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            if proc.returncode == 0:
                status_text += "• **Internet:** ✅ Connected\n"
            else:
                status_text += "• **Internet:** ✖️ Disconnected\n"
        except Exception:
             status_text += "• **Internet:** ❓ Unknown\n"

        # 3. Disk Space
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            status_text += f"• **Disk Free:** {free_gb:.1f} GB\n"
        except:
            pass
        
        # Create view with stats button
        view = StatusView(self)
        
        await self.agent.discord.send_message(channel_id, status_text, view=view)

    async def cmd_intelligence(self, channel_id: int):
        """Show intelligence metrics (Logarithmic Scale)."""
        import math
        
        # Calculate scores
        tool_diversity = len(self.agent.tool_usage_count)
        total_tool_uses = sum(self.agent.tool_usage_count.values())
        successful_learns = self.agent.successful_learnings
        
        # Logarithmic Formula:
        # 1. Diversity: 4 points per unique tool
        # 2. Usage: 20 * log10(usage) -> 10 uses = 20pts, 100 uses = 40pts, 1000 uses = 60pts
        # 3. Learning: 5 points per successful learning
        
        usage_score = 0
        if total_tool_uses > 0:
             usage_score = 20 * math.log10(total_tool_uses)
             
        intelligence = int((tool_diversity * 4) + usage_score + (successful_learns * 5))
        
        # Determine Level/Rank
        if intelligence < 50:
            rank = "🌱 Novice"
            desc = "Just starting out."
        elif intelligence < 100:
            rank = "🔨 Apprentice"
            desc = "Learning the basics."
        elif intelligence < 200:
            rank = "🔧 Adept"
            desc = "Getting smarter every day."
        elif intelligence < 350:
            rank = "🎓 Expert"
            desc = "High capabilities and experience."
        else:
            rank = "🧠 Master AI"
            desc = "Singularity approaching?"

        intel_text = f"""🧠 **Intelligence Metrics:**

**Overall Score:** {intelligence}
**Rank:** {rank}

• Tool Diversity: {tool_diversity} tools (x4 = {tool_diversity*4})
• Usage Score: {int(usage_score)} (based on {total_tool_uses} uses)
• Learnings: {successful_learns} (x5 = {successful_learns*5})

_{desc}_"""
        
        await self.agent.discord.send_message(channel_id, intel_text)

    async def cmd_intel(self, channel_id: int):
        """Shortcut for intelligence."""
        await self.cmd_intelligence(channel_id)
    
    async def cmd_restart(self, channel_id: int, author: str, author_id: int):
        """Restart the agent (Admin only)."""
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can restart the agent.")
            return
        
        await self.agent.discord.send_message(channel_id, "🔄 Restarting agent...")
        logger.info(f"Agent restart initiated by {author}")
        
        # Create restart flag file with channel ID for post-restart notification
        import json
        restart_info = {
            "channel_id": channel_id,
            "author": author,
            "timestamp": time.time()
        }
        with open(".restart_flag", "w") as f:
            json.dump(restart_info, f)
        
        # Perform graceful shutdown before restart
        logger.info("Performing graceful shutdown...")
        shutdown_success = await self.agent.graceful_shutdown(timeout=10)
        
        if not shutdown_success:
            logger.warning("Graceful shutdown failed or timed out")
            
        if not shutdown_success:
            # Shutdown failed and user might have cancelled via the interactive view in graceful_shutdown
            # or it timed out without forced restart.
            # If graceful_shutdown returned False, it means we shouldn't proceed with restart unless forced inside there?
            # Actually, graceful_shutdown interactively handles "Force", but if it returns False that means "Cancel".
            # Raising SystemExit or execv inside graceful_shutdown might be too much side effect.
            # Let's assume graceful_shutdown handles the UI, and returns True if we should proceed (or if force was chosen), False if cancelled.
            
            # Wait, my previous implementation of graceful_shutdown returns True if "Force" is chosen.
            # So if it returns False, it means "Cancel".
            await self.agent.discord.send_message(channel_id, "❌ **Restart cancelled.**")
            return

        # 2. Restart Process
        import os
        import sys
        logger.info("Restarting Python process...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    async def cmd_shutdown(self, channel_id: int, author_id: int):
        """Gracefully shutdown the agent (Admin only)."""
        # Admin check
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied**: This command is restricted to administrators.")
            return
        
        # Send confirmation message
        await self.agent.discord.send_message(channel_id, "🛑 **Shutting down agent...**\nStopping service and killing all processes.")
        
        # Log shutdown
        logger.info(f"Shutdown initiated by admin {author_id}")
        
        try:
            # Perform graceful shutdown
            await self.agent.graceful_shutdown(timeout=10)
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}")
        
        # Stop the service via systemctl (which will kill this process)
        logger.info("Executing: sudo systemctl stop rpi_ai.service")
        import subprocess
        try:
            # Run in background/detached logic not needed as we want to die, but we need to ensure the command is sent 
            # before we die. subprocess.run waits, but if we are killed during it, it's fine.
            # We assume sudo passwordless is set up for this command as per setup scripts.
            subprocess.run(["sudo", "systemctl", "stop", "rpi_ai.service"], check=False)
        except Exception as e:
            logger.error(f"Failed to execute systemctl stop: {e}")
            await self.agent.discord.send_message(channel_id, f"❌ Failed to stop service: {e}")
        
        # Exit the process explicitly if systemctl didn't kill us instantly
        logger.info("Exiting agent process...")
        import sys
        sys.exit(0)
    

    async def cmd_learn(self, channel_id: int, args: list = None):
        """Force AI to learn. Usage: !learn [tool_name|all|stop|queue]"""
        
        if not args:
            # Single forced learning (original behavior)
            await self.agent.discord.send_message(channel_id, "🎓 Forcing single learning session...")
            self.agent.actions_without_tools = 2
            self.agent.boredom_score = 1.0 # Force immediate action
            await self.agent.discord.send_message(channel_id, "✅ Learning forced. I will try to learn something new now.")
            return

        raw_subcommand = args[0].lower()
        valid_subcommands = ["all", "stop", "queue"]
        # Also include tool names for fuzzy matching if it's not a standard subcommand
        all_tools = list(self.agent.tools.tools.keys())
        
        # First check standard subcommands
        subcommand = self._match_subcommand(raw_subcommand, valid_subcommands)
        
        # If no standard subcommand matched, check tools
        if not subcommand:
            tool_match = self._match_subcommand(raw_subcommand, all_tools)
            if tool_match:
                subcommand = tool_match
            else:
                # If no match at all, keep raw for error message or exact match fallback
                subcommand = raw_subcommand
                
        if subcommand != raw_subcommand:
             await self.agent.discord.send_message(channel_id, f"💡 Did you mean `{subcommand}`? Executing...")
        
        # Queue command - show current learning queue
        if subcommand == 'queue':
            if not self.agent.learning_queue:
                await self.agent.discord.send_message(channel_id, "📋 **Learning Queue: Empty**\nUse `!learn all` to start learning all tools.")
                return
            
            queue_list = "\n".join([f"{i+1}. `{tool}`" for i, tool in enumerate(self.agent.learning_queue)])
            total = len(self.agent.learning_queue)
            status = "🔄 Active" if self.agent.is_learning_mode else "⏸️ Paused"
            
            await self.agent.discord.send_message(channel_id, 
                f"📋 **Learning Queue Status:** {status}\n\n"
                f"**Remaining Tools ({total}):**\n{queue_list}\n\n"
                f"💡 *Use `!learn stop` to cancel the queue*")
            return
        
        # Stop command
        if subcommand == 'stop':
            if self.agent.is_learning_mode:
                self.agent.is_learning_mode = False
                self.agent.learning_queue = []
                await self.agent.discord.send_message(channel_id, "🛑 **Learning Session Stopped.**\nResuming normal autonomous behavior.")
            else:
                await self.agent.discord.send_message(channel_id, "ℹ️ No active learning session to stop.")
            return

        # Learn All
        if subcommand == 'all':
            # Learn all tools sequentially
            await self.agent.discord.send_message(channel_id, "🎓 **Starting Comprehensive Learning Session**")
            
            tools_to_learn = list(self.agent.tools.tools.keys())
            count = len(tools_to_learn)
            
            await self.agent.discord.send_message(channel_id, 
                f"📋 Plan: I will systematically learn and test {count} tools.\n"
                f"Tools: {', '.join(tools_to_learn)}")
            
            # Set learning mode
            self.agent.learning_queue = tools_to_learn
            self.agent.is_learning_mode = True
            self.agent.boredom_score = 1.0  # Force immediate action
            
            await self.agent.discord.send_message(channel_id, "🚀 Learning sequence initiated!")
            return

        # Learn Specific Tool
        tool_name = subcommand
        
        if tool_name in self.agent.tools.tools:
            await self.agent.discord.send_message(channel_id, f"🎓 **Targeted Learning:** `{tool_name}`")
            
            # Set up single-item queue
            self.agent.learning_queue = [tool_name]
            self.agent.is_learning_mode = True
            self.agent.boredom_score = 1.0
            
            await self.agent.discord.send_message(channel_id, f"🚀 Learning sequence initiated for `{tool_name}`!")
        else:
             await self.agent.discord.send_message(channel_id, f"✖️ Unknown tool: `{tool_name}`.\nAvailable tools: {', '.join(self.agent.tools.tools.keys())}")
    
    async def cmd_memory(self, channel_id: int):
        """Show memory statistics."""
        mem_count = len(self.agent.memory.get_recent_memories(limit=10000))
        action_count = len(self.agent.action_history)
        
        # Count by type
        learning_count = self.agent.memory.count_memories_by_type("learning")
        user_teaching_count = self.agent.memory.count_memories_by_type("user_teaching")
        error_count = self.agent.memory.count_memories_by_type("error")
        
        mem_text = f"""💾 **Memory Statistics:**

• **Total Memories:** {mem_count}
• **Action History:** {action_count} entries

**📊 Breakdown:**
• 🧠 Learned Concepts: {learning_count}
• 🎓 User Teachings: {user_teaching_count}
• ⚠️ Recorded Errors: {error_count}
• 📝 Other: {mem_count - learning_count - user_teaching_count - error_count}

**💡 Configuration:**
• Min Score to Save: {config_settings.MEMORY_CONFIG['MIN_SCORE_TO_SAVE']}
• Keywords: {', '.join(config_settings.MEMORY_CONFIG['KEYWORDS'][:5])}..."""
        
        await self.agent.discord.send_message(channel_id, mem_text)
    
    async def cmd_tools(self, channel_id: int):
        """Show available tools and usage."""
        tool_text = "🛠️ **Available Tools:**\n\n"
        
        # List all registered tools
        for tool_name, tool in self.agent.tools.tools.items():
            usage_count = self.agent.tool_usage_count.get(tool_name, 0)
            last_used_ts = self.agent.tool_last_used.get(tool_name)
            
            # Improved formatting
            status_icon = "🆕" if usage_count == 0 else "✅"
            status_text = "New" if usage_count == 0 else f"Used {usage_count}x"
            
            tool_text += f"**{tool_name}** {status_icon} ({status_text})\n"
            if last_used_ts:
                last_used_str = datetime.datetime.fromtimestamp(last_used_ts).strftime('%Y-%m-%d %H:%M')
                tool_text += f"└ 🕒 Last used: {last_used_str}\n"
            
            tool_text += f"└ 📝 _{tool.description}_\n\n"
        
        await self.agent.discord.send_message(channel_id, tool_text)
    
    async def cmd_logs(self, channel_id: int, args: list):
        """Show recent log entries."""
        # Parse arguments
        num_lines = 20
        log_level = None
        
        if args:
            if args[0].isdigit():
                num_lines = int(args[0])  # No limit, use user-specified value
            elif args[0].lower() in ['error', 'warning', 'info', 'debug']:
                log_level = args[0].upper()
            
            # Check for second argument (log level after number)
            if len(args) > 1 and args[1].lower() in ['error', 'warning', 'info', 'debug']:
                log_level = args[1].upper()
        
        try:
            # Read last N lines from agent.log
            log_path = "agent.log"
            if not os.path.exists(log_path):
                await self.agent.discord.send_message(channel_id, "✖️ Log file not found.")
                return
            
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter by log level first if specified
            if log_level:
                filtered_lines = [line for line in lines if log_level in line]
                # Then get last N lines from filtered results
                recent_lines = filtered_lines[-num_lines:]
            else:
                # No filter, just get last N lines
                recent_lines = lines[-num_lines:]
            
            if not recent_lines:
                await self.agent.discord.send_message(channel_id, "📭 No matching log entries found.")
                return
            
            # If more than 50 lines, send as file
            if len(recent_lines) > 50:
                # Create temp file
                import tempfile
                filter_suffix = f"_{log_level.lower()}" if log_level else ""
                filename = f"logs_{num_lines}{filter_suffix}_{int(time.time())}.txt"
                temp_path = os.path.join(tempfile.gettempdir(), filename)
                
                try:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.writelines(recent_lines)
                    
                    filter_text = f" ({log_level} only)" if log_level else ""
                    await self.agent.discord.send_message(
                        channel_id, 
                        f"📋 **Last {len(recent_lines)} log entries{filter_text}:**\nSending as file...",
                        file_path=temp_path
                    )
                finally:
                    # Clean up temp file
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except:
                        pass
            else:
                # Send in message (50 or fewer lines)
                log_output = ''.join(recent_lines)
                
                # Truncate if too long for Discord
                if len(log_output) > 1900:
                    log_output = log_output[-1900:]
                    prefix = "... (truncated)\n"
                else:
                    prefix = ""
                
                filter_text = f" ({log_level} only)" if log_level else ""
                await self.agent.discord.send_message(channel_id, 
                    f"📋 **Last {len(recent_lines)} log entries{filter_text}:**\n```\n{prefix}{log_output}\n```")
        
        except Exception as e:
            await self.agent.discord.send_message(channel_id, f"✖️ Error reading logs: {e}")
    
    async def cmd_live(self, channel_id: int, args: list):
        """Live commands - currently supports 'logs' or 'log'."""
        if not args:
            await self.agent.discord.send_message(channel_id, "❓ Usage: `!live logs [duration]`")
            return
        
        raw_subcommand = args[0].lower()
        valid_subcommands = ["logs", "log"]
        
        subcommand = self._match_subcommand(raw_subcommand, valid_subcommands)
        
        if subcommand:
            if subcommand != raw_subcommand:
                 await self.agent.discord.send_message(channel_id, f"💡 Did you mean `{subcommand}`? Starting stream...")
            # Parse optional duration (default 60s)
            duration = 60  # Default: 1 minute
            if len(args) > 1:
                # Support formats like: 20, 20s, 2m, 1h
                match = re.match(r"(\d+)([smh]?)", args[1].lower())
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    if unit == 'm':
                        duration = value * 60
                    else:
                        duration = value  # seconds or no unit
            
            # Run as background task so other commands can be processed
            asyncio.create_task(self._cmd_logs_live(channel_id, min(duration, 3600)))
        else:
            await self.agent.discord.send_message(channel_id, f"❓ Unknown subcommand: `{subcommand}`. Use `!live logs`")
    
    async def _cmd_logs_live(self, channel_id: int, duration: int = 60):
        """Live stream logs for specified duration (default 60 seconds)."""

        log_path = "agent.log"
        if not os.path.exists(log_path):
            await self.agent.discord.send_message(channel_id, "✖️ Log file not found.")
            return

        # Vypočítáme čas ukončení pro zobrazení
        start_time = time.time()
        end_time = start_time + duration
        end_dt = datetime.datetime.now() + datetime.timedelta(seconds=duration)
        end_time_str = end_dt.strftime("%H:%M:%S")

        # První zpráva
        msg_obj = await self.agent.discord.send_message(channel_id, 
            f"📸 **Live Log Monitor** (Ends at {end_time_str})\n```\nInitializing...\n```")
        
        if not msg_obj: return

        # Nastavení čtení souboru (od konce)
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)
                # Načteme jen kousek zpět, ať nemáme tunu textu na začátku
                last_position = max(0, f.tell() - 10000) 
                f.seek(last_position)
        except Exception as e:
            await msg_obj.edit(content=f"✖️ Error: {e}")
            return

        # Filtrovací funkce (stejná jako dřív, aby tam nebylo smetí)
        def should_show_log(line):
            # Discord internal spam filter
            discord_markers = ['discord.client', 'discord.gateway', 'WebSocket Event', 'Keep Alive']
            if any(m in line for m in discord_markers) and "ERROR" not in line: return False
            if len(line) > 350: return False # Skip extremne dlouhe radky
            if '- DEBUG -' in line and 'agent.' not in line: return False
            return True

        log_buffer = []

        # --- HLAVNÍ SMYČKA ---
        iteration = 0
        while True:
            iteration += 1
            current_time = time.time()
            remaining = int(end_time - current_time)
            
            if remaining <= 0: break
            
            # Čtení nových řádků
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()

                updated = False
                if new_lines:
                    for line in new_lines:
                        if should_show_log(line):
                            # Jen ořežeme prázdné znaky na konci a ošetříme backsticky
                            clean_line = line.strip().replace("```", "'''")
                            if clean_line:
                                log_buffer.append(clean_line + "\n") # Přidáme odřádkování
                                updated = True
            except: pass

            # Udržujeme buffer v rozumné velikosti (cca 30 řádků)
            log_buffer = log_buffer[-30:]

            # Aktualizace zprávy (jen při změně nebo každých 5s kvůli odpočtu)
            if updated or iteration % 2 == 0:
                
                header = f"📸 **System Live Logging**"
                
                # Spojíme logy
                body_text = "".join(log_buffer)
                
                # Ořez pro limit Discordu (limit 2000 znaku)
                if len(body_text) > 1850:
                    body_text = body_text[-1850:]
                    # Uřízneme k prvnímu novému řádku, aby první řádek nebyl poloviční
                    first_nl = body_text.find('\n')
                    if first_nl != -1:
                        body_text = body_text[first_nl+1:]

                # Code block s "yaml" pro barvu jako !monitor
                content = f"{header} (Ends: {end_time_str})\n```yaml\n{body_text}\nLast Update: {datetime.datetime.now().strftime('%H:%M:%S')}```"
                
                try:
                    await msg_obj.edit(content=content)
                except discord.NotFound:
                    # Message deleted, send new one
                    msg_obj = await self.agent.discord.send_message(channel_id, content)
                    if not msg_obj: break
                except Exception: break 
                
            await asyncio.sleep(2) # Interval aktualizace

        # --- KONEC ---
        final_header = f"✅ **System Live Logging Finished**"
        body_text = "".join(log_buffer)[-1850:] # Bezpečnostní ořez
        
        await msg_obj.edit(content=f"{final_header}\n```yaml\n{body_text}\nLast Update: {datetime.datetime.now().strftime('%H:%M:%S')}```")
    

    async def cmd_stats(self, channel_id: int):
        """Show comprehensive statistics."""
        import math
        
        uptime_seconds = time.time() - self.agent.start_time
        uptime_str = self._format_uptime(uptime_seconds)
        
        # Intelligence Score - Logarithmic scaling for realism
        tool_diversity = len(self.agent.tool_usage_count)
        total_tool_uses = sum(self.agent.tool_usage_count.values())
        
        # Count learnings from memory (user_teaching and learning types)
        learnings = (self.agent.memory.count_memories_by_type("user_teaching") + 
                    self.agent.memory.count_memories_by_type("learning"))
        
        # Component scores (0-1000 total) - Stricter logarithmic curves
        tool_diversity_score = min(500, math.log(tool_diversity + 1) * 120)  # Max 500 at ~130 tools
        usage_efficiency = min(300, math.log(total_tool_uses + 1) * 100)  # Max 300 points
        learning_score = min(200, math.log(learnings + 1) * 45)  # Max 200 at ~280 learnings
        
        intelligence = int(tool_diversity_score + usage_efficiency + learning_score)
        
        # Activity metrics
        total_actions = len(self.agent.action_history)
        total_memories = len(self.agent.memory.get_recent_memories(limit=10000))
        
        # Calculate activity rate (actions per minute)
        activity_rate = (total_actions / max(1, uptime_seconds / 60))
        
        # Get hostname for stats
        hostname = platform.node()
        os_name = platform.system()
        
        stats_text = f"""📊 **Comprehensive Statistics**

🖥️ **System:**
• Host: `{hostname}` ({os_name})
• Uptime: {uptime_str}
• Started: <t:{int(self.agent.start_time)}:R>

💾 **Memory:**
• Total Memories: {total_memories}

🛠️ **Most Used Tools:**"""
        
        # Sort tools by usage
        sorted_tools = sorted(self.agent.tool_usage_count.items(), key=lambda x: x[1], reverse=True)
        for tool, count in sorted_tools[:3]:
            stats_text += f"\n• {tool}: {count} times"
        
        if not sorted_tools:
            stats_text += "\n• No tools used yet"
        
        await self.agent.discord.send_message(channel_id, stats_text)
    
    async def cmd_export(self, channel_id: int, args: list):
        """Export data and send to Discord chat."""
        import json
        
        raw_export_type = args[0] if args else 'stats'
        valid_types = ['history', 'memory', 'stats', 'all']
        
        export_type = self._match_subcommand(raw_export_type, valid_types)
        
        if not export_type:
            await self.agent.discord.send_message(channel_id, 
                "✖️ Invalid export type. Use: `history`, `memory`, `stats`, or `all`")
            return
            
        if export_type != raw_export_type:
             await self.agent.discord.send_message(channel_id, f"💡 Did you mean `{export_type}`? Exporting...")
        
        export_data = {}
        
        if export_type in ['history', 'all']:
            export_data['action_history'] = self.agent.action_history
        
        if export_type in ['memory', 'all']:
            memories = self.agent.memory.get_recent_memories(limit=50)  # Limit to avoid too long message
            export_data['memories'] = [{'content': m['content'][:100], 'metadata': m['metadata']} for m in memories]
        
        if export_type in ['stats', 'all']:
            export_data['stats'] = {
                'uptime_seconds': time.time() - self.agent.start_time,
                'tool_usage': self.agent.tool_usage_count,
                'successful_learnings': self.agent.successful_learnings,
                'total_actions': len(self.agent.action_history),
                'boredom_score': self.agent.boredom_score,
                'goals': self.agent.goals
            }
        
        # Format as JSON and send to Discord
        json_output = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Check length (Discord has 2000 char limit)
        if len(json_output) > 1900:
            # Save to temp file
            filename = f"export_{export_type}_{int(time.time())}.json"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                
                await self.agent.discord.send_message(channel_id, 
                    f"📦 **Export ({export_type}):**\nData is too large for a message, sending as file.", 
                    file_path=filename)
            except Exception as e:
                await self.agent.discord.send_message(channel_id, f"✖️ Error creating export file: {e}")
            finally:
                # Clean up
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                except:
                    pass
        else:
            await self.agent.discord.send_message(channel_id, 
                f"📦 **Export ({export_type}):**\n```json\n{json_output}\n```")
    async def cmd_ask(self, channel_id: int, question: str):
        """Ask the AI a question."""
        self.agent.is_processing = True
        
        # Manually send thinking since we removed it from global handler
        await self.agent.discord.send_message(channel_id, "🤔 Thinking...")
        
        try:
            if not question:
                await self.agent.discord.send_message(channel_id, "❓ Usage: `!ask <your question>`")
                return

            # Initialize memories variable to prevent NameError in error handling code
            memories = []
            
            # Retrieve relevant memories with defensive error handling
            try:
                memories = self.agent.memory.search_relevant_memories(question, limit=5)
            except Exception as mem_error:
                logger.warning(f"cmd_ask: Failed to retrieve memories: {mem_error}")
                # Continue with empty memories list
            
            # 1. Select Tool
            tools_desc = self.agent.tools.get_descriptions()
            system_prompt = (
                "You are an intelligent assistant with access to the following tools:\n"
                f"{tools_desc}\n\n"
                "Analyze the user's question and determine if a tool is needed to answer it.\n"
                "If a tool is needed, return a JSON object with the tool name and arguments.\n"
                "If NO tool is needed (e.g. for general knowledge or chat), return 'NO_TOOL'.\n\n"
                "Format for tool usage:\n"
                "```json\n"
                "{\n"
                "  \"tool\": \"tool_name\",\n"
                "  \"params\": {\n"
                "    \"arg_name\": \"value\"\n"
                "  }\n"
                "}\n"
                "```\n"
                "Example: {\"tool\": \"weather_tool\", \"params\": {\"location\": \"London\"}}"
            )
            
            tool_selection_response = await self.agent.llm.generate_response(
                prompt=f"User Question: {question}\n\nSelect the best tool (or NO_TOOL):",
                system_prompt=system_prompt
            )
            
            tools_logger.info(f"cmd_ask: Tool selection response: {tool_selection_response}")
            
            tool_selected = None
            tool_params = {}
            
            if tool_selection_response and "NO_TOOL" not in tool_selection_response.upper():
                try:
                    # Clean up response (remove markdown code blocks if present)
                    clean_response = tool_selection_response.strip()
                    if clean_response.startswith("```json"):
                        clean_response = clean_response[7:]
                    elif clean_response.startswith("```"):
                        clean_response = clean_response[3:]
                    if clean_response.endswith("```"):
                        clean_response = clean_response[:-3]
                    
                    clean_response = clean_response.strip()
                    
                    # Extract JSON from response (in case LLM adds extra text)
                    json_start = clean_response.find('{')
                    json_end = clean_response.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_str = clean_response[json_start:json_end]
                        tool_data = json.loads(json_str)
                        tool_selected = tool_data.get('tool')
                        tool_params = tool_data.get('params', {})
                        tools_logger.debug(f"cmd_ask: Parsed tool: {tool_selected}, params: {tool_params}")
                    else:
                         tools_logger.warning(f"cmd_ask: Could not find JSON in response: {clean_response}")
                except Exception as e:
                    tools_logger.warning(f"cmd_ask: Failed to parse tool selection JSON: {e}")
            
            # Execute selected tool if valid
            if tool_selected:
                tool = self.agent.tools.get_tool(tool_selected)
                if tool:
                    tools_logger.info(f"cmd_ask: Executing tool '{tool_selected}' with params: {tool_params}")
                    
                    # Send status message based on tool type
                    status_messages = {
                        'weather_tool': '🌥️ Checking weather...',
                        'math_tool': '🔢 Calculating...',
                        'time_tool': '🕰️ Checking time...',
                        'translate_tool': '🦜 Translating...',
                        'wikipedia_tool': '📚 Searching Wikipedia...',
                        'web_tool': '🩺 Searching the web...',
                        'code_tool': '💻 Executing code...',
                        'file_tool': '📂 Accessing file...',
                        'system_tool': '🖥️ Checking system...',
                    }
                    status_msg = status_messages.get(tool_selected, f'🔧 Using {tool_selected}...')
                    await self.agent.discord.send_message(channel_id, status_msg)
                    
                    try:
                        tool_result = await tool._execute_with_logging(**tool_params)
                        
                        # Track usage
                        self.agent.tool_usage_count[tool_selected] = self.agent.tool_usage_count.get(tool_selected, 0) + 1
                        self.agent._save_tool_stats()
                        
                        # Check if tool result is an error
                        if tool_result.startswith("Error:"):
                            tools_logger.warning(f"cmd_ask: Tool '{tool_selected}' returned error: {tool_result}")
                            await self.agent.discord.send_message(channel_id, f"⚠️ {tool_result}")
                            # Don't return, continue to LLM-based answer as fallback
                        else:
                            # Formulate answer using tool result
                            answer_prompt = (
                                f"Question: {question}\n\n"
                                f"Tool result:\n{tool_result}\n\n"
                                "Based on the tool result above, provide a clear and conversational answer to the question."
                            )
                            
                            final_answer = await self.agent.llm.generate_response(
                                prompt=answer_prompt,
                                system_prompt="You are a helpful assistant. Use the tool result to answer the question naturally."
                            )
                            
                            await self.agent.discord.send_message(channel_id, f"💬 **Answer:**\n{final_answer}")
                            return
                    except Exception as e:
                        tools_logger.error(f"cmd_ask: Error executing tool '{tool_selected}': {e}")
                        await self.agent.discord.send_message(channel_id, f"✖️ Error using {tool_selected}: {e}")
                        # Continue to LLM-based answer as fallback
            # Step 2: Try to answer directly with AI's knowledge + Memory
            # Build a comprehensive prompt that encourages formulation
            if memories:
                # Has memory context - need to formulate from it
                full_prompt = (
                    f"Question: {question}\n\n"
                    f"Context from my memory:\n" + "\n".join([f"- {m['content']}" for m in memories]) + "\n\n"
                    "Based on the context above, answer the question in YOUR OWN WORDS. "
                    "Formulate a natural, conversational response. Do not just copy from context.\n"
                    "If the context doesn't fully answer the question, reply with: NEED_SEARCH: <query>"
                )
                system_prompt = "You are a helpful assistant. Answer questions naturally based on provided context."
            else:
                # No memories - use general knowledge
                full_prompt = question
                system_prompt = (
                    "You are a helpful AI assistant. Answer questions clearly using your knowledge.\n"
                    "If you need current/real-time information, reply: NEED_SEARCH: <query>\n\n"
                    "Examples:\n"
                    "Q: 'who was hitler' â†’ A: Adolf Hitler was the dictator of Nazi Germany from 1933-1945...\n"
                    "Q: 'what is python' â†’ A: Python is a high-level programming language...\n"
                    "Q: 'news today' â†’ NEED_SEARCH: latest news 2025\n"
                    "Q: 'weather now' â†’ NEED_SEARCH: current weather"
                )
            
            logger.debug("cmd_ask: Sending prompt to LLM...")
            initial_response = await self.agent.llm.generate_response(
                prompt=full_prompt,
                system_prompt=system_prompt
            )
            logger.debug(f"cmd_ask: LLM response received: '{initial_response}'")
            
            if not initial_response:
                logger.error("cmd_ask: Received empty response from LLM")
                await self.agent.discord.send_message(channel_id, "✖️ Error: Empty response from AI.")
                return

            # Check for LLM failure
            if initial_response == "LLM not available.":
                logger.warning("cmd_ask: LLM reported unavailable")
                await self.agent.discord.send_message(channel_id, "⚠️ **LLM Unavailable.** Falling back to web search...")
                
                # Notify Admin
                await self.agent.send_admin_dm("⚠️ **Alert:** LLM is unavailable during `!ask` command execution.", category="error")
                
                web_tool = self.agent.tools.get_tool('web_tool')
                if web_tool:
                    search_results = await web_tool._execute_with_logging(action="search", query=question)
                    # Display results directly since we can't summarize
                    await self.agent.discord.send_message(channel_id, f"🩺 **Search Results for:** `{question}`\n\n{search_results[:1800]}")
                    return
                else:
                    await self.agent.discord.send_message(channel_id, "✖️ Web tool also unavailable.")
                    return



            # === NEW: Detect bad/nonsensical LLM responses ===
            bad_response_indicators = [
                "DON'T",  # Fragment from old prompt examples
                "just repeat",
                len(initial_response.strip()) < 10,  # Too short
                initial_response.strip() == question.strip(),  # Exact repeat of question
                initial_response.lower().startswith(("examples:", "rules:", "instructions:")),  # Regurgitating prompt
            ]
            
            is_bad_response = any([
                indicator if isinstance(indicator, bool) else indicator in initial_response 
                for indicator in bad_response_indicators
            ])
            
            if is_bad_response:
                logger.warning(f"cmd_ask: Detected bad LLM response: '{initial_response}'.")
                
                # Check if we have relevant memories to use instead
                if memories:
                    logger.info(f"cmd_ask: Found {len(memories)} relevant memories. Trying to formulate answer from memory.")
                    
                    # Try to formulate answer from memories using simpler prompt
                    memory_text = "\n".join([f"- {m['content']}" for m in memories[:5]])
                    
                    formulate_prompt = (
                        f"Question: {question}\n\n"
                        f"Information from memory:\n{memory_text}\n\n"
                        "Based on the above information, provide a clear and concise answer to the question. "
                        "Use only the information provided above."
                    )
                    
                    try:
                        memory_answer = await self.agent.llm.generate_response(
                            prompt=formulate_prompt,
                            system_prompt="You are a helpful assistant. Answer based only on the provided information. Be concise and clear."
                        )
                        
                        # Check if this answer is also bad
                        is_memory_answer_bad = any([
                            indicator if isinstance(indicator, bool) else indicator in memory_answer 
                            for indicator in bad_response_indicators
                        ])
                        
                        if not is_memory_answer_bad and len(memory_answer.strip()) > 10:
                            logger.info("cmd_ask: Successfully formulated answer from memories.")
                            await self.agent.discord.send_message(channel_id, f"🧠 **Answer (from memory):**\n{memory_answer}")
                            return
                        else:
                            logger.warning("cmd_ask: LLM failed to formulate memory answer. Showing memories directly.")
                            # Fallback: just show memories directly
                            memory_list = "\n".join([f"{i}. {m['content']}" for i, m in enumerate(memories[:5], 1)])
                            await self.agent.discord.send_message(channel_id, f"🧠 **Based on what I know:**\n{memory_list}")
                            return
                    except Exception as e:
                        logger.error(f"cmd_ask: Error formulating from memories: {e}")
                        # Fallback: show memories directly
                        memory_list = "\n".join([f"{i}. {m['content']}" for i, m in enumerate(memories[:5], 1)])
                        await self.agent.discord.send_message(channel_id, f"🧠 **Based on what I know:**\n{memory_list}")
                        return
                
                # No relevant memories - fallback to web search or other tools
                logger.info("cmd_ask: No relevant memories found, falling back to web search.")
                await self.agent.discord.send_message(channel_id, "🩺 Searching for information...")
                
                web_tool = self.agent.tools.get_tool('web_tool')
                if web_tool:
                    search_results = await web_tool._execute_with_logging(action="search", query=question)
                    await self.agent.discord.send_message(channel_id, f"🩺 **Search Results:**\n{search_results[:1800]}")
                    return
                else:
                    await self.agent.discord.send_message(channel_id, "✖️ Cannot answer - no relevant information in memory and web search unavailable.")
                    return

            # If AI can answer directly, return it
            # Check for NEED_SEARCH intent (case-insensitive)
            import re
            search_match = re.search(r"need_search:\s*(.*)", initial_response, re.IGNORECASE)
            
            if not search_match:
                logger.debug("cmd_ask: Sending direct answer")
                await self.agent.discord.send_message(channel_id, f"💬 **Answer:**\n{initial_response}")
                return
                
            # Step 3: Handle Web Search
            if search_match:
                search_query = search_match.group(1).strip()
                logger.debug(f"cmd_ask: Performing web search for: {search_query}")
                await self.agent.discord.send_message(channel_id, f"🩺 Searching the web for: `{search_query}`...")

                web_tool = self.agent.tools.get_tool('web_tool')
                if web_tool:
                    search_results = await web_tool._execute_with_logging(action="search", query=search_query)
                    
                    # Generate final answer with search results
                    final_prompt = (
                        f"Question: {question}\n\n"
                        f"Search Results:\n{search_results}\n\n"
                        "Based on the search results, provide a comprehensive answer to the question."
                    )
                    
                    final_answer = await self.agent.llm.generate_response(
                        prompt=final_prompt,
                        system_prompt="You are a helpful AI assistant. Synthesize the search results to answer the user's question."
                    )
                    
                    # Save to memory
                    self.agent.memory.add_memory(
                        content=f"Q: {question} -> A: {final_answer}",
                        metadata={"type": "qa_search", "query": search_query}
                    )
                    
                    await self.agent.discord.send_message(channel_id, f"💬 **Answer:**\n{final_answer}")
                    return
                else:
                    await self.agent.discord.send_message(channel_id, "✖️ Web tool not available.")
                    return
                        
        except Exception as e:
            logger.error(f"cmd_ask: Critical error: {e}", exc_info=True)
            # Track error for debug system
        finally:
            self.agent.is_processing = False
    async def cmd_teach(self, channel_id: int, info: str):
        """Teach the AI something new."""
        import config_settings
        if not info:
             await self.agent.discord.send_message(channel_id, "🧠 Usage: `!teach <information>`")
             return

        # Use add_filtered_memory if available (it is now in core.py)
        # Store metadata indicating user source
        metadata = {
            "type": "user_teaching", 
            "importance": "high",
            "taught_by_user": True,
            "source_user_id": config_settings.ADMIN_USER_IDS[0] if config_settings.ADMIN_USER_IDS else 0 # Best guess or from context if available
            # Note: cmd_teach signature in this file doesn't seem to have author_id passed in handle_command for some reason?
            # Checking handle_command: await self.cmd_teach(channel_id, ' '.join(args)) -> No author_id.
            # I should probably update handle_command too if I want author_id, but for now I'll just skip detailed author info or use a generic one.
        }
        
        # Use filtered memory adder to clean up the input if needed, but for !teach we trust the user more.
        # However, the user asked to "extract key info", so using add_filtered_memory is correct.
        if hasattr(self.agent, 'add_filtered_memory'):
            await self.agent.add_filtered_memory(info, metadata)
        else:
             self.agent.memory.add_memory(info, metadata)
        
        self.agent.successful_learnings += 1
        
        await self.agent.discord.send_message(channel_id, 
            f"✅ Learned! I will remember: '{info}'\n🧠 Total learnings: {self.agent.successful_learnings}")
    
    async def cmd_search(self, channel_id: int, query: str):
        """Force AI to search for something. Usage: !search [url] <query>"""
        if not query:
            await self.agent.discord.send_message(channel_id, "🩺 Usage: `!search [url] <query>`")
            return
        
        # Check if query contains a URL
        url = None
        search_term = None
        
        parts = query.split()
        for part in parts:
            if part.startswith(('http://', 'https://')):
                url = part
                break
        
        if url:
            # Remove URL from query to get search term
            search_term = query.replace(url, "").strip()
            
            await self.agent.discord.send_message(channel_id, f"📄 Reading: {url}...")
            if search_term:
                 await self.agent.discord.send_message(channel_id, f"🩺 Searching in page for: '{search_term}'...")
            
            tool = self.agent.tools.get_tool('web_tool')
            if tool:
                # Read page content with higher limit
                content = await tool._execute_with_logging(action='read', url=url, limit=10000)
                
                if content.startswith("Error:"):
                    await self.agent.discord.send_message(channel_id, f"✖️ {content}")
                    return

                if search_term:
                    # Search within content
                    import re
                    # Case insensitive search
                    matches = []
                    # Find all occurrences
                    for m in re.finditer(re.escape(search_term), content, re.IGNORECASE):
                        start = max(0, m.start() - 50)
                        end = min(len(content), m.end() + 50)
                        context = content[start:end].replace("\n", " ")
                        matches.append(f"...{context}...")
                    
                    if matches:
                        # Limit to top 5 matches
                        result_text = "\n".join(matches[:5])
                        await self.agent.discord.send_message(channel_id, f"✅ **Found matches:**\n```\n{result_text}\n```")
                    else:
                        await self.agent.discord.send_message(channel_id, f"✖️ Term '{search_term}' not found in page.")
                else:
                    # Just show beginning of content
                    await self.agent.discord.send_message(channel_id, f"📄 **Page Content:**\n```\n{content[:1900]}\n```")
            else:
                await self.agent.discord.send_message(channel_id, "✖️ Web tool not available")
            
        else:
            # Standard web search
            await self.agent.discord.send_message(channel_id, f"🩺 Searching for: '{query}'...")
            
            # Use the web_tool directly
            tool = self.agent.tools.get_tool('web_tool')
            if tool:
                result = await tool._execute_with_logging(action='search', query=query)
                
                # Track usage
                self.agent.tool_usage_count['web_tool'] = self.agent.tool_usage_count.get('web_tool', 0) + 1
                self.agent._save_tool_stats()
                self.agent._add_to_history(f"Searched: {query}")
                
                await self.agent.discord.send_message(channel_id, f"📋 **Results:**\n{result[:1900]}")
            else:
                await self.agent.discord.send_message(channel_id, "✖️ Web tool not available")
    
    async def _test_code_integrity(self) -> dict:
        """Static analysis of agent code to detect common errors."""
        import ast
        import builtins
        
        results = {"status": "✅ OK", "issues": []}
        files_to_check = [__file__] # Check commands.py
        
        # Add core.py if possible
        try:
            import agent.core
            files_to_check.append(agent.core.__file__)
        except:
            pass

        for file_path in files_to_check:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                
                tree = ast.parse(source)
                
                # 1. Collect globals
                global_names = set(dir(builtins))
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            global_names.add(alias.asname or alias.name.split('.')[0])
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        global_names.add(node.name)
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                global_names.add(target.id)
                
                # 2. Walk functions to find undefined names
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        local_names = set()
                        # Add args
                        for arg in node.args.args:
                            local_names.add(arg.arg)
                        if node.args.vararg: local_names.add(node.args.vararg.arg)
                        if node.args.kwarg: local_names.add(node.args.kwarg.arg)
                        
                        # Walk body to find assignments and usages
                        for child in ast.walk(node):
                            # Track assignments
                            if isinstance(child, ast.Assign):
                                for target in child.targets:
                                    if isinstance(target, ast.Name):
                                        local_names.add(target.id)
                            
                            # Track nested function definitions
                            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                # Don't track the parent function itself
                                if child != node:
                                    local_names.add(child.name)
                            
                            # Track comprehension variables (list/dict/set comp, generator)
                            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                                for generator in child.generators:
                                    if isinstance(generator.target, ast.Name):
                                        local_names.add(generator.target.id)
                                    # Handle tuple unpacking in comprehensions
                                    elif isinstance(generator.target, ast.Tuple):
                                        for elt in generator.target.elts:
                                            if isinstance(elt, ast.Name):
                                                local_names.add(elt.id)
                            
                            # Track lambda arguments
                            elif isinstance(child, ast.Lambda):
                                for arg in child.args.args:
                                    local_names.add(arg.arg)
                            
                            # Track for loop variables
                            elif isinstance(child, (ast.For, ast.AsyncFor)):
                                if isinstance(child.target, ast.Name):
                                    local_names.add(child.target.id)
                                elif isinstance(child.target, ast.Tuple):
                                    for elt in child.target.elts:
                                        if isinstance(elt, ast.Name):
                                            local_names.add(elt.id)
                            
                            # Track with statement variables
                            elif isinstance(child, (ast.With, ast.AsyncWith)):
                                for item in child.items:
                                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                                        local_names.add(item.optional_vars.id)
                            
                            # Track exception handler variables
                            elif isinstance(child, ast.ExceptHandler):
                                if child.name:
                                    local_names.add(child.name)
                            
                            # Check for undefined variables
                            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                                if (child.id not in local_names and 
                                    child.id not in global_names and 
                                    child.id != "self"):
                                    
                                    # Filter out common false positives
                                    # Built-ins and common modules
                                    common_names = [
                                        'True', 'False', 'None', 'Exception',
                                        'logger', 'config_settings', 'discord',
                                        # Standard library modules
                                        'asyncio', 'os', 'time', 'json', 're', 'math',
                                        'sys', 'tempfile', 'ast', 'builtins', 'difflib',
                                        'socket', 'py_compile', 'subprocess', 'datetime',
                                        'glob', 'random', 'platform', 'psutil',
                                        # Common parameter/variable names
                                        'match', 'result', 'response', 'data',
                                        'interaction', 'button', 'view',
                                        'ngrok', 'importlib', 'agent',
                                        'bytes_val', 'value', 'item',
                                        'name', 'length', 'percent', 'util',
                                        'mem_used', 'mem_total', 'kb',
                                        'host', 'port', 'stdout', 'stderr',
                                        'context',
                                        # Function-specific variables
                                        'config_secrets', 'check_rate_limit', 'allowed',
                                        'create_release', 'time_remaining',
                                        'HelpView', 'command_handler', 'channel_id',
                                        # Class names (imported)
                                        'VectorStore', 'LLMClient', 'DiscordClient',
                                        'HardwareMonitor', 'LedIndicator', 'ResourceManager',
                                        'NetworkMonitor', 'get_error_tracker', 'WebServer',
                                        'ToolRegistry', 'CommandHandler',
                                        'FileTool', 'SystemTool', 'WebTool', 'TimeTool',
                                        'MathTool', 'WeatherTool', 'CodeTool', 'NoteTool',
                                        'DatabaseTool', 'DiscordActivityTool', 'RSSTool',
                                        'TranslateTool', 'WikipediaTool',
                                        'ForceShutdownView',
                                        # Special variables
                                        '__file__',
                                    ]
                                    
                                    if child.id in common_names: 
                                        continue
                                    
                                    results["issues"].append(f"{os.path.basename(file_path)}:{node.name}: Undefined variable '{child.id}'")
                                    results["status"] = "⚠️ Issues Found"
            
            except Exception as e:
                results["issues"].append(f"Failed to analyze {os.path.basename(file_path)}: {e}")
        
        if not results["issues"]:
            results["details"] = "No static errors found."
        else:
            results["details"] = "\n".join(results["issues"][:10]) # Limit output
            
        return results

    async def _run_diagnostics(self, area: str) -> dict:
        """Run system diagnostics for a specific area."""
        results = {}
        
        # Determine which tests to run
        if area == 'all':
            # For 'all', only verify availability, don't execute
            test_areas = ['llm', 'network', 'database', 'filesystem', 'tools', 'memory', 'ngrok', 'discord', 'resources', 'loops']
            verify_only = True
        elif area == 'quick':
            test_areas = ['llm', 'network', 'database', 'discord']
            verify_only = False
        elif area == 'deep':
            # DEEP DEBUG MODE
            test_areas = ['critical_files', 'tools_functional', 'network', 'ngrok', 'database', 'filesystem', 'code_integrity']
            verify_only = False
        elif area == 'tools':
            test_areas = ['tools_functional']
            verify_only = False
        elif area == 'filesystem':
            test_areas = ['filesystem', 'critical_files']
            verify_only = False
        else:
            test_areas = [area]
            verify_only = False
        
        # Execute tests
        for test_area in test_areas:
            if verify_only:
                # For 'all', just check if components exist
                if test_area == 'tools':
                    results['tools'] = {'status': '✅ Available' if hasattr(self.agent, 'tools') else '❌ Missing'}
                elif test_area == 'llm':
                    results['llm'] = {'status': '✅ Available' if hasattr(self.agent, 'llm') else '❌ Missing'}
                elif test_area == 'network':
                    results['network'] = {'status': '✅ Available' if hasattr(self.agent, 'network_monitor') else '❌ Missing'}
                elif test_area == 'database':
                    results['database'] = {'status': '✅ Available' if hasattr(self.agent.memory, 'conn') else '❌ Missing'}
                elif test_area == 'filesystem':
                    results['filesystem'] = {'status': '✅ Available' if os.path.exists('workspace') else '❌ Missing'}
                elif test_area == 'memory':
                    results['memory'] = {'status': '✅ Available' if hasattr(self.agent, 'memory') else '❌ Missing'}
                elif test_area == 'ngrok':
                    results['ngrok'] = {'status': '✅ Available' if ngrok else '❌ Missing'}
                elif test_area == 'discord':
                    results['discord'] = {'status': '✅ Available' if hasattr(self.agent, 'discord') else '❌ Missing'}
                elif test_area == 'resources':
                    results['resources'] = {'status': '✅ Available' if hasattr(self.agent, 'resource_manager') else '❌ Missing'}
                elif test_area == 'loops':
                    # Check if loops are running
                    loop_status = await self._check_loop_health()
                    results['loops'] = loop_status
            else:
                # Full execution
                if test_area == 'tools':
                    results['tools'] = await self._test_tools()
                elif test_area == 'tools_functional':
                    results['tools_functional'] = await self._test_tools_functional()
                elif test_area == 'critical_files':
                    results['critical_files'] = await self._test_critical_files()
                elif test_area == 'llm':
                    results['llm'] = await self._test_llm()
                elif test_area == 'network':
                    results['network'] = await self._test_network()
                elif test_area == 'ngrok':
                    results['ngrok'] = await self._test_ngrok()
                elif test_area == 'database':
                    results['database'] = await self._test_database()
                elif test_area == 'filesystem':
                    results['filesystem'] = await self._test_filesystem()
                elif test_area == 'memory':
                    results['memory'] = await self._test_memory()
                elif test_area in ['code_integrity', 'code', 'compile']:
                    results['code_integrity'] = await self._test_code_integrity()
                elif test_area in ['boredom', 'discord', 'resources']:
                    # Use existing debug_info for these
                    debug_info = self.agent.get_debug_info(test_area)
                    results[test_area] = debug_info.get(test_area, {})
                
        return results

    async def cmd_debug(self, channel_id: int, args: list, user_id: int = None):
        """Comprehensive system verification and diagnostics."""
        # Admin check
        if user_id and user_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "â›” **Access Denied**: This command is restricted to administrators.")
            return

        area = args[0].lower() if args else 'quick'
        
        valid_areas = ['all', 'quick', 'deep', 'tools', 'llm', 'network', 'ngrok', 
                       'database', 'filesystem', 'memory', 'boredom', 'discord', 'resources',
                       'errors', 'logs', 'config', 'code_integrity', 'code', 'compile']
        
        if area not in valid_areas:
            # Fuzzy matching
            import difflib
            matches = difflib.get_close_matches(area, valid_areas, n=1, cutoff=0.6)
            
            if matches:
                area = matches[0]
                await self.agent.discord.send_message(channel_id, f"💊 Did you mean **{area}**? Running diagnostics for '{area}'...")
            else:
                await self.agent.discord.send_message(channel_id,
                    f"✖️ Invalid area. Use: {', '.join(valid_areas)}")
                return
        
        # Special handling for new subcommands
        if area == 'errors':
            await self._cmd_debug_errors(channel_id)
            return
        elif area == 'logs':
            # Parse args for logs
            filter_level = None
            count = 15
            if len(args) > 1:
                if args[1].isdigit():
                    count = int(args[1])
                elif args[1].lower() in ['error', 'warning', 'info', 'debug']:
                    filter_level = args[1].upper()
                    if len(args) > 2 and args[2].isdigit():
                        count = int(args[2])
            await self._cmd_debug_logs(channel_id, count, filter_level)
            return
        elif area == 'config':
            await self._cmd_debug_config(channel_id)
            return
        elif area in ['code_integrity', 'code', 'compile']:
            analyzing_msg = await self.agent.discord.send_message(
                channel_id, 
                "🔃 **Analyzing code integrity...**\n```\nRunning AST analysis...\n```"
            )
            
            try:
                # Run with timeout
                import asyncio
                results = await asyncio.wait_for(
                    self._test_code_integrity(),
                    timeout=30.0
                )
                
                # Format result as embed
                import discord
                
                if results.get('issues'):
                    # Send full report as file
                    import tempfile
                    filename = f"code_integrity_{int(time.time())}.txt"
                    temp_path = os.path.join(tempfile.gettempdir(), filename)
                    
                    try:
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write("CODE INTEGRITY CHECK REPORT\n")
                            f.write("=" * 50 + "\n\n")
                            f.write(f"Status: {results['status']}\n")
                            f.write(f"Total Issues: {len(results['issues'])}\n\n")
                            f.write("ISSUES:\n")
                            f.write("-" * 50 + "\n")
                            for i, issue in enumerate(results['issues'], 1):
                                f.write(f"{i}. {issue}\n")
                        
                        # Create embed
                        embed = discord.Embed(
                            title="🩺 Code Integrity Check",
                            description=f"**Status:** {results['status']}\n**Issues Found:** {len(results['issues'])}",
                            color=discord.Color.orange()
                        )
                        embed.add_field(name="📄 Report", value="Full report attached as file", inline=False)
                        
                        # Edit the analyzing message with embed
                        if analyzing_msg:
                            await analyzing_msg.edit(content=None, embed=embed)
                            # Send file in same channel
                            channel = analyzing_msg.channel
                            await channel.send(file=discord.File(temp_path))
                        else:
                            await self.agent.discord.send_message(
                                channel_id,
                                f"**Status:** {results['status']}\n**Issues:** {len(results['issues'])}\n📄 Full report attached.",
                                file_path=temp_path
                            )
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                else:
                    # Create success embed
                    embed = discord.Embed(
                        title="🩺 Code Integrity Check",
                        description=f"**Status:** {results['status']}\n**Issues Found:** 0",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="✅ Result", value="No issues found.", inline=False)
                    
                    # Edit the analyzing message with success embed
                    if analyzing_msg:
                        await analyzing_msg.edit(content=None, embed=embed)
                    else:
                        await self.agent.discord.send_message(
                            channel_id,
                            f"✅ **Status:** {results['status']}\n**Issues:** 0\nNo issues found."
                        )
                
            except asyncio.TimeoutError:
                await self.agent.discord.send_message(
                    channel_id,
                    "⚠️ **Code integrity check timed out** (>30s)"
                )
            except Exception as e:
                logger.error(f"Code integrity check failed: {e}", exc_info=True)
                await self.agent.discord.send_message(
                    channel_id,
                    f"✖️ **Check failed**: {str(e)}"
                )
            return
        
        await self.agent.discord.send_message(channel_id, f"🩺 Running system diagnostics ({area})...")
        
        try:
            maintenance_enabled = False
            queue_was_empty = self.queue.qsize() == 0
            
            # Enable maintenance mode for deep/all if queue is empty
            if area in ['deep', 'all'] and queue_was_empty:
                maintenance_enabled = True
                self.agent.maintenance_mode = True
                await self.agent.discord.send_message(channel_id, "⚠️ **Maintenance Mode Active**: Autonomous behaviors paused (queue empty).")
            elif area in ['deep', 'all'] and not queue_was_empty:
                await self.agent.discord.send_message(channel_id, "ℹ️ **Note**: Processes not paused (queue has pending commands).")
            
            # Run diagnostics
            results = await self._run_diagnostics(area)
            
            if maintenance_enabled:
                self.agent.maintenance_mode = False
                await self.agent.discord.send_message(channel_id, "✅ **Maintenance Mode Deactivated**: Autonomous behaviors resumed.")
            
            # Format output
            header = f"🩺 **System Diagnostics Report** ({area})\n"
            yaml_start = "```yaml\n"
            yaml_end = "```"
            
            # Construct full body first
            body = ""
            for system, data in results.items():
                body += f"{system.upper()}:\n"
                for key, value in data.items():
                    formatted_key = key.replace('_', ' ').title()
                    body += f"  {formatted_key}: {value}\n"
                body += "\n"
            
            # Check length
            if len(header) + len(yaml_start) + len(body) + len(yaml_end) > 1900:
                # Split by systems
                parts = []
                current_body = ""
                
                for system, data in results.items():
                    system_block = f"{system.upper()}:\n"
                    for key, value in data.items():
                        formatted_key = key.replace('_', ' ').title()
                        system_block += f"  {formatted_key}: {value}\n"
                    system_block += "\n"
                    
                    if len(current_body) + len(system_block) > 1800:
                        parts.append(current_body)
                        current_body = system_block
                    else:
                        current_body += system_block
                
                if current_body:
                    parts.append(current_body)
                
                await self.agent.discord.send_message(channel_id, header)
                for i, part in enumerate(parts):
                    await self.agent.discord.send_message(channel_id, f"{yaml_start}{part}{yaml_end}")
            else:
                await self.agent.discord.send_message(channel_id, f"{header}{yaml_start}{body}{yaml_end}")
                
        except Exception as e:
            logger.error(f"Diagnostics failed: {e}", exc_info=True)
            await self.agent.discord.send_message(channel_id, f"✖️ **Diagnostics Failed:** {e}")
            if maintenance_enabled:
                self.agent.maintenance_mode = False
    
    async def _test_tools(self):
        """Test all registered tools."""
        results = {}
        total_tools = len(self.agent.tools.tools)
        passed = 0
        
        for tool_name, tool in self.agent.tools.tools.items():
            try:
                # Test tool availability
                if tool:
                    passed += 1
                    results[tool_name] = "✅ Available"
                else:
                    results[tool_name] = "✖️ Not Loaded"
            except Exception as e:
                results[tool_name] = f"✖️ Error: {str(e)[:30]}"
        
        results['summary'] = f"✅ {passed}/{total_tools} tools available"
        return results
    
    async def _test_llm(self):
        """Test LLM inference capability."""
        results = {}
        start_time = time.time()
        
        try:
            if not self.agent.llm or not self.agent.llm.llm:
                results['status'] = "✖️ Not initialized"
                return results
            
            # Test inference
            response = await self.agent.llm.generate_response(
                "Reply with just the word 'OK'",
                system_prompt="You are a test system. Reply exactly as requested."
            )
            
            latency = (time.time() - start_time) * 1000
            
            if response and "OK" in response.upper():
                results['status'] = "✅ Operational"
                results['latency'] = f"{latency:.0f}ms"
                results['provider'] = getattr(self.agent.llm, 'provider_type', 'Unknown')
                results['model'] = getattr(self.agent.llm, 'model_filename', 'Unknown')
            elif response == "LLM not available.":
                results['status'] = "✖️ Unavailable"
            else:
                results['status'] = f"⚠️ Unexpected response"
                results['response'] = response[:50] if response else "None"
                
        except Exception as e:
            results['status'] = f"✖️ Error: {str(e)[:50]}"
        
        return results
    
    async def _test_network(self):
        """Test network connectivity."""
        results = {}
        
        # Test Internet (ping)
        try:
            cmd = "ping -c 1 8.8.8.8" if platform.system() != "Windows" else "ping -n 1 8.8.8.8"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            results['internet'] = "✅ Connected" if proc.returncode == 0 else "✖️ Disconnected"
        except:
            results['internet'] = "❓ Unknown"
        
        # Test DNS
        try:
            import socket
            socket.gethostbyname('google.com')
            results['dns'] = "✅ Working"
        except:
            results['dns'] = "✖️ Failed"
        
        # Test Discord API (if available)
        try:
            if self.agent.discord and hasattr(self.agent.discord, 'client'):
                if self.agent.discord.client and not self.agent.discord.client.is_closed():
                    results['discord_api'] = "✅ Connected"
                else:
                    results['discord_api'] = "✖️ Disconnected"
            else:
                results['discord_api'] = "❓ Not initialized"
        except:
            results['discord_api'] = "✖️ Error"
        
        return results
    
    async def _test_ngrok(self):
        """Test ngrok tunnel status."""
        results = {}
        
        try:
            # Check if ngrok process is running
            ngrok_running = False
            for proc in psutil.process_iter(['name']):
                try:
                    if 'ngrok' in proc.info['name'].lower():
                        ngrok_running = True
                        break
                except:
                    pass
            
            if ngrok_running:
                results['process'] = "✅ Running"
                
                # Check for active tunnels (without showing URL)
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://127.0.0.1:4040/api/tunnels', timeout=5) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                tunnels = data.get('tunnels', [])
                                if tunnels:
                                    results['tunnel'] = "✅ Active"
                                else:
                                    results['tunnel'] = "⚠️ Not Active"
                            else:
                                results['tunnel'] = "⚠️ API Error"
                except:
                    results['tunnel'] = "⚠️ Cannot reach API"
            else:
                results['process'] = "✖️ Not running"
                results['tunnel'] = "✖️ Not Active"
                
        except Exception as e:
            results['status'] = f"✖️ Error: {str(e)[:50]}"
        
        return results
    
    async def _test_database(self):
        """Test database connection and operations."""
        results = {}
        
        try:
            # Test connection
            if hasattr(self.agent, 'memory') and hasattr(self.agent.memory, 'conn'):
                results['connection'] = "✅ Connected"
                
                # Test query execution
                try:
                    cursor = self.agent.memory.conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM memories")
                    count = cursor.fetchone()[0]
                    results['query_test'] = f"✅ OK ({count} memories)"
                except Exception as e:
                    results['query_test'] = f"✖️ Query failed: {str(e)[:30]}"
                
                # Test write capability
                try:
                    test_content = f"__test__{time.time()}"
                    self.agent.memory.add_memory(
                        content=test_content,
                        metadata={"type": "system_test"}
                    )
                    results['write_test'] = "✅ OK"
                    
                    # Clean up test memory
                    cursor.execute("DELETE FROM memories WHERE content = ?", (test_content,))
                    self.agent.memory.conn.commit()
                except Exception as e:
                    results['write_test'] = f"✖️ Write failed: {str(e)[:30]}"
            else:
                results['connection'] = "✖️ Not initialized"
                
        except Exception as e:
            results['status'] = f"✖️ Error: {str(e)[:50]}"
        
        return results
    
    async def _test_filesystem(self):
        """Test filesystem read/write access."""
        results = {}
        
        # Test workspace directory
        workspace_dir = "workspace"
        test_file = os.path.join(workspace_dir, f"__test__{time.time()}.txt")
        
        try:
            # Ensure workspace exists
            os.makedirs(workspace_dir, exist_ok=True)
            results['workspace_exists'] = "✅ Yes"
            
            # Test write
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                results['write_access'] = "✅ OK"
            except Exception as e:
                results['write_access'] = f"✖️ Failed: {str(e)[:30]}"
                return results
            
            # Test read
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                if content == "test":
                    results['read_access'] = "✅ OK"
                else:
                    results['read_access'] = "⚠️ Content mismatch"
            except Exception as e:
                results['read_access'] = f"✖️ Failed: {str(e)[:30]}"
            
            # Test delete
            try:
                os.remove(test_file)
                results['delete_access'] = "✅ OK"
            except Exception as e:
                results['delete_access'] = f"✖️ Failed: {str(e)[:30]}"
                
            # Check disk space
            try:
                disk = psutil.disk_usage(workspace_dir)
                free_gb = disk.free / (1024**3)
                results['disk_space'] = f"✅ {free_gb:.1f} GB free"
            except:
                results['disk_space'] = "❓ Unknown"
                
        except Exception as e:
            results['status'] = f"✖️ Error: {str(e)[:50]}"
        
        return results
    
    async def _test_tools_functional(self):
        """Test actual execution of tools with safe commands."""
        results = {}
        
        # Define safe test cases for tools
        test_cases = {
            'math_tool': {'action': 'calc', 'expression': '1 + 1'},
            'time_tool': {'action': 'now'},
            'system_tool': {'action': 'info'},
            'code_tool': {'code': 'print("test")'},
            'translate_tool': {'text': 'hello', 'target': 'cs'},
            'weather_tool': {'location': 'London'}, # Might fail if offline
            'wikipedia_tool': {'query': 'Python (programming language)'}, # Might fail if offline
            'note_tool': {'action': 'list'}, 
            'git_tool': {'action': 'status'},
            'database_tool': {'query': 'SELECT 1'},
            'rss_tool': {'url': 'https://feeds.bbci.co.uk/news/rss.xml'}, # Needs a valid URL
            'web_tool': {'action': 'search', 'query': 'test'}, # Might fail if offline
            'file_tool': {'action': 'list_files', 'filename': '.'},
            'discord_activity_tool': {} # No args needed
        }
        
        for tool_name, tool in self.agent.tools.tools.items():
            if tool_name in test_cases:
                try:
                    # Execute with safe args
                    args = test_cases[tool_name]
                    # Timeout to prevent hanging
                    try:
                        result = await asyncio.wait_for(tool._execute_with_logging(**args), timeout=30.0)
                        # Check if result indicates success (simple check)
                        if "Error" in str(result) and "offline" not in str(result) and "unavailable" not in str(result):
                             results[tool_name] = f"⚠️ Error: {str(result)[:30]}"
                        else:
                             results[tool_name] = "✅ OK"
                    except asyncio.TimeoutError:
                        results[tool_name] = "✖️ Timeout"
                except Exception as e:
                    results[tool_name] = f"✖️ Failed: {str(e)[:30]}"
            else:
                results[tool_name] = "❓ No test case"
                
        return results

    async def _check_loop_health(self) -> dict:
        """Check if all task loops are running and restart if needed."""
        results = {}
        
        # Check if loop tasks exist and are not done
        if hasattr(self.agent, 'loop_tasks'):
            loop_names = ['boredom_loop', 'observation_loop', 'action_loop', 'backup_loop']
            loop_functions = [
                self.agent.boredom_loop,
                self.agent.observation_loop,
                self.agent.action_loop,
                self.agent.backup_loop
            ]
            
            for i, task in enumerate(self.agent.loop_tasks):
                loop_name = loop_names[i] if i < len(loop_names) else f'loop_{i}'
                
                if task.done():
                    # Loop has stopped
                    try:
                        exception = task.exception()
                        results[loop_name] = f"❌ Stopped (Exception: {exception})"
                        logger.error(f"Loop {loop_name} crashed: {exception}")
                    except:
                        results[loop_name] = "❌ Stopped"
                        logger.warning(f"Loop {loop_name} stopped without exception")
                    
                    # Auto-restart if agent is still running (not a deliberate shutdown)
                    if self.agent.is_running and i < len(loop_functions):
                        try:
                            import asyncio
                            logger.info(f"Auto-restarting {loop_name}...")
                            # Replace the dead task with a new one
                            self.agent.loop_tasks[i] = asyncio.create_task(loop_functions[i]())
                            results[loop_name] += " → 🔄 Restarted"
                            
                            # Notify admin
                            await self.agent.send_admin_dm(
                                f"⚠️ **Loop Auto-Restart**\n{loop_name} crashed and was automatically restarted.",
                                category="system"
                            )
                        except Exception as e:
                            logger.error(f"Failed to restart {loop_name}: {e}")
                            results[loop_name] += f" (Restart failed: {e})"
                else:
                    results[loop_name] = "✅ Running"
        else:
            results['status'] = "❌ Loop tasks not initialized"
            
        return results

    async def _test_memory(self) -> dict:
        """Test memory system."""
        results = {}
        
        try:
            if not hasattr(self.agent, 'memory'):
                results['status'] = "❌ Not initialized"
                return results
            
            # Count memories
            try:
                cursor = self.agent.memory.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memories")
                count = cursor.fetchone()[0]
                results['memory_count'] = f"{count} memories"
            except Exception as e:
                results['memory_count'] = f"❌ Error: {str(e)[:30]}"
            
            # Test search
            try:
                search_results = self.agent.memory.search_memory("test", limit=1)
                results['search'] = "✅ OK"
            except Exception as e:
                results['search'] = f"❌ Error: {str(e)[:30]}"
                
            results['status'] = "✅ Operational"
        except Exception as e:
            results['status'] = f"❌ Error: {str(e)[:50]}"
        
        return results


    async def _test_critical_files(self):
        """Check existence of critical project files."""
        results = {}
        
        critical_files = [
            'main.py',
            'config_secrets.py',
            'config_settings.py',
            'requirements.txt',
            'agent/core.py',
            'agent/commands.py',
            'agent/memory.py',
            'agent/llm.py',
            'agent/tools.py',
            'agent_memory.db'
        ]
        
        for filename in critical_files:
            if os.path.exists(filename):
                results[filename.replace('/', '.').title()] = "✅ OK"
            else:
                results[filename.replace('/', '.').title()] = "✖️ Missing"
                
        return results


    
    async def cmd_mood(self, channel_id: int):
        """Show AI's current mood based on metrics."""
        boredom = self.agent.boredom_score
        actions_without_tools = self.agent.actions_without_tools
        recent_learnings = self.agent.successful_learnings
        
        # Determine mood
        if boredom < 0.1 and recent_learnings > 0:
            mood = "😊 Happy"
            description = "I'm learning and staying active!"
        elif boredom < 0.3:
            mood = "😐 Neutral"
            description = "Things are okay, just going through the motions."
        elif boredom < 0.5:
            mood = "🥱 Slightly Bored"
            description = "I could use something interesting to do..."
        elif boredom < 0.7:
            mood = "😴 Bored"
            description = "Not much happening. Need stimulation!"
        else:
            mood = "😫 Very Bored"
            description = "This is getting tedious... I need to learn something!"
        
        if actions_without_tools >= 2:
            mood += " (Frustrated)"
            description += "\nI keep doing basic actions instead of using tools!"
        
        # Boredom status details
        boredom_pct = int(boredom * 100)
        threshold_pct = int(self.agent.BOREDOM_THRESHOLD_HIGH * 100)
        
        mood_text = f"""💭 **Current Mood:**

{mood}
_{description}_

**Factors:**
• Boredom: {boredom_pct}% (Threshold: {threshold_pct}%)
• Recent Tool Use: {'Yes ✅' if actions_without_tools == 0 else f'No (last {actions_without_tools} actions)'}
• Learnings: {recent_learnings}
"""
        
        await self.agent.discord.send_message(channel_id, mood_text)
    
    async def cmd_goals(self, channel_id: int, args: list, author_id: int):
        """Manage AI goals."""
        if not args:
            # Show current goals
            if not self.agent.goals:
                await self.agent.discord.send_message(channel_id, "🎯 **No goals set.**\nUse `!goals add <goal>` to add one.")
                return
            
            goals_text = "🎯 **Current Goals:**\n\n"
            for i, goal in enumerate(self.agent.goals, 1):
                goals_text += f"{i}. {goal}\n"
            goals_text += "\n💊 Use `!goals add <goal>` to add or `!goals clear` to remove all."
            await self.agent.discord.send_message(channel_id, goals_text)
            return

        # Parse subcommand
        raw_subcommand = args[0].lower()
        valid_subcommands = ["add", "remove", "clear"]
        
        subcommand = self._match_subcommand(raw_subcommand, valid_subcommands)
        
        if not subcommand:
             await self.agent.discord.send_message(channel_id, 
                "❓ Usage:\n• `!goals` - Show goals\n• `!goals add <goal>` - Add goal\n• `!goals remove <num>` - Remove goal\n• `!goals clear` - Clear all")
             return

        if subcommand != raw_subcommand:
             await self.agent.discord.send_message(channel_id, f"💡 Did you mean `{subcommand}`? Executing...")
    
        if subcommand == 'add':
            if len(args) < 2:
                 await self.agent.discord.send_message(channel_id, "✖️ Usage: `!goals add <goal>`")
                 return
            # Add new goal
            new_goal = ' '.join(args[1:])
            self.agent.goals.append(new_goal)
            await self.agent.discord.send_message(channel_id, 
                f"✅ Goal added: '{new_goal}'\n🎯 Total goals: {len(self.agent.goals)}")
        
        elif subcommand == 'clear':
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can clear all goals.")
                return

            # Clear all goals
            count = len(self.agent.goals)
            self.agent.goals = []
            await self.agent.discord.send_message(channel_id, 
                f"🗑️ Cleared {count} goals.")
        
        elif subcommand == 'remove':
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can remove goals.")
                return

            # If no number provided, show list
            if len(args) < 2:
                if not self.agent.goals:
                     await self.agent.discord.send_message(channel_id, "🎯 No goals to remove.")
                     return
                
                goals_text = "🗑️ **Select goal to remove:**\n\n"
                for i, goal in enumerate(self.agent.goals, 1):
                    goals_text += f"**{i}.** {goal}\n"
                goals_text += "\nUsage: `!goals remove <number>`"
                await self.agent.discord.send_message(channel_id, goals_text)
                return

            # Remove specific goal by number
            try:
                index = int(args[1]) - 1
                if 0 <= index < len(self.agent.goals):
                    removed = self.agent.goals.pop(index)
                    await self.agent.discord.send_message(channel_id, 
                        f"✅ Removed goal: '{removed}'")
                else:
                    await self.agent.discord.send_message(channel_id, 
                        f"✖️ Invalid goal number. Use 1-{len(self.agent.goals)}")
            except ValueError:
                await self.agent.discord.send_message(channel_id, 
                    "✖️ Invalid number. Usage: `!goals remove <number>`")
    

    async def cmd_config(self, channel_id: int, args: list, author_id: int = 0):
        """Show configuration settings (Admin only)."""
        import config_settings

        # Admin check
        if author_id not in config_settings.ADMIN_USER_IDS:
             await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can view configuration.")
             return
        
        config_text = "⚙️ **Current Configuration:**\n\n"
        
        # Iterate over settings
        for key, value in vars(config_settings).items():
            # Skip built-ins and secrets
            if key.startswith("__"): continue
            if "TOKEN" in key or "KEY" in key or "PASSWORD" in key: continue
            
            # Filter time-related if requested (optional)
            # if "TIME" in key or "INTERVAL" in key: continue
            
            # Format value
            if isinstance(value, list):
                val_str = f"[{len(value)} items]"
            else:
                val_str = str(value)
                if len(val_str) > 50: val_str = val_str[:47] + "..."
            
            config_text += f"• `{key}`: {val_str}\n"
            
        await self.agent.discord.send_message(channel_id, config_text)
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)

    async def cmd_monitor(self, channel_id: int, args: list):
        """Start system monitoring. Usage: !monitor [duration]"""
        
        # Parse duration
        duration = 0  # Default to Snapshot mode (0 seconds)
        if args:
            match = re.match(r"(\d+)([smh]?)", args[0].lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == 'm': duration = value * 60
                elif unit == 'h': duration = value * 3600
                else: duration = value
        
        # Cap duration at 1 hour
        duration = min(duration, 3600)
        is_live = duration > 0
        
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
        end_time_str = end_time.strftime("%H:%M:%S")
        
        # Initial message
        if is_live:
            msg = await self.agent.discord.send_message(channel_id, f"📸 **System Monitor Live**\nInitializing... (Runs until {end_time_str})")
        else:
            msg = await self.agent.discord.send_message(channel_id, f"📸 **System Snapshot**\nGathering data...")
            
        if not msg:
            return

        # Start monitoring loop
        if is_live:
            # Run in background to avoid blocking
            asyncio.create_task(self._monitor_loop(msg, end_time, is_live=True))
        else:
            # Run once and wait
            await self._monitor_loop(msg, end_time, is_live=False)

    async def _monitor_loop(self, msg, end_time, is_live):
        """Internal loop for system monitoring."""
        
        # Helper for progress bar
        def create_bar(percent, length=20):
            filled = int(length * percent / 100)
            return "█" * filled + "░" * (length - filled)

        # Helper for CPU model
        def get_cpu_model():
            try:
                if platform.system() == "Windows":
                    command = "wmic cpu get name"
                    output = subprocess.check_output(command, shell=True).decode().strip()
                    return output.split('\n')[1].strip()
                elif platform.system() == "Linux":
                    command = "cat /proc/cpuinfo | grep 'model name' | uniq"
                    output = subprocess.check_output(command, shell=True).decode().strip()
                    return output.split(':')[1].strip()
                return platform.processor()
            except:
                return "Unknown CPU"

        # Helper for GPU info
        def get_gpu_info():
            gpu_data = {'name': 'Unknown GPU', 'util': None, 'mem_used': 0, 'mem_total': 0}
            
            # 1. Try nvidia-smi for full stats
            try:
                output = subprocess.check_output(
                    "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits", 
                    shell=True
                ).decode().strip()
                name, util, mem_used, mem_total = output.split(', ')
                gpu_data = {
                    'name': name,
                    'util': int(util),
                    'mem_used': int(mem_used),
                    'mem_total': int(mem_total)
                }
                return gpu_data
            except:
                pass
            
            # 2. Fallback to wmic for name only (Windows)
            try:
                if platform.system() == "Windows":
                    command = "wmic path win32_VideoController get name"
                    output = subprocess.check_output(command, shell=True).decode().strip()
                    lines = [line.strip() for line in output.split('\n') if line.strip() and 'Name' not in line]
                    # Filter out virtual adapters
                    real_gpus = [g for g in lines if 'Virtual' not in g and 'Remote' not in g]
                    if real_gpus:
                        gpu_data['name'] = real_gpus[0] # Take first real GPU
            except:
                pass
                
            return gpu_data

        cpu_model = get_cpu_model()
        last_net_io = psutil.net_io_counters()
        last_time = time.time()
        end_time_str = end_time.strftime("%H:%M:%S")
        
        # If live mode, we need a small delay to calc net speed for first frame
        if not is_live:
            await asyncio.sleep(0.5) 

        # Update loop
        while True:
            try:
                # 1. CPU
                cpu_percent = psutil.cpu_percent(interval=None)
                
                # 2. RAM
                ram = psutil.virtual_memory()
                ram_gb_used = ram.used / (1024**3)
                ram_gb_total = ram.total / (1024**3)
                
                # 3. GPU
                gpu_info = get_gpu_info()
                
                # 4. Disks
                disk_str = ""
                for part in psutil.disk_partitions():
                    if 'cdrom' in part.opts or part.fstype == '':
                        continue
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        free_gb = usage.free / (1024**3)
                        disk_bar = create_bar(usage.percent, 10)
                        disk_str += f"  {part.device:<3} [{disk_bar}] {usage.percent:>3}% (Free: {free_gb:.0f}GB)\n"
                    except:
                        pass

                # 5. Network Speed
                current_net_io = psutil.net_io_counters()
                current_time = time.time()
                time_delta = current_time - last_time
                
                if time_delta > 0:
                    sent_speed = (current_net_io.bytes_sent - last_net_io.bytes_sent) / time_delta / 1024 # KB/s
                    recv_speed = (current_net_io.bytes_recv - last_net_io.bytes_recv) / time_delta / 1024 # KB/s
                else:
                    sent_speed = 0
                    recv_speed = 0
                
                last_net_io = current_net_io
                last_time = current_time
                
                # Format speed
                def fmt_speed(kb):
                    return f"{kb/1024:.1f} MB/s" if kb > 1000 else f"{kb:.1f} KB/s"

                # 6. Uptime
                boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.datetime.now() - boot_time
                uptime_str = str(uptime).split('.')[0]

                # Build Dashboard
                dashboard = "```yaml\n[SYSTEM RESOURCES]\n"
                
                # CPU Section
                dashboard += f"CPU:  [{create_bar(cpu_percent)}] {cpu_percent:>3}%\n"
                dashboard += f"      {cpu_model}\n"
                
                # RAM Section
                dashboard += f"RAM:  [{create_bar(ram.percent)}] {ram.percent:>3}% ({ram_gb_used:.1f}/{ram_gb_total:.1f} GB)\n"
                
                # GPU Section
                if gpu_info['util'] is not None:
                    gpu_bar = create_bar(gpu_info['util'])
                    dashboard += f"GPU:  [{gpu_bar}] {gpu_info['util']:>3}% ({gpu_info['mem_used']}/{gpu_info['mem_total']} MB)\n"
                else:
                    dashboard += f"GPU:  [░░░░░░░░░░░░░░░░░░░░] N/A%\n"
                dashboard += f"      {gpu_info['name']}\n"
                
                # Disk Section
                dashboard += f"DISK:\n{disk_str}"
                
                # Network & Uptime
                dashboard += f"NET:  ⬇️ {fmt_speed(recv_speed)} | ⬆️ {fmt_speed(sent_speed)}\n"
                dashboard += f"UPTIME: {uptime_str}\n"
                
                dashboard += f"\nLast Update: {datetime.datetime.now().strftime('%H:%M:%S')}\n```"
                
                # Update message
                if is_live:
                    try:
                        await msg.edit(content=f"📊 **System Monitor Live** (Ends: {end_time_str})\n{dashboard}")
                    except discord.NotFound:
                        # Message deleted, send new one
                        new_msg = await self.agent.discord.send_message(msg.channel.id, f"📊 **System Monitor Live** (Ends: {end_time_str})\n{dashboard}")
                        if new_msg:
                            msg = new_msg
                        else:
                            break
                    except Exception:
                        break
                else:
                    await msg.edit(content=f"📷 **System Snapshot**\n{dashboard}")
                    break # Exit loop for snapshot
                
                # Check if time is up
                if datetime.datetime.now() >= end_time:
                    if is_live:
                        await msg.edit(content=f"📊 **System Monitor Finished**\n{dashboard}")
                    break
                
                await asyncio.sleep(2) # Fixed 2s interval
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                break

    async def _auto_hide_message(self, message, delay):
        """Hides a message after a delay by editing it."""
        await asyncio.sleep(delay)
        try:
            await message.edit(content="🔒 _Message hidden for security_")
        except:
            pass

    async def start_ssh_tunnel(self, channel_id: Optional[int] = None):
        """Starts the SSH tunnel and notifies."""
        if self.ngrok_process is not None:
            if channel_id:
                await self.agent.discord.send_message(channel_id, "ℹ️ SSH tunnel is already running.")
            return

        # Cleanup removed to support dual tunnels (SSH + Web)
        # Cleanup happens on Agent Startup/Shutdown only

        if not ngrok:
            if channel_id:
                await self.agent.discord.send_message(channel_id, "⚠️ Pyngrok not installed.")
            return

        if channel_id:
            await self.agent.discord.send_message(channel_id, "🔧 Starting ngrok SSH tunnel (via pyngrok)...")
        
        try:
            # Start ngrok tunnel via pyngrok in executor to avoid blocking
            # This uses the same process as the web interface!
            loop = asyncio.get_running_loop()
            
            # Use run_in_executor for blocking ngrok.connect
            # Note: ngrok.connect might not be thread-safe if pyngrok isn't, but usually it is for separate tunnels
            self.ngrok_process = await loop.run_in_executor(None, lambda: ngrok.connect(22, "tcp"))
            
            logger.info(f"SSH tunnel started: {self.ngrok_process.public_url}")
            
            # Register as protected process (ngrok process itself)
            # We need to find the actual ngrok process ID
            # pyngrok manages the process, we can try to get it
            ngrok_proc = await loop.run_in_executor(None, ngrok.get_ngrok_process)
            if ngrok_proc and hasattr(self.agent, 'resource_manager'):
                self.agent.resource_manager.register_protected_process(
                    ngrok_proc.proc.pid,
                    "ngrok"
                )
                logger.info(f"Ngrok process registered as protected (PID: {ngrok_proc.proc.pid})")
            
        except Exception as e:
            logger.exception("SSH tunnel setup failed")
            if channel_id:
                await self.agent.discord.send_message(channel_id, f"✖️ Failed to start ngrok: {e}")
            self.ngrok_process = None
            return

        # Notify - Wait for Discord to be ready if no channel_id specified (startup mode)
        if not channel_id:
            # Wait up to 60s for Discord
            for _ in range(60):
                if self.agent.discord.is_ready:
                    break
                await asyncio.sleep(1)
        
        await self._notify_ssh_info(channel_id)

    async def _kill_ngrok_processes(self):
        """Kills any running ngrok processes to free up session limits."""
        logger.info("Cleaning up ngrok processes...")
        
        # 1. Soft Stop via pyngrok
        try:
            if self.ngrok_process:
                ngrok.kill()
                self.ngrok_process = None
        except Exception:
            pass

        # 2. System-level Soft Stop (SIGTERM)
        import psutil
        try:
            procs_found = []
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'ngrok' in proc.info['name'].lower():
                    procs_found.append(proc)
                    try:
                        logger.info(f"Soft killing ngrok process {proc.info['pid']}...")
                        proc.terminate()
                    except Exception as e:
                        logger.warning(f"Failed to soft kill {proc.info['pid']}: {e}")
            
            if procs_found:
                await asyncio.sleep(1.0) # Wait for cleanup
                
                # 3. Force Kill (SIGKILL) if still alive
                for proc in procs_found:
                    if proc.is_running():
                        try:
                            logger.warning(f"Force killing stubborn ngrok process {proc.info['pid']}...")
                            proc.kill()
                        except Exception as e:
                             logger.error(f"Failed to force kill {proc.info['pid']}: {e}")
        except Exception as e:
            logger.error(f"Error during ngrok cleanup: {e}")


    class SSHView(discord.ui.View):
        def __init__(self, command_handler, ssh_command, net_use_command):
            super().__init__(timeout=300)
            self.command_handler = command_handler
            self.ssh_command = ssh_command
            self.net_use_command = net_use_command

        @discord.ui.button(label="📋 Copy SSH", style=discord.ButtonStyle.primary)
        async def copy_ssh(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in config_settings.ADMIN_USER_IDS:
                await interaction.response.send_message("⛔ Access Denied: Admin only.", ephemeral=True)
                return
            await interaction.response.send_message(f"```{self.ssh_command}```", ephemeral=True)

        @discord.ui.button(label="📋 Copy Net Use", style=discord.ButtonStyle.secondary)
        async def copy_net_use(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in config_settings.ADMIN_USER_IDS:
                await interaction.response.send_message("⛔ Access Denied: Admin only.", ephemeral=True)
                return
            await interaction.response.send_message(f"```{self.net_use_command}```", ephemeral=True)

    async def _notify_ssh_info(self, channel_id: Optional[int] = None):
        """Queries ngrok and sends SSH info."""
        public_url = None
        
        # 1. Try to get from stored tunnel object
        if self.ngrok_process and hasattr(self.ngrok_process, 'public_url'):
            public_url = self.ngrok_process.public_url
        
        # 2. Fallback: Query pyngrok for any TCP tunnel
        if not public_url and ngrok:
            try:
                loop = asyncio.get_running_loop()
                tunnels = await loop.run_in_executor(None, ngrok.get_tunnels)
                for t in tunnels:
                    if t.proto == "tcp":
                        public_url = t.public_url
                        # Update reference
                        self.ngrok_process = t
                        break
            except Exception as e:
                logger.error(f"Failed to get tunnels from pyngrok: {e}")

        if not public_url:
            if channel_id:
                await self.agent.discord.send_message(channel_id, "❌ Could not find active SSH tunnel.")
            return

        # Parse URL (tcp://0.tcp.ngrok.io:12345 -> host, port)
        # Remove tcp:// prefix
        clean_url = public_url.replace("tcp://", "")
        try:
            host, port = clean_url.split(":")
        except ValueError:
            logger.error(f"Failed to parse public URL: {public_url}")
            if channel_id:
                await self.agent.discord.send_message(channel_id, f"❌ Failed to parse URL: {public_url}")
            return
        
        ssh_command = f"ssh davca@{host} -p {port}"
        net_use_command = f'cmd /c "for %i in (Z Y X W V U T S R Q P O N M L K J I H G F E D B A) do @if not exist %i:\\\\ (net use %i: \\\\\\\\sshfs\\\\davca@{host}!{port} /user:davca && exit)"'

        
        message = "✅ **SSH Tunnel Established!**\nKlikněte na tlačítka pro zobrazení příkazů."
        
        if channel_id:
            view = self.SSHView(self, ssh_command, net_use_command)
            await self.agent.discord.send_message(channel_id, message, view=view)
        else:
            # Send to admin DM if no channel specified (Startup)
            # Send commands directly as text blocks for easy copying on mobile/startup WITHOUT buttons
            try:
                 # Shorten simpler message
                startup_msg = (
                    f"✅ **SSH Ready** (`{host}:{port}`)\n\n"
                    f"**Terminal:**\n`{ssh_command}`\n\n"
                    f"**Mount:**\n`{net_use_command}`"
                )
                await self.agent.send_admin_dm(startup_msg, category="ssh")
            except Exception as e:
                logger.error(f"Failed to send Admin DM: {e}")

    async def cmd_ssh(self, channel_id: int, author_id: int, args: list = None):
        if author_id not in config_settings.ADMIN_USER_IDS:
             await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can manage SSH tunnel.")
             return
        
        # Parse subcommand
        raw_subcommand = args[0].lower() if args else "start"
        valid_subcommands = ["start", "stop", "restart", "status"]
        
        subcommand = self._match_subcommand(raw_subcommand, valid_subcommands)
        
    async def run_quick_debug(self):
        """Runs a quick diagnostic check for crash reports."""
        report = []
        try:
            # 1. Check Internet
            is_online = await self.agent.network_monitor.check_connectivity()
            report.append(f"• **Network:** {'✅ Online' if is_online else '❌ Offline'}")
            
            # 2. Check Disk Space
            usage = self.agent.resource_manager.check_resources()
            report.append(f"• **Disk:** {usage.disk_percent}% used")
            
            # 3. Check Memory
            report.append(f"• **RAM:** {usage.ram_percent}% used")
            
            # 4. Check API Latency (Mock)
            start = time.time()
            # Just measure internal loop responsiveness for now
            await asyncio.sleep(0.01)
            latency = (time.time() - start) * 1000
            report.append(f"• **Loop Latency:** {latency:.1f}ms")
            
            return "\n".join(report)
        except Exception as e:
            return f"Diagnostic failed: {e}"

    async def run_startup_diagnostics(self):
        """Runs simplified diagnostics for startup/restart."""
        report = []
        
        # 1. Syntax Check (Compile)
        try:
            import compileall
            import io
            import sys
            
            # Capture stdout to avoid clutter
            # We just want to know if it passed
            files_scanned = 0
            failed = False
            
            agent_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Compile logic - manually walk to count files
            for root, dirs, files in os.walk(agent_dir):
                for file in files:
                    if file.endswith(".py"):
                        files_scanned += 1
                        try:
                            import py_compile
                            py_compile.compile(os.path.join(root, file), doraise=True)
                        except Exception:
                            failed = True
            
            status = "✅ OK" if not failed else "⚠️ Issues Found"
            report.append(f"• **Compilation:** {status} ({files_scanned} files)")
            
        except Exception as e:
            report.append(f"• **Compilation:** ⚠️ Error ({e})")

        # 2. Tool Test
        try:
            tool_count = len(self.agent.tools.tools)
            report.append(f"• **Tools:** ✅ Loaded ({tool_count} tools)")
        except:
             report.append("• **Tools:** ⚠️ Error")

        # 3. SSH/Ngrok Status
        try:
            ssh_status = "❌ Inactive"
            if self.ngrok_process or (ngrok and len(ngrok.get_tunnels()) > 0):
                 ssh_status = "✅ Active"
            report.append(f"• **SSH Tunnel:** {ssh_status}")
        except:
            report.append("• **SSH Tunnel:** ❓ Unknown")
        
        # 4. Loop Health Check
        try:
            loop_health = await self._check_loop_health()
            running_loops = sum(1 for status in loop_health.values() if '✅' in str(status))
            total_loops = len(loop_health)
            report.append(f"• **Task Loops:** {running_loops}/{total_loops} running")
        except Exception as e:
            report.append(f"• **Task Loops:** ❓ Error ({e})")
            
        return "\n".join(report)

    async def cmd_ssh(self, channel_id: int, author_id: int, args: list = None):
        
        # Parse subcommand
        raw_subcommand = args[0].lower() if args else "start"
        valid_subcommands = ["start", "stop", "restart", "status"]
        
        subcommand = self._match_subcommand(raw_subcommand, valid_subcommands)

        if subcommand != raw_subcommand:
             await self.agent.discord.send_message(channel_id, f"💡 Did you mean `{subcommand}`? Executing...")
        
        if subcommand == "stop":
            # Admin check for destructive action
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** You are not authorized to stop the tunnel.")
                return

            # Stop ngrok tunnel
            if self.ngrok_process is None:
                await self.agent.discord.send_message(channel_id, "ℹ️ No SSH tunnel is currently running.")
                return
            
            try:
                # Disconnect using pyngrok
                if hasattr(self.ngrok_process, 'public_url'):
                    ngrok.disconnect(self.ngrok_process.public_url)
                else:
                    # Fallback if it's not a proper object (shouldn't happen with new logic)
                    pass
                
                self.ngrok_process = None
                await self.agent.discord.send_message(channel_id, "✅ SSH tunnel stopped.")
                logger.info("SSH tunnel stopped")
            except Exception as e:
                logger.error(f"Error stopping SSH tunnel: {e}")
                await self.agent.discord.send_message(channel_id, f"✖️ Error stopping tunnel: {e}")
            return
        
        elif subcommand == "restart":
            # Admin check for destructive action
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** You are not authorized to restart the tunnel.")
                return

            # Restart ngrok tunnel
            if self.ngrok_process is not None:
                try:
                    # Properly disconnect ngrok tunnel using pyngrok API
                    if hasattr(self.ngrok_process, 'public_url'):
                        ngrok.disconnect(self.ngrok_process.public_url)
                    self.ngrok_process = None
                    await asyncio.sleep(1)
                    await self.agent.discord.send_message(channel_id, "🔄 Restarting SSH tunnel...")
                except Exception as e:
                    logger.error(f"Error stopping old tunnel: {e}")
            else:
                await self.agent.discord.send_message(channel_id, "🔄 Starting SSH tunnel...")
            # Fall through to start
        
        elif subcommand == "start" or not args:
            # Check if already running
            if self.ngrok_process is not None:
                # If running, allow anyone to see status
                await self._notify_ssh_info(channel_id)
                return
            else:
                # If NOT running, only admin can start
                if author_id not in config_settings.ADMIN_USER_IDS:
                    await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** You are not authorized to start the tunnel.")
                    return
                # Proceed to start
        else:
            await self.agent.discord.send_message(channel_id, "❓ Usage: `!ssh [start|stop|restart]`")
            return
        
        # Start ngrok tunnel
        await self.start_ssh_tunnel(channel_id)
    
    def _extract_ssh_command(self, ngrok_output: str, username: str = "davca") -> str:
        """Extract SSH command from ngrok output or URL.
        
        Args:
            ngrok_output: Ngrok output text or URL (e.g. 'tcp://4.tcp.eu.ngrok.io:12633')
            username: SSH username (default: 'davca')
            
        Returns:
            SSH command string or error message
        """
        # Hledáme vzor: tcp://<adresa>:<port>
        pattern = r'tcp://(.*?):(\d+)'
        match = re.search(pattern, ngrok_output)
        
        if match:
            address = match.group(1)
            port = match.group(2)
            return f"ssh {username}@{address} -p {port}"
        else:
            return "Adresa tcp:// nebyla ve výstupu nalezena."

    async def cmd_topic(self, channel_id: int, args: list, author_id: int):
        """Manage conversation topics. Usage: !topic [add|remove|list|clear] <topic>"""
        if not args:
            await self.cmd_topic(channel_id, ["list"], author_id)
            return

        subcommand = args[0].lower()
        topic_text = " ".join(args[1:]) if len(args) > 1 else None
        
        # Load topics
        topics_file = getattr(config_settings, 'TOPICS_FILE', 'boredom_topics.json')
        topics = []
        if os.path.exists(topics_file):
            try:
                with open(topics_file, 'r', encoding='utf-8') as f:
                    topics = json.load(f)
            except Exception as e:
                logger.error(f"Error loading topics: {e}")
        
        if subcommand == "list":
            if not topics:
                 await self.agent.discord.send_message(channel_id, "ℹ️ No topics defined.")
            else:
                 # Numbered list
                 topic_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(topics)])
                 await self.agent.discord.send_message(channel_id, f"📝 **Current Topics:**\n{topic_list}")
            return
            
        # Admin check for modification
        if author_id not in config_settings.ADMIN_USER_IDS:
             await self.agent.discord.send_message(channel_id, "⛔ Modification of topics is restricted to admins.")
             return

        if subcommand == "add":
            if not topic_text:
                await self.agent.discord.send_message(channel_id, "❓ Usage: `!topic add <topic text>`")
                return
            
            if topic_text not in topics:
                topics.append(topic_text)
                with open(topics_file, 'w', encoding='utf-8') as f:
                    json.dump(topics, f, indent=2)
                await self.agent.discord.send_message(channel_id, f"✅ Topic added: `{topic_text}`")
            else:
                await self.agent.discord.send_message(channel_id, f"ℹ️ Topic already exists: `{topic_text}`")
        
        elif subcommand == "remove":
             if author_id not in config_settings.ADMIN_USER_IDS:
                 await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can remove topics.")
                 return

             if not topic_text:
                await self.agent.discord.send_message(channel_id, "❓ Usage: `!topic remove <topic text or index>`")
                return
             
             # Try remove by index
             if topic_text.isdigit():
                 idx = int(topic_text) - 1
                 if 0 <= idx < len(topics):
                     removed = topics.pop(idx)
                     with open(topics_file, 'w', encoding='utf-8') as f:
                        json.dump(topics, f, indent=2)
                     await self.agent.discord.send_message(channel_id, f"✅ Topic removed: `{removed}`")
                     return
                 else:
                     await self.agent.discord.send_message(channel_id, f"✖️ Invalid index: {topic_text}. Range: 1-{len(topics)}")
                     return

             # Try remove by text
             if topic_text in topics:
                 topics.remove(topic_text)
                 with open(topics_file, 'w', encoding='utf-8') as f:
                    json.dump(topics, f, indent=2)
                 await self.agent.discord.send_message(channel_id, f"✅ Topic removed: `{topic_text}`")
             else:
                 await self.agent.discord.send_message(channel_id, f"✖️ Topic not found: `{topic_text}`")
                 
        elif subcommand == "clear":
             if author_id not in config_settings.ADMIN_USER_IDS:
                 await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can clear all topics.")
                 return

             topics = []
             with open(topics_file, 'w', encoding='utf-8') as f:
                json.dump(topics, f, indent=2)
             await self.agent.discord.send_message(channel_id, "✅ All topics cleared.")
             
        else:
             # Implicit add for convenience if not a recognized command
             full_text = " ".join(args)
             if full_text not in topics:
                  topics.append(full_text)
                  with open(topics_file, 'w', encoding='utf-8') as f:
                      json.dump(topics, f, indent=2)
                  await self.agent.discord.send_message(channel_id, f"✅ Topic added: `{full_text}`")
             else:
                  await self.agent.discord.send_message(channel_id, f"ℹ️ Topic already exists: `{full_text}`")

    async def cmd_cmd(self, channel_id: int, command: str, author_id: int):
        """Execute shell command (Restricted)."""
        
        logger.info(f"cmd_cmd called with command: {command}")
            
        if not command:
            # Get OS info for display
            sys_name = platform.system()
            release = platform.release().replace("+rpt-rpi-v8", "")
            distro = ""
            if sys_name == "Linux":
                try:
                    if os.path.exists('/etc/os-release'):
                        with open('/etc/os-release') as f:
                            content = f.read()
                            match = re.search(r'^PRETTY_NAME=["\']?([^"\'\n\r]+)["\']?', content, re.MULTILINE)
                            if match:
                                distro = match.group(1)
                            else:
                                match = re.search(r'^ID=["\']?([^"\'\n\r]+)["\']?', content, re.MULTILINE)
                                if match:
                                    distro = match.group(1)
                except:
                    pass
            
            os_info = f"{distro} ({sys_name} {release})" if distro else f"{sys_name} {release}"

            await self.agent.discord.send_message(channel_id, f"💻 Usage: `!cmd <command>`\nℹ️ **System:** {os_info}")
            return

        # Check if non-admin is trying to use restricted commands
        if author_id not in config_settings.ADMIN_USER_IDS:
            command_lower = command.lower()
            for pattern in config_settings.ONLY_ADMIN_RESTRICTED_COMMANDS:
                if pattern in command_lower:
                    await self.agent.discord.send_message(
                        channel_id, 
                        f"⛔ **Access Denied.** This command is restricted to admins: `{pattern.strip()}`\n"
                        f"🛡️ Allowed: Basic read-only commands (ls, pwd, whoami, date, etc.)"
                    )
                    logger.warning(f"Non-admin user {author_id} attempted restricted command: {command}")
                    return
            
        logger.info("Sending executing message...")
        await self.agent.discord.send_message(channel_id, f"💻 Executing: `{command}`...")
        
        try:
             # Run asynchronously
             process = await asyncio.create_subprocess_shell(
                 command,
                 stdout=asyncio.subprocess.PIPE,
                 stderr=asyncio.subprocess.PIPE
             )
             stdout, stderr = await process.communicate()
             
             output = stdout.decode('utf-8', errors='replace').strip()
             error = stderr.decode('utf-8', errors='replace').strip()
             
             if output:
                 if len(output) > 1900:
                     # Send as file
                     import tempfile
                     filename = f"cmd_output_{int(time.time())}.txt"
                     temp_path = os.path.join(tempfile.gettempdir(), filename)
                     try:
                         with open(temp_path, 'w', encoding='utf-8') as f:
                             f.write(output)
                         await self.agent.discord.send_message(channel_id, "📄 Output too long, sending as file:", file_path=temp_path)
                     finally:
                         if os.path.exists(temp_path):
                             os.remove(temp_path)
                 else:
                     await self.agent.discord.send_message(channel_id, f"```\n{output}\n```")
             
             if error:
                 await self.agent.discord.send_message(channel_id, f"⚠️ **Stderr:**\n```\n{error}\n```")
                 
             if not output and not error:
                 await self.agent.discord.send_message(channel_id, "✅ Command executed (no output).")
                 
        except Exception as e:
             logger.error(f"Error executing shell command: {e}")
             await self.agent.discord.send_message(channel_id, f"❌ Execution failed: {e}")