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

    @discord.ui.button(label="Zobrazit detailní statistiky", style=discord.ButtonStyle.primary, emoji="📊")
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the response first to avoid timeout
        await interaction.response.defer()
        # Execute !stats command in the channel (visible to everyone)
        await self.command_handler.cmd_stats(interaction.channel_id)

class CommandHandler:
    """Handles Discord bot commands."""
    
    # List of all valid commands for fuzzy matching
    VALID_COMMANDS = [
        "!help", "!status", "!intelligence", "!inteligence", "!restart", "!learn",
        "!memory", "!tools", "!logs", "!stats", "!export", "!ask",
        "!teach", "!search", "!mood", "!goals", "!config", "!monitor", "!ssh", "!cmd", "!live", "!topic",
        "!documentation", "!docs", "!report"
    ]
    
    def __init__(self, agent):
        self.agent = agent
        self.ngrok_process = None  # Track running ngrok process
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.is_running = False
        self.last_user_command = None # Track last command for reporting

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
                    await self._execute_command(msg)
                except Exception as e:
                    logger.error(f"Error executing command: {e}", exc_info=True)
                    channel_id = msg.get('channel_id')
                    if channel_id:
                        await self.agent.discord.send_message(channel_id, f"✖️ Internal error executing command: {e}")
                finally:
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in command worker loop: {e}")
                await asyncio.sleep(1)

    async def handle_command(self, msg: dict):
        """Enqueue a command for processing."""
        q_size = self.queue.qsize()
        
        # Add to queue
        await self.queue.put(msg)
        
        # Feedback if queue is busy
        if q_size > 0:
            logger.info(f"Command queued (Position: {q_size + 1})")
            # Optional: Add reaction to indicate queued status if possible
            # await self.agent.discord.add_reaction(msg['id'], msg['channel_id'], "âŹł")

    async def _execute_command(self, msg: dict):
        """Execute the command logic (internal)."""
        content = msg['content'].strip()
        channel_id = msg['channel_id']
        author = msg['author']
        author_id = msg.get('author_id', 0)
        
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
        command = original_command
        if command not in self.VALID_COMMANDS:
            # Find closest match
            closest_match = None
            min_distance = float('inf')
            
            for valid_cmd in self.VALID_COMMANDS:
                distance = levenshtein_distance(command, valid_cmd)
                # Only auto-correct if distance is small (1-2 characters different)
                if distance < min_distance and distance <= 2:
                    min_distance = distance
                    closest_match = valid_cmd
            
            if closest_match:
                # Auto-correct the command
                logger.info(f"Auto-correcting '{original_command}' → '{closest_match}' (distance: {min_distance})")
                await self.agent.discord.send_message(channel_id, 
                    f"💊 Did you mean `{closest_match}`? (auto-correcting '{original_command}')")
                command = closest_match
        
        # Route to appropriate handler
        if command == "!help":
            await self.cmd_help(channel_id)
        elif command == "!status":
            await self.cmd_status(channel_id)
        elif command == "!inteligence" or command == "!intelligence":
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
            await self.cmd_goals(channel_id, args)
        elif command == "!config":
            await self.cmd_config(channel_id, args)
        elif command == "!monitor":
            await self.cmd_monitor(channel_id, args)
        elif command == "!ssh":
            await self.cmd_ssh(channel_id, author_id, args)
        elif command == "!cmd":
            await self.cmd_cmd(channel_id, ' '.join(args), author_id)
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
        elif command == "!topic":
            await self.cmd_topic(channel_id, args, author_id)
        elif command in ["!documentation", "!docs"]:
            await self.cmd_documentation(channel_id)
        elif command == "!report":
            await self.cmd_report(channel_id, author_id)
        else:
            await self.agent.discord.send_message(channel_id, f"❓ Unknown command: {command}. Use `!help` for available commands.")
    
    async def cmd_help(self, channel_id: int):
        """Show all available commands with friendly formatting and categories."""
        help_text = """
🤖 **AI Agent - Nápověda Příkazů**

📋 **BASIC**
`!help` `!status` `!stats` `!intelligence` `!mood` `!config`

🎓 **LEARNING & TOOLS**
`!learn [tool|all]` - Naučí nástroje
`!tools` - Seznam nástrojů
`!ask <otázka>` - Zeptej se (paměť + nástroje)
`!teach <text>` - Nauč něco nového
`!search <dotaz>` - Vyhledej info

💾 **DATA**
`!memory [dump]` - Statistiky paměti
`!logs [počet] [ERROR|WARNING|INFO]` - Zobraz logy
`!live logs [1m|5m|10m|1h]` - Živý stream
`!export [history|memory|stats|all]` - Export dat
`!topic [add|remove|clear] [...]` - Témata (⛔ admin)
`!docs` - Dokumentace

💬 **INTERACTION**
`!goals [add|remove|clear] [...]` - Správa cílů

⚙️ **ADMIN** (🔐 oprávnění)
`!restart` - Restart agenta
`!monitor [cpu|ram|disk|network]` - Monitoring
`!debug [quick|deep]` - Diagnostika
`!ssh [start|stop|status]` - SSH tunel
`!cmd <příkaz>` - Shell (⚠️ omezené)

💡 Syntaxe: <povinné> [nepovinné|možnosti]
        """
        
        await self.agent.discord.send_message(channel_id, help_text.strip())
    
    class StatusView(discord.ui.View):
        def __init__(self, command_handler):
            super().__init__(timeout=60)
            self.command_handler = command_handler

        @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.primary)
        async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            await self.command_handler.cmd_status(interaction.channel_id)

    async def cmd_status(self, channel_id: int):
        """Show agent status with system info and health checks."""
        # Get system info
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
        """Show intelligence metrics."""
        # Calculate intelligence score (0-100)
        tool_diversity = len(self.agent.tool_usage_count)  # How many different tools used
        total_tool_uses = sum(self.agent.tool_usage_count.values())
        successful_learns = self.agent.successful_learnings
        
        # Simple formula: diversity + usage + learnings
        intelligence = min(100, (tool_diversity * 10) + (total_tool_uses * 2) + (successful_learns * 5))
        
        intel_text = f"""🧠 **Intelligence Metrics:**

**Overall Intelligence:** {intelligence}/100
• Tool Diversity: {tool_diversity} different tools
• Total Tool Uses: {total_tool_uses}
• Successful Learnings: {successful_learns}

**Analysis:** """
        
        if intelligence < 20:
            intel_text += "Very low - Just starting out"
        elif intelligence < 50:
            intel_text += "Low - Learning the basics"
        elif intelligence < 75:
            intel_text += "Moderate - Getting smarter!"
        else:
            intel_text += "High - Very capable!"
        
        await self.agent.discord.send_message(channel_id, intel_text)
    
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
            
            # Show error with buttons instead of automatic force restart
            import discord
            
            class RestartConfirmView(discord.ui.View):
                def __init__(self, command_handler):
                    super().__init__(timeout=60.0)  # 60 second timeout
                    self.command_handler = command_handler
                
                @discord.ui.button(label="Force Restart", style=discord.ButtonStyle.danger, emoji="☢️")
                async def force_restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Admin-only check
                    if interaction.user.id not in config_settings.ADMIN_USER_IDS:
                        await interaction.response.send_message("â›” Admin only", ephemeral=True)
                        return
                    
                    await interaction.response.send_message("☢️ **Forcing restart...**", ephemeral=True)
                    
                    import os
                    import sys
                    logger.warning(f"Force restart initiated by {interaction.user.name}")
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                
                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="✖️")
                async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Admin-only check
                    if interaction.user.id not in config_settings.ADMIN_USER_IDS:
                        await interaction.response.send_message("â›” Admin only", ephemeral=True)
                        return
                    
                    await interaction.response.send_message("✅ Restart cancelled", ephemeral=True)
                    # Remove restart flag since we're not restarting
                    if os.path.exists(".restart_flag"):
                        os.remove(".restart_flag")
                    self.stop()
            
            view = RestartConfirmView(self)
            
            await self.agent.discord.send_message(
                channel_id,
                "⚠️ **Graceful shutdown failed or timed out**\n\n"
                "Some resources may not have closed properly.\n"
                "Choose an option:",
                view=view
            )
            return
        
        # Graceful shutdown succeeded, proceed with restart
        import os
        import sys
        
        logger.info("Restarting Python process...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    async def cmd_learn(self, channel_id: int, args: list = None):
        """Force AI to learn. Usage: !learn [tool_name|all|stop]"""
        
        if not args:
            # Single forced learning (original behavior)
            await self.agent.discord.send_message(channel_id, "🎓 Forcing single learning session...")
            self.agent.actions_without_tools = 2
            self.agent.boredom_score = 1.0 # Force immediate action
            await self.agent.discord.send_message(channel_id, "✅ Learning forced. I will try to learn something new now.")
            return

        subcommand = args[0].lower()
        
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
        # Handle partial matches or exact matches
        if tool_name not in self.agent.tools.tools:
            # Try to find close match
            for t in self.agent.tools.tools:
                if tool_name in t:
                    tool_name = t
                    break
        
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
        mem_count = len(self.agent.memory.get_recent_memories(limit=1000))
        
        mem_text = f"""💾 **Memory Statistics:**

• Total Memories: {mem_count}
• Action History: {len(self.agent.action_history)} entries

🚧 More detailed memory stats coming soon!"""
        
        await self.agent.discord.send_message(channel_id, mem_text)
    
    async def cmd_tools(self, channel_id: int):
        """Show available tools and usage."""
        tool_text = "🛠️ **Available Tools:**\n\n"
        
        # List all registered tools
        for tool_name, tool in self.agent.tools.tools.items():
            usage_count = self.agent.tool_usage_count.get(tool_name, 0)
            last_used_ts = self.agent.tool_last_used.get(tool_name)
            
            status = "🆕 New" if usage_count == 0 else f"✅ Learned/Used {usage_count} times"
            
            if last_used_ts:
                last_used_str = datetime.datetime.fromtimestamp(last_used_ts).strftime('%Y-%m-%d %H:%M')
                status += f" (Last: {last_used_str})"
            
            tool_text += f"• `{tool_name}` - {status}\n"
            tool_text += f"  _{tool.description}_\n\n"
        
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
        
        subcommand = args[0].lower()
        
        if subcommand in ["logs", "log"]:
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
            asyncio.create_task(self._cmd_logs_live(channel_id, duration))
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
â€˘ Host: `{hostname}` ({os_name})
â€˘ Uptime: {uptime_str}
â€˘ Started: <t:{int(self.agent.start_time)}:R>

💾 **Memory:**
â€˘ Total Memories: {total_memories}

🛠️ **Most Used Tools:**"""
        
        # Sort tools by usage
        sorted_tools = sorted(self.agent.tool_usage_count.items(), key=lambda x: x[1], reverse=True)
        for tool, count in sorted_tools[:3]:
            stats_text += f"\nâ€˘ {tool}: {count} times"
        
        if not sorted_tools:
            stats_text += "\nâ€˘ No tools used yet"
        
        await self.agent.discord.send_message(channel_id, stats_text)
    
    async def cmd_export(self, channel_id: int, args: list):
        """Export data and send to Discord chat."""
        import json
        
        export_type = args[0] if args else 'stats'
        
        if export_type not in ['history', 'memory', 'stats', 'all']:
            await self.agent.discord.send_message(channel_id, 
                "âťŚ Invalid export type. Use: `history`, `memory`, `stats`, or `all`")
            return
        
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
            if "NEED_SEARCH:" not in initial_response:
                logger.debug("cmd_ask: Sending direct answer")
                await self.agent.discord.send_message(channel_id, f"💬 **Answer:**\n{initial_response}")
                return
                
            # Step 3: Handle Web Search
            if "NEED_SEARCH:" in initial_response:
                search_query = initial_response.split("NEED_SEARCH:", 1)[1].strip()
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
        if not info:
             await self.agent.discord.send_message(channel_id, "🧠 Usage: `!teach <information>`")
             return

        # Store as a high-priority memory
        self.agent.memory.add_memory(
            content=f"User taught me: {info}",
            metadata={"type": "user_teaching", "importance": "high"}
        )
        
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
                        # This is a simplified check and might have false positives/negatives
                        # but should catch obvious missing vars like 'memories'
                        for child in ast.walk(node):
                            if isinstance(child, ast.Assign):
                                for target in child.targets:
                                    if isinstance(target, ast.Name):
                                        local_names.add(target.id)
                            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                                if (child.id not in local_names and 
                                    child.id not in global_names and 
                                    child.id != "self"):
                                    
                                    # Filter out common false positives
                                    if child.id in ['True', 'False', 'None', 'Exception']: continue
                                    
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
            test_areas = ['llm', 'network', 'database', 'filesystem', 'tools', 'memory', 'ngrok', 'discord', 'resources', 'boredom', 'code_integrity']
        elif area == 'quick':
            test_areas = ['llm', 'network', 'database', 'discord']
        elif area == 'deep':
            # DEEP DEBUG MODE
            test_areas = ['critical_files', 'tools_functional', 'network', 'ngrok', 'database', 'filesystem', 'code_integrity']
        elif area == 'tools':
            test_areas = ['tools_functional']
        elif area == 'filesystem':
            test_areas = ['filesystem', 'critical_files']
        else:
            test_areas = [area]
        
        # Execute tests
        for test_area in test_areas:
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
            elif test_area == 'code_integrity':
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
                       'errors', 'logs', 'config', 'code_integrity', 'code']
        
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
        elif area in ['code_integrity', 'code']:
            analyzing_msg = await self.agent.discord.send_message(
                channel_id, 
                "🔃 **Analyzing code integrity...**\n```\nRunning AST analysis...\n```"
            )
            
            try:
                # Run in thread to avoid blocking
                import asyncio
                results = await asyncio.wait_for(
                    asyncio.to_thread(self._test_code_integrity),
                    timeout=30.0
                )
                
                # Format result
                header = "🩺 **Code Integrity Check**\n"
                yaml = "```yaml\n"
                body = f"STATUS: {results['status']}\n"
                if results.get('issues'):
                    body += f"ISSUES: {len(results['issues'])}\n"
                    for issue in results['issues'][:10]:
                        body += f"  - {issue}\n"
                else:
                    body += "No issues found.\n"
                
                # Edit the analyzing message with results
                await self.agent.discord.edit_message(
                    channel_id,
                    analyzing_msg,
                    f"{header}{yaml}{body}```"
                )
                
            except asyncio.TimeoutError:
                await self.agent.discord.edit_message(
                    channel_id,
                    analyzing_msg,
                    "⚠️ **Code integrity check timed out** (>30s)"
                )
            except Exception as e:
                logger.error(f"Code integrity check failed: {e}", exc_info=True)
                await self.agent.discord.edit_message(
                    channel_id,
                    analyzing_msg,
                    f"✖️ **Check failed**: {str(e)}"
                )
            return
        
        await self.agent.discord.send_message(channel_id, f"🩺 Running system diagnostics ({area})...")
        
        try:
            maintenance_enabled = False
            if area in ['deep', 'tools', 'all']:  # Updated to include 'all'
                maintenance_enabled = True
                self.agent.maintenance_mode = True
                await self.agent.discord.send_message(channel_id, "⚠️ **Maintenance Mode Active**: Autonomous behaviors paused.")
            
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
                        async with session.get('http://localhost:4040/api/tunnels', timeout=2) as resp:
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
            'rss_tool': {'url': 'https://news.ycombinator.com/rss'}, # Needs a valid URL
            'web_tool': {'action': 'search', 'query': 'test'}, # Might fail if offline
            'file_tool': {'action': 'read', 'filename': 'requirements.txt'},
            'discord_activity_tool': {} # No args needed
        }
        
        for tool_name, tool in self.agent.tools.tools.items():
            if tool_name in test_cases:
                try:
                    # Execute with safe args
                    args = test_cases[tool_name]
                    # Timeout to prevent hanging
                    try:
                        result = await asyncio.wait_for(tool._execute_with_logging(**args), timeout=10.0)
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
    
    async def cmd_goals(self, channel_id: int, args: list):
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
        
        elif args[0] == 'add' and len(args) > 1:
            # Add new goal
            new_goal = ' '.join(args[1:])
            self.agent.goals.append(new_goal)
            await self.agent.discord.send_message(channel_id, 
                f"✅ Goal added: '{new_goal}'\n🎯 Total goals: {len(self.agent.goals)}")
        
        elif args[0] == 'clear':
            # Clear all goals
            count = len(self.agent.goals)
            self.agent.goals = []
            await self.agent.discord.send_message(channel_id, 
                f"🗑️ Cleared {count} goals.")
        
        elif args[0] == 'remove' and len(args) > 1:
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
        else:
            await self.agent.discord.send_message(channel_id, 
                "❓ Usage:\n• `!goals` - Show goals\n• `!goals add <goal>` - Add goal\n• `!goals remove <num>` - Remove goal\n• `!goals clear` - Clear all")
    
    async def cmd_config(self, channel_id: int, args: list):
        """Show/modify configuration."""
        await self.agent.discord.send_message(channel_id, "🚧 Config management is under construction.")
    
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

        if channel_id:
            await self.agent.discord.send_message(channel_id, "🔧 Starting ngrok SSH tunnel...")
        
        try:
            # Start ngrok in background
            self.ngrok_process = await asyncio.create_subprocess_shell(
                "ngrok tcp 22",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Register as protected process
            if self.ngrok_process and hasattr(self.agent, 'resource_manager'):
                self.agent.resource_manager.register_protected_process(
                    self.ngrok_process.pid,
                    "ngrok"
                )
                logger.info(f"Ngrok process registered as protected (PID: {self.ngrok_process.pid})")
            
            # Wait a bit for ngrok to start and establish connection
            await asyncio.sleep(3)
        except Exception as e:
            logger.exception("SSH tunnel setup failed")
            if channel_id:
                await self.agent.discord.send_message(channel_id, f"✖️ Failed to start ngrok: {e}")
            self.ngrok_process = None
            return

        # Query ngrok API for tunnel info
        await self._notify_ssh_info(channel_id)


    class SSHView(discord.ui.View):
        def __init__(self, command_handler, ssh_command, net_use_command):
            super().__init__(timeout=300)
            self.command_handler = command_handler
            self.ssh_command = ssh_command
            self.net_use_command = net_use_command

        @discord.ui.button(label="📋 Copy SSH", style=discord.ButtonStyle.primary)
        async def copy_ssh(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(f"```{self.ssh_command}```", ephemeral=True)

        @discord.ui.button(label="📋 Copy Net Use", style=discord.ButtonStyle.secondary)
        async def copy_net_use(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(f"```{self.net_use_command}```", ephemeral=True)

        @discord.ui.button(label="🛑 Stop Tunnel", style=discord.ButtonStyle.danger)
        async def stop_tunnel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in config_settings.ADMIN_USER_IDS:
                await interaction.response.send_message("⛔ Access Denied", ephemeral=True)
                return
            await interaction.response.defer()
            await self.command_handler.cmd_ssh(interaction.channel_id, interaction.user.id, ["stop"])

    async def _notify_ssh_info(self, channel_id: Optional[int] = None):
        """Queries ngrok API and sends SSH info."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://127.0.0.1:4040/api/tunnels', timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            # Get the first tunnel (should be our TCP tunnel)
                            public_url = tunnels[0].get('public_url', '')
                            
                            # Extract SSH command using regex
                            ssh_command = self._extract_ssh_command(public_url, username="davca")
                            
                            if ssh_command and ssh_command.startswith("ssh"):
                                # Parse host and port for net use command
                                # ssh davca@0.tcp.eu.ngrok.io -p 12345
                                parts = ssh_command.split()
                                host_part = parts[1] # davca@0.tcp.eu.ngrok.io
                                port_part = parts[3] # 12345
                                
                                host = host_part.split('@')[1]
                                
                                # Dynamic drive letter selection (Z -> A, excluding C)
                                # Uses cmd /c to allow "exit" to break the loop upon success
                                net_use_command = (
                                    f'cmd /c "for %i in (Z Y X W V U T S R Q P O N M L K J I H G F E D B A) '
                                    f'do @if not exist %i:\\ (net use %i: \\\\sshfs\\davca@{host}!{port_part} /user:davca && exit)"'
                                )
                                
                                view = self.SSHView(self, ssh_command, net_use_command)
                                msg = f"✅ **SSH Tunnel Established!**\n\nClick the buttons below to get connection commands (Admins only)."
                                
                                if channel_id:
                                    await self.agent.discord.send_message(channel_id, msg, view=view)
                                else:
                                    # Send to admin DM if no channel specified
                                    await self.agent.send_admin_dm(f"✅ **SSH Tunnel Established!**\n\n**SSH:**\n```bash\n{ssh_command}\n```\n\n**Net Use:**\n```batch\n{net_use_command}\n```", category="ssh")
                            else:
                                if channel_id:
                                    await self.agent.discord.send_message(channel_id, "⚠️ Tunnel started but failed to parse connection info.")
                        else:
                            if channel_id:
                                await self.agent.discord.send_message(channel_id, "⚠️ Tunnel started but API returned no tunnels. Wait a moment and try again.")
                    else:
                        if channel_id:
                            await self.agent.discord.send_message(channel_id, f"⚠️ Failed to query ngrok API: Status {resp.status}")
            except Exception as e:
                logger.error(f"Error querying ngrok API: {e}")
                if channel_id:
                    await self.agent.discord.send_message(channel_id, f"✖️ Error querying ngrok API: {e}")

    async def cmd_ssh(self, channel_id: int, author_id: int, args: list = None):
        
        # Parse subcommand
        subcommand = args[0].lower() if args else "start"
        
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
                self.ngrok_process.terminate()
                await asyncio.sleep(1)
                if self.ngrok_process.returncode is None:
                    self.ngrok_process.kill()
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
                    self.ngrok_process.terminate()
                    await asyncio.sleep(1)
                    if self.ngrok_process.returncode is None:
                        self.ngrok_process.kill()
                    self.ngrok_process = None
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

    async def cmd_cmd(self, channel_id: int, command: str, author_id: int):
        """Execute shell command (Restricted)."""
        
        logger.info(f"cmd_cmd called with command: {command}")
        if author_id not in config_settings.ADMIN_USER_IDS:
            await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** You are not authorized to use this command.")
            logger.warning(f"Unauthorized !cmd attempt by user ID {author_id}")
            return
            
        if not command:
            await self.agent.discord.send_message(channel_id, "💻 Usage: `!cmd <command>`")
            return
            
        logger.info("Sending executing message...")
        await self.agent.discord.send_message(channel_id, f"💻 Executing: `{command}`...")
        logger.info("Executing message sent.")
        
        try:
            # Run command asynchronously
            logger.info("Starting subprocess...")
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("Subprocess started, waiting for output...")
            
            stdout, stderr = await process.communicate()
            logger.info("Subprocess finished.")
            
            output = ""
            if stdout:
                output += stdout.decode('utf-8', errors='replace')
            if stderr:
                output += stderr.decode('utf-8', errors='replace')
                
            if not output:
                output = "(No output)"
                
            # Check length
            if len(output) > 1900:
                # Save to temp file
                filename = f"cmd_output_{int(time.time())}.txt"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(output)
                    
                    await self.agent.discord.send_message(channel_id, 
                        f"📄 Output too large, sending as file:", 
                        file_path=filename)
                except Exception as e:
                    await self.agent.discord.send_message(channel_id, f"✖️ Error creating output file: {e}")
                finally:
                    # Clean up
                    try:
                        if os.path.exists(filename):
                            os.remove(filename)
                    except:
                        pass
            else:
                await self.agent.discord.send_message(channel_id, f"```text\n{output}\n```")
                
        except Exception as e:
            logger.exception("Cmd execution failed")
            await self.agent.discord.send_message(channel_id, f"✖️ Execution failed: {e}")
    
    async def _cmd_debug_errors(self, channel_id: int):
        """Debug subcommand: Show runtime error tracking."""
        try:
            summary = self.agent.error_tracker.get_summary(hours=24)
            recommendations = self.agent.error_tracker.get_recommendations()
            
            header = "⚠️ **Runtime Errors (Last 24h)**\n"
            yaml_start = "```yaml\n"
            yaml_end = "```"
            
            body = f"TOTAL: {summary['total']} errors\n\n"
            
            if summary['by_type']:
                body += "BY TYPE:\n"
                for error_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
                    body += f"  {error_type}: {count} occurrence(s)\n"
                body += "\n"
            
            if summary['recent_errors']:
                body += "RECENT (Last 10):\n"
                for i, err in enumerate(summary['recent_errors'][-10:], 1):
                    import datetime
                    ts = datetime.datetime.fromtimestamp(err['timestamp']).strftime('%H:%M')
                    body += f"  {i}. [{ts}] {err['error_type']} in {err['file']}:{err['line']}\n"
                    body += f"     {err['function']}: {err['message'][:60]}\n"
                body += "\n"
            
            if recommendations:
                body += "RECOMMENDATIONS:\n"
                for rec in recommendations[:5]:
                    body += f"  - {rec}\n"
            
            await self.agent.discord.send_message(channel_id, f"{header}{yaml_start}{body}{yaml_end}")
            
        except Exception as e:
            logger.error(f"_cmd_debug_errors failed: {e}", exc_info=True)
            await self.agent.discord.send_message(channel_id, f"✖️ Error tracking failed: {e}")
    
    async def _cmd_debug_logs(self, channel_id: int, count: int = 15, filter_level: str = None):
        """Debug subcommand: Show raw logs with optional filtering."""
        try:
            log_path = "agent.log"
            if not os.path.exists(log_path):
                await self.agent.discord.send_message(channel_id, "✖️ Log file not found")
                return
            
            # Read last N lines
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Get last lines
            last_lines = lines[-count * 3:] if count < len(lines) else lines
            
            # Filter if needed
            if filter_level:
                last_lines = [line for line in last_lines if filter_level in line]
            
            # Take only requested count
            last_lines = last_lines[-count:]
            
            if not last_lines:
                await self.agent.discord.send_message(channel_id, f"✖️ No logs found{' with filter: ' + filter_level if filter_level else ''}")
                return
            
            # Format output
            filter_text = f" (filter: {filter_level})" if filter_level else ""
            header = f"📋 **Logs (Last {len(last_lines)} lines{filter_text})**\n"
            code_start = "```\n"
            code_end = "```"
            
            log_text = "".join(last_lines)
            
            # Truncate if too long
            if len(log_text) > 1800:
                log_text = "...\n" + log_text[-1800:]
            
            await self.agent.discord.send_message(channel_id, f"{header}{code_start}{log_text}{code_end}")
            
        except Exception as e:
            logger.error(f"_cmd_debug_logs failed: {e}", exc_info=True)
            await self.agent.discord.send_message(channel_id, f"✖️ Log reading failed: {e}")
    
    async def _cmd_debug_config(self, channel_id: int):
        """Debug subcommand: Show current configuration."""
        try:
            import config_settings
            
            header = "⚙️ **Current Configuration**\n"
            yaml_start = "```yaml\n"
            yaml_end = "```"
            
            body = "ENVIRONMENT:\n"
            body += f"  Debug Mode: {getattr(config_settings, 'DEBUG_MODE', 'N/A')}\n"
            body += f"  Log Level: {getattr(config_settings, 'LOG_LEVEL', 'N/A')}\n\n"
            
            body += "LLM:\n"
            body += f"  Provider: {getattr(self.agent.llm, 'provider_type', 'Unknown')}\n"
            body += f"  Model: {getattr(self.agent.llm, 'model_filename', 'Unknown')}\n"
            body += f"  Temperature: {getattr(config_settings, 'TEMPERATURE', 'N/A')}\n"
            body += f"  Max Tokens: {getattr(config_settings, 'MAX_TOKENS', 'N/A')}\n\n"
            
            body += "AGENT:\n"
            body += f"  Boredom Threshold Low: {self.agent.BOREDOM_THRESHOLD_LOW}\n"
            body += f"  Boredom Threshold High: {self.agent.BOREDOM_THRESHOLD_HIGH}\n"
            body += f"  Boredom Decay: {self.agent.BOREDOM_DECAY_RATE}\n"
            body += f"  Boredom Interval: {self.agent.BOREDOM_INTERVAL}s\n\n"
            
            body += "DISCORD:\n"
            body += f"  Token: ***Hidden***\n"
            body += f"  Admin IDs: {config_settings.ADMIN_USER_IDS}\n\n"
            
            body += "PATHS:\n"
            body += f"  Database: {getattr(self.agent.memory, 'db_path', 'N/A')}\n"
            body += f"  Logs: agent.log\n"
            body += f"  State: agent_state.json\n"
            
            await self.agent.discord.send_message(channel_id, f"{header}{yaml_start}{body}{yaml_end}")
            
        except Exception as e:
            logger.error(f"_cmd_debug_config failed: {e}", exc_info=True)
    
    async def cmd_topic(self, channel_id: int, args: list, author_id: int):
        """Manages boredom topics stored in JSON file.
        
        Usage:
            !topic - List all topics
            !topic add <text> - Add new topic (admin only)
            !topic remove <index> - Remove topic (admin only)
            !topic clear - Clear all topics (admin only)
        """
        import config_settings
        
        # Load topics from JSON
        def load_topics():
            try:
                if os.path.exists(config_settings.TOPICS_FILE):
                    with open(config_settings.TOPICS_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    return []
            except Exception as e:
                logger.error(f"Failed to load topics: {e}")
                return []
        
        # Save topics to JSON
        def save_topics(topics):
            try:
                with open(config_settings.TOPICS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(topics, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                logger.error(f"Failed to save topics: {e}")
                return False
        
        # No args - show all topics
        if not args:
            topics = load_topics()
            if not topics:
                await self.agent.discord.send_message(channel_id, "📋 **Boredom Topics:** (empty)")
                return
            
            topics_list = "\n".join([f"{i+1}. {topic}" for i, topic in enumerate(topics)])
            await self.agent.discord.send_message(
                channel_id,
                f"📋 **Boredom Topics ({len(topics)}):**\n```\n{topics_list}\n```"
            )
            return
        
        # Subcommands require admin
        subcommand = args[0].lower()
        
        # Add topic
        if subcommand == "add":
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can add topics.")
                return
            
            if len(args) < 2:
                await self.agent.discord.send_message(channel_id, "✖️ Usage: `!topic add <text>`")
                return
            
            new_topic = ' '.join(args[1:])
            topics = load_topics()
            topics.append(new_topic)
            
            if save_topics(topics):
                await self.agent.discord.send_message(
                    channel_id,
                    f"✅ **Topic added!**\nTotal topics: {len(topics)}\n\n*New topic:* {new_topic}"
                )
            else:
                await self.agent.discord.send_message(channel_id, "✖️ Failed to save topics to file.")
            return
        
        # Remove topic
        elif subcommand == "remove":
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can remove topics.")
                return
            
            if len(args) < 2 or not args[1].isdigit():
                await self.agent.discord.send_message(channel_id, "✖️ Usage: `!topic remove <index>`")
                return
            
            index = int(args[1]) - 1  # Convert to 0-based
            topics = load_topics()
            
            if index < 0 or index >= len(topics):
                await self.agent.discord.send_message(channel_id, f"✖️ Invalid index. Must be between 1 and {len(topics)}")
                return
            
            removed_topic = topics.pop(index)
            
            if save_topics(topics):
                await self.agent.discord.send_message(
                    channel_id,
                    f"✅ **Topic removed!**\nRemaining topics: {len(topics)}\n\n*Removed:* {removed_topic}"
                )
            else:
                await self.agent.discord.send_message(channel_id, "✖️ Failed to save topics to file.")
            return
        
        # Clear all topics
        elif subcommand == "clear":
            if author_id not in config_settings.ADMIN_USER_IDS:
                await self.agent.discord.send_message(channel_id, "⛔ **Access Denied.** Only admins can clear topics.")
                return
            
            topics = load_topics()
            count = len(topics)
            
            if save_topics([]):
                await self.agent.discord.send_message(
                    channel_id,
                    f"✅ **All topics cleared!**\nRemoved {count} topics."
                )
            else:
                await self.agent.discord.send_message(channel_id, "✖️ Failed to clear topics.")
            return
        
        else:
            await self.agent.discord.send_message(
                channel_id,
                "✖️ Unknown subcommand. Use: `!topic`, `!topic add <text>`, `!topic remove <index>`, or `!topic clear`"
            )
    

    async def cmd_documentation(self, channel_id: int):
        """Shows project documentation with interactive buttons."""
        overview_path = "documentation/OVERVIEW.md"
        try:
            if not discord:
                await self.agent.discord.send_message(channel_id, "❌ Discord module not available.")
                return

            # Define View classes locally
            
            class CommandsView(discord.ui.View):
                def __init__(self, parent_view):
                    super().__init__(timeout=300)
                    self.parent_view = parent_view

                async def _send_file(self, interaction, path):
                    try:
                        if os.path.exists(path):
                            await interaction.response.send_message(file=discord.File(path), ephemeral=True)
                        else:
                            await interaction.response.send_message(f"❌ Soubor {path} nebyl nalezen.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Chyba při odesílání: {e}", ephemeral=True)

                @discord.ui.button(label="📋 Basic", style=discord.ButtonStyle.secondary)
                async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/commands/basic.md")

                @discord.ui.button(label="🎓 Tools & Learning", style=discord.ButtonStyle.secondary)
                async def tools(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/commands/tools-learning.md")

                @discord.ui.button(label="💾 Data", style=discord.ButtonStyle.secondary)
                async def data(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/commands/data-management.md")

                @discord.ui.button(label="💬 Interaction", style=discord.ButtonStyle.secondary)
                async def interaction_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/commands/interaction.md")

                @discord.ui.button(label="⚙️ Admin", style=discord.ButtonStyle.danger)
                async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/commands/admin.md")

            class CoreView(discord.ui.View):
                def __init__(self, parent_view):
                    super().__init__(timeout=300)
                    self.parent_view = parent_view

                async def _send_file(self, interaction, path):
                    try:
                        if os.path.exists(path):
                            await interaction.response.send_message(file=discord.File(path), ephemeral=True)
                        else:
                            await interaction.response.send_message(f"❌ Soubor {path} nebyl nalezen.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Chyba při odesílání: {e}", ephemeral=True)

                @discord.ui.button(label="🤖 Autonomous", style=discord.ButtonStyle.secondary)
                async def autonomous(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/core/autonomous-behavior.md")

                @discord.ui.button(label="🧠 Memory", style=discord.ButtonStyle.secondary)
                async def memory(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/core/memory-system.md")

                @discord.ui.button(label="🗣️ LLM", style=discord.ButtonStyle.secondary)
                async def llm(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/core/llm-integration.md")

                @discord.ui.button(label="💻 Resources", style=discord.ButtonStyle.secondary)
                async def resources(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/core/resource-manager.md")
                
                @discord.ui.button(label="🔌 Discord", style=discord.ButtonStyle.secondary)
                async def discord_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/core/discord-client.md")

            class AdvancedView(discord.ui.View):
                def __init__(self, parent_view):
                    super().__init__(timeout=300)
                    self.parent_view = parent_view

                async def _send_file(self, interaction, path):
                    try:
                        if os.path.exists(path):
                            await interaction.response.send_message(file=discord.File(path), ephemeral=True)
                        else:
                            await interaction.response.send_message(f"❌ Soubor {path} nebyl nalezen.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Chyba při odesílání: {e}", ephemeral=True)

                @discord.ui.button(label="🔍 Fuzzy Matching", style=discord.ButtonStyle.secondary)
                async def fuzzy_matching(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/advanced/fuzzy-matching-algorithm.md")

            class ScriptsView(discord.ui.View):
                def __init__(self, parent_view):
                    super().__init__(timeout=300)
                    self.parent_view = parent_view

                async def _send_file(self, interaction, path):
                    try:
                        if os.path.exists(path):
                            await interaction.response.send_message(file=discord.File(path), ephemeral=True)
                        else:
                            await interaction.response.send_message(f"❌ Soubor {path} nebyl nalezen.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Chyba při odesílání: {e}", ephemeral=True)

                @discord.ui.button(label="🚀 Deployment", style=discord.ButtonStyle.secondary)
                async def deployment(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/scripts/deployment-guide.md")

                @discord.ui.button(label="📜 Batch Scripts", style=discord.ButtonStyle.secondary)
                async def batch_scripts(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_file(interaction, "documentation/scripts/batch-scripts-reference.md")

            class DocumentationView(discord.ui.View):
                def __init__(self, command_handler):
                    super().__init__(timeout=300)
                    self.command_handler = command_handler

                async def _send_doc(self, interaction, path, title):
                    try:
                        if os.path.exists(path):
                           await interaction.response.send_message(file=discord.File(path), ephemeral=True)
                        else:
                            await interaction.response.send_message(f"❌ Soubor {path} nebyl nalezen.", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)

                @discord.ui.button(label="📖 Overview", style=discord.ButtonStyle.primary)
                async def overview(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_doc(interaction, "documentation/OVERVIEW.md", "Overview")

                @discord.ui.button(label="💬 Commands", style=discord.ButtonStyle.secondary)
                async def commands(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_message("Vyber kategorii příkazů:", view=CommandsView(self), ephemeral=True)

                @discord.ui.button(label="🛠️ Tools", style=discord.ButtonStyle.secondary)
                async def tools(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_doc(interaction, "documentation/tools/all-tools.md", "Tools")

                @discord.ui.button(label="🧠 Core", style=discord.ButtonStyle.secondary)
                async def core(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_message("Vyber sekci Core:", view=CoreView(self), ephemeral=True)

                @discord.ui.button(label="📜 Scripts", style=discord.ButtonStyle.secondary)
                async def scripts(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_message("Vyber Scripts dokumentaci:", view=ScriptsView(self), ephemeral=True)

                @discord.ui.button(label="🎓 Advanced", style=discord.ButtonStyle.secondary)
                async def advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.send_message("Vyber Advanced téma:", view=AdvancedView(self), ephemeral=True)

                @discord.ui.button(label="🆘 Troubleshooting", style=discord.ButtonStyle.danger)
                async def troubleshooting(self, interaction: discord.Interaction, button: discord.ui.Button):
                    await self._send_doc(interaction, "documentation/troubleshooting.md", "Troubleshooting")

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
            
        except Exception as e:
            logger.error(f"Failed to show documentation: {e}")
            await self.agent.discord.send_message(channel_id, f"❌ Chyba: {e}")

    async def cmd_report(self, channel_id: int, author_id: int):
        """Saves the last agent output and the user command that triggered it to reports.json."""
        if not self.last_user_command:
            await self.agent.discord.send_message(channel_id, "⚠️ No previous command found to report.")
            return

        last_agent_history = getattr(self.agent.discord, 'last_message_history', [])
        last_agent_output = getattr(self.agent.discord, 'last_sent_message', None)
        current_command_messages = getattr(self.agent.discord, 'current_command_messages', [])
        
        if not current_command_messages and not last_agent_output:
            await self.agent.discord.send_message(channel_id, "⚠️ No previous agent output found to report.")
            return

        report_entry = {
            "timestamp": time.time(),
            "user": self.last_user_command['user'],
            "user_id": self.last_user_command['user_id'],
            "user_command": self.last_user_command['command'],
            "agent_output": last_agent_output, # Legacy field
            "agent_outputs": current_command_messages, # Full list of messages with edits
            "reported_by": author_id
        }

        try:
            reports_file = "reports.json"
            reports = []
            if os.path.exists(reports_file):
                with open(reports_file, 'r', encoding='utf-8') as f:
                    try:
                        reports = json.load(f)
                    except json.JSONDecodeError:
                        pass # Start fresh if corrupted

            reports.append(report_entry)

            with open(reports_file, 'w', encoding='utf-8') as f:
                json.dump(reports, f, indent=4, ensure_ascii=False)

            await self.agent.discord.send_message(channel_id, "✅ **Report Saved!**\nThe last interaction has been logged to `reports.json`.")
            logger.info(f"Report saved by user {author_id}")

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            await self.agent.discord.send_message(channel_id, f"❌ Failed to save report: {e}")
