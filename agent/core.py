import asyncio
import logging
import time
from typing import Optional
import sys
import platform
import os
import json
import discord
import psutil

logger = logging.getLogger(__name__)

class AutonomousAgent:
    def __init__(self, discord_token: str = None):
        self.os_type = sys.platform
        self.is_linux = self.os_type.startswith('linux')
        logger.info(f"Initializing Agent on {platform.system()} ({platform.release()})")
        
        # Load persistent state
        state = self._load_agent_state()
        self.boredom_score = state.get("boredom_score", 0.0)
        
        # Load admin DMs state with backward compatibility
        self.admin_dms = state.get("admin_dms", {})
        
        # Migration: If old format exists and new format is empty/missing default
        if "last_admin_dm_id" in state and "default" not in self.admin_dms:
            self.admin_dms["default"] = {
                "id": state.get("last_admin_dm_id"),
                "channel_id": state.get("last_admin_dm_channel_id"),
                "timestamp": state.get("last_admin_dm_timestamp")
            }
            logger.info("Migrated legacy admin DM state to 'default' category")
        
        self.last_activity_time = time.time()
        self.is_running = False
        self.actions_without_tools = 0  # Counter to force tool usage
        self.action_history = []  # Track last actions (non-boredom)
        self.tool_usage_count = self._load_tool_stats()  # Track tool usage (persistent)
        self.tool_last_used = self._load_tool_timestamps() # Track last usage time
        self.successful_learnings = 0  # Track successful learnings
        self.start_time = time.time()  # Track uptime
        self.learning_queue = []  # Queue for forced learning
        self.is_learning_mode = False # Flag for learning mode
        self.is_processing = False # Flag for active LLM processing
        self.maintenance_mode = False # Flag for maintenance/debug mode
        self.goals = [  # AI goals
            "Learn new things using tools",
            "Try to maintain boredom below 70%",
            "Use diverse tools",
            "Build knowledge base"
        ]
        
        # Debug tracking
        self.messages_processed = 0
        self.dm_count = 0
        self.channel_count = 0
        self.mention_count = 0
        self.last_message_time = None
        self.last_message_content = None
        self.last_tool_used = None
        self.last_tool_time = None
        self.last_decision_prompt = None
        self.last_decision_response = None
        self.decision_history = []  # Last 5 decisions
        
        # Thresholds
        self.BOREDOM_THRESHOLD_LOW = 0.2
        self.BOREDOM_THRESHOLD_HIGH = 0.4
        self.BOREDOM_DECAY_RATE = 0.01  # Slower decay (1% per interval)
        
        # Import config and load boredom interval
        import config_settings
        self.BOREDOM_INTERVAL = getattr(config_settings, 'BOREDOM_INTERVAL', 60)  # Default 60s if not in config
        
        # Subsystems
        from .memory import VectorStore
        from .llm import LLMClient
        from .discord_client import DiscordClient
        from .hardware import HardwareMonitor, LedIndicator
        from .resource_manager import ResourceManager, NetworkMonitor
        from .tools import (ToolRegistry, FileTool, SystemTool, WebTool,
                            TimeTool, MathTool, WeatherTool, CodeTool, 
                            NoteTool, DatabaseTool, RSSTool, 
                            TranslateTool, WikipediaTool, DiscordActivityTool)
        from .error_tracker import get_error_tracker
        from .web_interface import WebServer
        
        
        self.memory = VectorStore()
        self.llm = LLMClient()
        self.discord = DiscordClient(token=discord_token)
        self.hardware = HardwareMonitor()
        self.led = LedIndicator()
        self.resource_manager = ResourceManager(self)  # Add resource manager
        self.network_monitor = NetworkMonitor(self)  # Add network monitor
        self.error_tracker = get_error_tracker()  # Add error tracker
        self.web_server = WebServer(self) # Add web interface
        
        # Tools
        self.tools = ToolRegistry()
        self.tools.register(FileTool())
        self.tools.register(SystemTool())
        self.tools.register(WebTool())
        self.tools.register(TimeTool())
        self.tools.register(MathTool())
        self.tools.register(WeatherTool())
        self.tools.register(CodeTool())
        self.tools.register(NoteTool())
        # git_tool removed - dependency issues and not needed
        self.tools.register(DatabaseTool())
        self.tools.register(DiscordActivityTool(self))
        self.tools.register(RSSTool())
        self.tools.register(TranslateTool())
        self.tools.register(WikipediaTool())
        
        
        # Command handler
        from .commands import CommandHandler
        self.command_handler = CommandHandler(self)
    
    async def graceful_shutdown(self, timeout: int = 10) -> bool:
        """Gracefully shutdown agent, closing all resources safely."""
        logger.info("🔄 Starting graceful shutdown...")
        
        # Create incomplete shutdown flag
        try:
            with open(".shutdown_incomplete", "w") as f:
                f.write(str(time.time()))
        except Exception as e:
            logger.error(f"Failed to create shutdown flag: {e}")
        
        # 0. Stop web server
        try:
            if hasattr(self, 'web_server'):
                logger.info("Stopping web server...")
                self.web_server.stop()
        except Exception as e:
            logger.error(f"Failed to stop web server: {e}")
        
        shutdown_start = time.time()
        
        try:
            # 1. Stop autonomous loops
            logger.info("Stopping autonomous behaviors...")
            self.is_running = False
            await asyncio.sleep(0.5)
            
            # 2. Save agent state
            logger.info("Saving agent state...")
            try:
                self._save_agent_state()
            except Exception as e:
                logger.error(f"Failed to save agent state: {e}")
            
            # 3. Save tool stats
            logger.info("Saving tool statistics...")
            try:
                self._save_tool_stats()
                self._save_tool_timestamps()
            except Exception as e:
                logger.error(f"Failed to save tool stats: {e}")
            
            # 4. Commit and close database
            logger.info("Closing database...")
            try:
                if hasattr(self.memory, 'conn') and self.memory.conn:
                    self.memory.conn.commit()
                    self.memory.conn.close()
                    logger.info("Database closed successfully")
            except Exception as e:
                logger.error(f"Failed to close database: {e}")
            
            # 4.5 Ensure all file handles are closed (topics JSON etc.)
            logger.info("Ensuring all file handles are flushed...")
            try:
                import sys
                import gc
                # Force garbage collection to close any lingering file handles
                gc.collect()
                # Flush all open files
                for handler in logging.root.handlers:
                    if hasattr(handler, 'flush'):
                        handler.flush()
                    if hasattr(handler, 'stream'):
                        try:
                            handler.stream.flush()
                        except:
                            pass
                logger.info("File handles flushed")
            except Exception as e:
                logger.error(f"Error during file handle cleanup: {e}")
            
            # 5. Flush logs
            logger.info("Flushing logs...")
            try:
                for handler in logging.root.handlers:
                    handler.flush()
            except Exception as e:
                logger.error(f"Failed to flush logs: {e}")
            
            # 6. Close Discord client
            logger.info("Closing Discord connection...")
            try:
                if self.discord and hasattr(self.discord, 'client'):
                    if self.discord.client and not self.discord.client.is_closed():
                        await asyncio.wait_for(self.discord.client.close(), timeout=3.0)
                        logger.info("Discord client closed")
            except asyncio.TimeoutError:
                logger.warning("Discord client close timed out")
            except Exception as e:
                logger.error(f"Failed to close Discord client: {e}")
            
            # Check timeout
            elapsed = time.time() - shutdown_start
            if elapsed > timeout:
                logger.warning(f"Shutdown exceeded timeout ({elapsed:.1f}s > {timeout}s)")
                return False
            
            # Remove incomplete shutdown flag
            try:
                if os.path.exists(".shutdown_incomplete"):
                    os.remove(".shutdown_incomplete")
                    logger.info("✅ Graceful shutdown completed successfully")
            except Exception as e:
                logger.error(f"Failed to remove shutdown flag: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            return False

    async def start(self):
        """Starts the agent's main loops."""
        self.is_running = True
        logger.info("Agent starting...")
        
        # Check for incomplete shutdown
        if os.path.exists(".shutdown_incomplete"):
            logger.warning("Detected incomplete shutdown flag!")
            try:
                with open(".shutdown_incomplete", "r") as f:
                    timestamp = float(f.read().strip())
                import datetime
                shutdown_time = datetime.datetime.fromtimestamp(timestamp)
                incomplete_duration = time.time() - timestamp
                
                logger.warning(f"Last shutdown was incomplete at {shutdown_time} ({incomplete_duration:.0f}s ago)")
                
                # Remove the flag
                os.remove(".shutdown_incomplete")
                logger.info("Incomplete shutdown flag removed")
                
                # Will notify admin after Discord is ready
                self._incomplete_shutdown_detected = True
                self._incomplete_shutdown_time = shutdown_time
                
            except Exception as e:
                logger.error(f"Error processing incomplete shutdown flag: {e}")
        else:
            self._incomplete_shutdown_detected = False
        
        # Cleanup old test files
        self._cleanup_old_tests()
        
        # Start discord
        await self.discord.start()
        
        # Start web server
        try:
            self.web_server.start()
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
        
        # Start command handler worker
        self.command_handler.start()
        
        # Initial status
        hostname = platform.node()
        await self.discord.update_activity(f"Init on {hostname}...")
        
        # Start SSH tunnel automatically (independent of Discord)
        asyncio.create_task(self.command_handler.start_ssh_tunnel())
        
        # Wait for Discord to be ready (max 30s)
        logger.info("Waiting for Discord connection...")
        wait_start = time.time()
        while not self.discord.is_ready:
            if time.time() - wait_start > 30:
                logger.warning("Discord connection timed out (30s). Proceeding offline...")
                break
            await asyncio.sleep(0.5)
        
        # Check for restart flag and notify
        import json
        logger.info(f"Checking for restart flag at {os.path.abspath('.restart_flag')}")
        if os.path.exists(".restart_flag"):
            logger.info("Restart flag FOUND!")
            try:
                with open(".restart_flag", "r") as f:
                    restart_info = json.load(f)
                logger.info(f"Restart info loaded: {restart_info}")
                
                channel_id = restart_info.get("channel_id")
                author = restart_info.get("author", "unknown")
                
                if channel_id:
                    logger.info(f"Sending restart notification to {channel_id}")
                    await self.discord.send_message(channel_id, f"✅ **Agent restarted successfully!**\nAs requested by {author}\nRunning post-restart diagnostics...")
                    
                    # Run quick diagnostics
                    try:
                        logger.info("Running post-restart diagnostics...")
                        results = await self.command_handler._run_diagnostics('quick')
                        logger.info("Diagnostics complete.")
                        
                        # Check for failures
                        failures = []
                        for system, data in results.items():
                            for key, value in data.items():
                                if "❌" in str(value) or "Error" in str(value) or "Failed" in str(value):
                                    failures.append(f"{system}: {key} ({value})")
                        
                        if not failures:
                            await self.discord.send_message(channel_id, "🚀 **Restart completed. All systems OK.**")
                        else:
                            failure_msg = "\n".join([f"- {f}" for f in failures])
                            await self.discord.send_message(channel_id, f"⚠️ **Restart completed, but some systems reported errors:**\n{failure_msg}")
                            
                    except Exception as e:
                        logger.error(f"Post-restart diagnostics failed: {e}")
                        await self.discord.send_message(channel_id, f"⚠️ **Restart completed, but diagnostics failed:** {e}")
                
                # Remove flag file
                logger.info("Removing restart flag file")
                os.remove(".restart_flag")
            except Exception as e:
                logger.error(f"Error processing restart flag: {e}")
        else:
            logger.info("Restart flag NOT found.")
        
        # SSH tunnel already started above
        
        try:
            await asyncio.gather(
                self.boredom_loop(),
                self.observation_loop(),
                self.action_loop(),
                self.backup_loop()
            )
        except Exception as e:
            logger.critical(f"Agent crashed: {e}")
            await self.report_error(e)
            raise

    def _cleanup_old_tests(self):
        """Delete files in tests/ directory older than 2 days."""
        try:
            tests_dir = os.path.abspath("tests")
            if not os.path.exists(tests_dir):
                return

            logger.info("Cleaning up old test files...")
            now = time.time()
            cutoff = now - (2 * 24 * 3600) # 2 days ago
            
            count = 0
            for filename in os.listdir(tests_dir):
                file_path = os.path.join(tests_dir, filename)
                # Skip directories
                if not os.path.isfile(file_path):
                    continue
                    
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime < cutoff:
                        os.remove(file_path)
                        logger.info(f"Deleted old test file: {filename}")
                        count += 1
                except Exception as e:
                    logger.error(f"Error deleting {filename}: {e}")
            
            if count > 0:
                logger.info(f"Cleanup complete. Deleted {count} old test files.")
            else:
                logger.info("Cleanup complete. No old test files found.")
        except Exception as e:
            logger.error(f"Error during test cleanup: {e}")
            
            count = 0
            for filename in os.listdir(tests_dir):
                file_path = os.path.join(tests_dir, filename)
                # Skip directories
                if not os.path.isfile(file_path):
                    continue
                    
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime < cutoff:
                        os.remove(file_path)
                        logger.info(f"Deleted old test file: {filename}")
                        count += 1
                except Exception as e:
                    logger.error(f"Error deleting {filename}: {e}")
            
            if count > 0:
                logger.info(f"Cleanup complete. Deleted {count} old test files.")
            else:
                logger.info("Cleanup complete. No old test files found.")
        except Exception as e:
            logger.error(f"Error during test cleanup: {e}")

    async def report_error(self, error: Exception):
        """Reports a critical error to the admin via Discord."""
        logger.error(f"Critical error reported: {error}")
        
        try:
            # Read last 100 lines of log
            log_path = "agent.log"
            log_content = ""
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    log_content = "".join(lines[-100:])
            
            error_msg = f"🚨 **CRITICAL ERROR** 🚨\n\nException: `{str(error)}`\n\n**Last 100 log lines:**"
            
            # Send to admin
            import config_settings
            if config_settings.ADMIN_USER_IDS and self.discord.client:
                user = await self.discord.client.fetch_user(config_settings.ADMIN_USER_IDS[0])
                
                if len(log_content) > 1800:
                    # Create temp file
                    import tempfile
                    filename = f"crash_log_{int(time.time())}.txt"
                    temp_path = os.path.join(tempfile.gettempdir(), filename)
                    
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(f"Exception: {error}\n\nLog:\n{log_content}")
                    
                    await user.send(f"🚨 **CRITICAL ERROR** 🚨\nException: `{str(error)}`\nSee attached log.", file=discord.File(temp_path))
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                else:
                    await self.send_admin_dm(f"{error_msg}\n```\n{log_content}\n```", category="error")

        except Exception as e:
            logger.critical(f"Failed to report error: {e}")


    async def boredom_loop(self):
        """Simulates the passage of time and intrinsic decay (boredom)."""
        logger.debug("Boredom loop started.")
        while self.is_running:
            if self.maintenance_mode:
                await asyncio.sleep(1)
                continue
                
            await asyncio.sleep(self.BOREDOM_INTERVAL)
            
            # Update status periodically
            await self.discord.update_activity(f"Boredom: {self.boredom_score*100:.0f}%")
            
            # Check hardware health
            if not self.hardware.is_safe_to_run():
                logger.warning("System unsafe. Pausing boredom loop.")
                await asyncio.sleep(30) # Cool down
                continue

            # Increase boredom
            self.boredom_score = min(1.0, self.boredom_score + self.BOREDOM_DECAY_RATE)
            self._save_agent_state()
            logger.debug(f"Boredom score: {self.boredom_score:.2f} | {self.hardware.get_status()}")
            
            if self.boredom_score > self.BOREDOM_THRESHOLD_HIGH:
                logger.debug("Boredom threshold exceeded. Triggering autonomous action.")
                
                self.led.set_state("BUSY")
                try:
                    await self.trigger_autonomous_action()
                except Exception as e:
                    logger.error(f"Autonomous action failed: {e}")
                    self.led.set_state("ERROR")
                    await asyncio.sleep(2)
                finally:
                    if not self.is_learning_mode:
                        self.led.set_state("IDLE")


    async def check_subsystems(self):
        """Checks health of subsystems and restarts if needed (Self-Healing)."""
        import config_settings
        
        # 1. Web Server Self-Healing
        if getattr(config_settings, 'WEB_SERVER_AUTO_RESTART', False):
            # Check if server should be running but isn't
            if hasattr(self, 'web_server'):
                is_running = self.web_server.thread and self.web_server.thread.is_alive()
                manual_stop = getattr(self.web_server, 'manual_stop', False)
                
                if not is_running and not manual_stop:
                    # Server is down and not stopped manually
                    current_time = time.time()
                    
                    # Initialize down timestamp if not set
                    if not hasattr(self, '_web_server_down_since'):
                        self._web_server_down_since = current_time
                        logger.warning("Web server is down! Starting restart timer...")
                    
                    # Check if down for > 10 seconds
                    elif current_time - self._web_server_down_since > 10:
                        logger.warning("Web server down for >10s. Attempting auto-restart...")
                        try:
                            self.web_server.start()
                            self._web_server_down_since = None # Reset
                            logger.info("Web server auto-restarted successfully.")
                            await self.discord.send_admin_dm("🔄 **Web Server Auto-Restarted**\nService was down for >10s.", category="system")
                        except Exception as e:
                            logger.error(f"Web server auto-restart failed: {e}")
                            # Reset timer to try again in 10s (prevent rapid loop)
                            self._web_server_down_since = current_time 
                
                elif is_running:
                    # Server is running, reset down timer
                    if hasattr(self, '_web_server_down_since') and self._web_server_down_since:
                        self._web_server_down_since = None

        # 2. SSH Tunnel Self-Healing
        # Check if tunnel is supposed to be running (we assume yes if agent is running)
        if self.command_handler.ngrok_process is None:
             # Check if it was manually stopped? 
             # For SSH, we usually want it always on unless explicitly stopped.
             # But command_handler doesn't have a manual_stop flag yet.
             # We'll assume if it's None, it might have been stopped manually or crashed.
             # However, the user specifically mentioned "kill -9" which kills the process but the object might still exist?
             pass
        
        # Better check: Verify the actual process if we have a PID
        # But pyngrok manages the process.
        # If the process was killed via kill -9, pyngrok might not know immediately.
        # We can check if the tunnel is still listed in ngrok.get_tunnels()
        
        try:
            from pyngrok import ngrok
            tunnels = ngrok.get_tunnels()
            ssh_tunnel_active = False
            for t in tunnels:
                if t.proto == "tcp" and (":22" in t.config['addr'] or t.config['addr'].endswith(":22")):
                    ssh_tunnel_active = True
                    break
            
            if not ssh_tunnel_active:
                # No SSH tunnel found!
                # Only restart if we haven't tried recently to avoid spam
                if not hasattr(self, '_last_ssh_restart_attempt') or time.time() - self._last_ssh_restart_attempt > 30:
                    logger.warning("SSH Tunnel not found! Attempting auto-restart...")
                    self._last_ssh_restart_attempt = time.time()
                    # Force restart
                    self.command_handler.ngrok_process = None 
                    await self.command_handler.start_ssh_tunnel()
                    await self.discord.send_admin_dm("🔄 **SSH Tunnel Auto-Restarted**\nTunnel was missing.", category="system")
        except Exception as e:
            logger.error(f"Error checking SSH tunnel health: {e}")


    async def observation_loop(self):
        """Polls sensors and queues inputs."""
        logger.debug("Observation loop started.")
        last_resource_check = 0
        last_subsystem_check = 0
        
        while self.is_running:
            # Check Discord Messages
            messages = await self.discord.get_messages()
            if messages:
                logger.debug(f"Processing {len(messages)} Discord messages.")
                self.reduce_boredom(0.1)
                
                for msg in messages:
                    # Track message stats
                    self.messages_processed += 1
                    self.last_message_time = time.time()
                    self.last_message_content = msg['content']
                    if msg.get('is_dm'):
                        self.dm_count += 1
                    else:
                        self.channel_count += 1
                    if msg.get('mentions_bot'):
                        self.mention_count += 1
                    
                    # Check for commands first - process immediately
                    if msg['content'].startswith('!'):
                        # Create task for immediate processing (bypasses queue)
                        asyncio.create_task(self.handle_command_immediate(msg))
                    # If directly addressed or DM, reply immediately
                    elif msg['is_dm'] or msg['mentions_bot']:
                        logger.info(f"Direct interaction from {msg['author']}. Replying...")
                        # Generate reply using LLM
                        response = await self.llm.generate_response(
                            prompt=f"User {msg['author']} says: {msg['content']}",
                            system_prompt="You are a helpful AI assistant. Answer in Czech language (čeština) unless asked otherwise. Be concise and accurate."
                        )
                        await self.discord.send_message(msg['channel_id'], response)
            
            # Resource monitoring (every 10 seconds)
            current_time = asyncio.get_event_loop().time()
            if current_time - last_resource_check >= 10:
                usage = self.resource_manager.check_resources()
                tier = self.resource_manager.get_tier(usage)
                
                # Check for tier change
                if tier != self.resource_manager.current_tier:
                    logger.info(f"Resource tier changed: {self.resource_manager.current_tier} -> {tier}")
                    self.resource_manager.current_tier = tier
                    await self.handle_resource_tier(tier, usage)
                
                last_resource_check = current_time
            
            # Subsystem Health Check (every 30 seconds)
            if current_time - last_subsystem_check >= 30:
                await self.check_subsystems()
                last_subsystem_check = current_time
            
            # Network monitoring (every 60 seconds)
            if current_time - self.network_monitor.last_check >= self.network_monitor.check_interval:
                is_online = await self.network_monitor.check_connectivity()
                
                # Handle state transitions
                if not is_online and self.network_monitor.is_online:
                    # Went offline
                    await self.network_monitor.handle_disconnect()
                    self.network_monitor.is_online = False
                elif is_online and not self.network_monitor.is_online:
                    # Came back online
                    await self.network_monitor.handle_reconnect()
                    self.network_monitor.is_online = True
                    
                    # Restart SSH tunnel if needed
                    asyncio.create_task(self.command_handler.start_ssh_tunnel())
                
                self.network_monitor.last_check = current_time
            
            await asyncio.sleep(1)

    async def _process_activity(self, activity_data: dict):
        """Research unknown user activities and store in memory."""
        activity_name = activity_data.get('name')
        user_id = activity_data.get('user_id')
        user_name = activity_data.get('user_name')
        
        if not activity_name:
            return

        # Check if we already know about this activity
        memories = self.memory.search_memory(f"What is {activity_name}?", limit=1)
        
        # If we have a high relevance memory, skip research but maybe update user association?
        # For now, just skip if we know the activity to avoid spamming research
        if memories and memories[0].get('metadata', {}).get('type') == 'activity_knowledge':
            # TODO: Maybe add logic to track which users play what?
            return

        logger.info(f"Detected new user activity: {activity_name} by {user_name}. Researching...")
        
        # Research using WebTool
        web_tool = self.tools.get_tool('web_tool')
        if web_tool:
            try:
                # Search for info
                query = f"What is {activity_name} video game?"
                search_result = await web_tool._execute_with_logging(action='search', query=query)
                
                # Track usage
                self.tool_usage_count['web_tool'] = self.tool_usage_count.get('web_tool', 0) + 1
                self._save_tool_stats()
                            
                # Store in memory
                content = f"Activity: {activity_name}\nInfo: {search_result[:500]}...\nPlayed by: {user_name} (ID: {user_id})"
                self.memory.add_memory(
                    content=content,
                    metadata={
                        "type": "activity_knowledge",
                        "activity": activity_name,
                        "first_seen_user_id": user_id,
                        "first_seen_user_name": user_name,
                        "timestamp": time.time()
                    }
                )
                logger.info(f"Learned about {activity_name} and saved to memory.")
                
            except Exception as e:
                logger.error(f"Failed to research activity {activity_name}: {e}")

    def _simplify_action(self, action: str) -> str:
        """Simplifies English action to concise form for Discord status."""
        # Remove common prefixes and filler words
        clean = action.replace("ACTION:", "").replace("Action:", "").strip()
        clean = clean.replace("TO stay engaged,", "").replace("To stay engaged,", "")
        clean = clean.replace("I will try to", "").replace("I'll try to", "")
        clean = clean.replace("I will", "").replace("I'll", "")
        clean = clean.replace("try to", "").strip()
        
        # Remove "some", "a few", etc.
        clean = clean.replace(" some ", " ").replace(" a few ", " ").replace(" several ", " ")
        
        # Clean up extra spaces
        while "  " in clean:
            clean = clean.replace("  ", " ")
        
        # Capitalize first letter
        if clean:
            clean = clean[0].upper() + clean[1:]
        
        return clean[:50]  # Limit length

    async def handle_resource_tier(self, tier: int, usage):
        """Handle resource tier changes with appropriate responses."""
        
        if tier == 0:
            # Normal - Basic Operation
            if hasattr(self.llm, 'update_parameters'):
                self.llm.update_parameters(tier)
                
        elif tier == 1:
            # Warning & Cleanup
            await self.resource_manager.execute_tier1()
            
        elif tier == 2:
            # Active Mitigation
            await self.resource_manager.execute_tier2()
            if hasattr(self.llm, 'update_parameters'):
                self.llm.update_parameters(tier)
                
        elif tier == 3:
            # Emergency
            await self.resource_manager.execute_tier3()
            if hasattr(self.llm, 'update_parameters'):
                self.llm.update_parameters(tier)
    
    async def backup_loop(self):
        """Periodically backs up the database (2x daily)."""
        logger.info("Backup loop started.")
        import glob
        
        while self.is_running:
            try:
                # Check time since last backup
                backup_dir = "backup"
                backups = sorted(glob.glob(os.path.join(backup_dir, "agent_memory_*.db")))
                
                should_backup = True
                if backups:
                    last_backup = backups[-1]
                    # Extract timestamp from filename: agent_memory_1234567890.db
                    try:
                        timestamp = int(last_backup.split("_")[-1].split(".")[0])
                        if time.time() - timestamp < 12 * 60 * 60:
                            should_backup = False
                            # Calculate sleep time
                            sleep_time = (12 * 60 * 60) - (time.time() - timestamp)
                            logger.info(f"Last backup was recent. Sleeping for {sleep_time/3600:.1f} hours.")
                            await asyncio.sleep(sleep_time)
                            continue
                    except ValueError:
                        logger.warning("Could not parse backup timestamp. Forcing backup.")
                
                if should_backup:
                    logger.info("Starting scheduled database backup...")
                    success = self.memory.create_backup()
                    if success:
                        logger.info("Scheduled database backup completed successfully")
                    else:
                        logger.error("Scheduled database backup failed")
            
            except Exception as e:
                logger.error(f"Error in backup loop: {e}")
            
            # Check again in 1 hour if we just backed up or failed
            await asyncio.sleep(60 * 60)
    
    async def action_loop(self):
        """Executes queued actions (placeholder)."""
        logger.info("Action loop started.")
        while self.is_running:
            if self.maintenance_mode:
                await asyncio.sleep(1)
                continue
                
            # Placeholder for action queue processing
            await asyncio.sleep(1)

    async def process_learning_queue(self):
        """Processes the entire learning queue in a batch."""
        if not self.learning_queue:
            return

        logger.info(f"Starting batch learning for {len(self.learning_queue)} tools...")
        self.led.set_state("BUSY")
        
        # Notify start
        await self.discord.update_activity(f"Learning {len(self.learning_queue)} tools...")
        
        while self.learning_queue:
            tool_name = self.learning_queue[0] # Peek first
            logger.info(f"LEARNING BATCH: Processing {tool_name}")
            
            try:
                # 1. Context for learning
                context = (f"I am in LEARNING MODE. My goal is to learn how to use the '{tool_name}' tool. "
                          f"I MUST use the '{tool_name}' tool now to test its functionality and learn what it does. "
                          f"I should try a simple, safe operation with it.")
                
                # 2. Retrieve relevant memories (RAG)
                past_memories = self.memory.get_recent_memories(limit=3)
                
                # 3. Decide action
                tool_desc = self.tools.get_descriptions()
                response = await self.llm.decide_action(context, past_memories, tool_desc)
                
                success = False
                if response:
                    # 4. Execute
                    tool_call = self.llm.parse_tool_call(response)
                    if tool_call:
                        target_tool_name = tool_call['tool']
                        args = tool_call['args']
                        
                        tool = self.tools.get_tool(target_tool_name)
                        if tool:
                            result = await tool._execute_with_logging(**args)
                            
                            # Track usage
                            self.tool_usage_count[target_tool_name] = self.tool_usage_count.get(target_tool_name, 0) + 1
                            self._save_tool_stats()
                            
                            # Store result
                            self.memory.add_memory(
                                content=f"Learning Session: Tool {target_tool_name} executed. Result: {result[:200]}...",
                                metadata={"type": "learning", "tool": target_tool_name, "importance": "high"}
                            )
                            
                            await self.report_learning(f"I successfully used the tool `{target_tool_name}` with arguments `{args}`.\nResult: {result[:200]}...")
                            self.successful_learnings += 1
                            self.tools.increment_usage(target_tool_name)
                            success = True
                
                if success:
                    # Remove from queue only on success? Or always?
                    # If we fail, we might want to skip it to avoid infinite loop.
                    if self.learning_queue and self.learning_queue[0] == tool_name:
                         self.learning_queue.pop(0)
                else:
                    logger.warning(f"Failed to learn {tool_name}, skipping...")
                    if self.learning_queue:
                        self.learning_queue.pop(0)
                
                # Wait a bit between tools
                await asyncio.sleep(5)
                
                # Dynamic cooldown if load is high
                while True:
                    cpu = psutil.cpu_percent(interval=1)
                    if cpu < 80.0:
                        break
                    logger.warning(f"Learning paused due to high load ({cpu}%), cooling down...")
                    await self.discord.update_activity(f"Cooling down ({cpu}%)...")
                    self.led.set_state("IDLE")
                    await asyncio.sleep(10)
                    self.led.set_state("BUSY")
                            
            except Exception as e:
                logger.error(f"Error learning {tool_name}: {e}")
                self.led.set_state("ERROR")
                await asyncio.sleep(1)
                self.led.set_state("BUSY")
                if self.learning_queue:
                    self.learning_queue.pop(0)
                
        self.is_learning_mode = False
        self.led.set_state("IDLE")
        logger.info("Batch learning complete.")
        await self.discord.update_activity("Learning complete.")


    async def trigger_autonomous_action(self):
        """The 'Free Will' mechanism."""
        
        # SAFETY FUSE: Check system load before running LLM
        # If CPU is too high (e.g. > 90%), skip LLM to prevent crash/OOM
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > 90.0:
                logger.warning(f"SAFETY FUSE: CPU load too high ({cpu_usage}%), skipping LLM autonomous action.")
                await self.discord.update_activity(f"Cooling down (CPU {cpu_usage:.0f}%)")
                # Perform lightweight fallback action
                await asyncio.sleep(5) 
                return
        except:
            pass

        # Prevent concurrent execution
        if self.is_processing:
            logger.debug("Skipping autonomous action: Agent is already processing.")
            return

        self.is_processing = True
        self.led.set_state("BUSY")
        logger.debug("Agent is bored. Deciding what to do...")
        await self.discord.update_activity("Thinking...")
        
        import random
        
        
        # Handle Learning Mode
        if self.is_learning_mode and self.learning_queue:
            await self.process_learning_queue()
            self.is_processing = False
            return
        
        # Force tool usage if too many actions without tools
        
        # Force tool usage if too many actions without tools
        elif self.actions_without_tools >= 2:
            logger.info("Forcing tool usage after repeated non-tool actions")
            context = f"Boredom: {self.boredom_score:.2f}. I MUST use the web_tool to search for something new and learn."
            self.actions_without_tools = 0
        else:
            # Load topics from JSON file
            import config_settings
            thoughts = []
            
            try:
                topics_file = config_settings.TOPICS_FILE
                if os.path.exists(topics_file):
                    with open(topics_file, 'r', encoding='utf-8') as f:
                        thoughts = json.load(f)
                    logger.debug(f"Loaded {len(thoughts)} topics from {topics_file}")
            except Exception as e:
                logger.error(f"Failed to load topics from JSON: {e}")
            
            # Fallback to default topics if JSON is empty or failed to load
            if not thoughts:
                thoughts = [
                    "I wonder what the latest AI news is.",
                    "I should search for Raspberry Pi projects.",
                    "I want to learn something new about Python programming.",
                    "Are there any interesting tech news today?",
                    "I should research machine learning topics.",
                    "I wonder what my friends are doing on Discord."
                ]
                logger.debug("Using default topics (JSON empty or missing)")
            
            context = f"Boredom: {self.boredom_score:.2f}. {random.choice(thoughts)}"
        
        # Special handling for "checking friends" thought
        if "friends are doing" in context:
            logger.info("Boredom trigger: Checking user activities...")
            await self.discord.update_activity("Watching friends...")
            if self.discord.is_ready:
                activities = await self.discord.get_online_activities()
                if activities:
                    for activity in activities:
                        await self._process_activity(activity)
                    self.reduce_boredom(0.5)
                    self.is_processing = False
                    return # Skip LLM action if we did this
                else:
                    logger.info("No active users found.")
                    # Fall through to normal LLM action if no one is doing anything
        
        # 1. Retrieve relevant memories (RAG)
        past_memories = self.memory.get_recent_memories(limit=3)
        if past_memories:
            logger.debug(f"Retrieved {len(past_memories)} past memories for context.")

        # 2. Decide action with Tools
        tool_desc = self.tools.get_descriptions()
        response = await self.llm.decide_action(context, past_memories, tool_desc)
        
        # Check for LLM failure
        if response is None:
            logger.warning("LLM returned None (likely context overflow). Skipping action.")
            self.is_processing = False
            return

        if response == "LLM not available.":
            logger.warning("LLM not available during autonomous action.")
            await self.send_admin_dm("⚠️ **Alert:** LLM is unavailable during autonomous loop.", category="error")
            # Fallback action to keep loop alive but not spam
            response = "TOOL: web_tool | ARGS: action='search', query='latest raspberry pi news'"

        
        # Track decision
        self.last_decision_prompt = context
        self.last_decision_response = response
        self.decision_history.append({
            'prompt': context[:100],
            'response': response[:100],
            'time': time.time()
        })
        if len(self.decision_history) > 5:
            self.decision_history.pop(0)
        
        # Check for tool call
        tool_call = self.llm.parse_tool_call(response)
        
        if tool_call:
            tool_name = tool_call['tool']
            args = tool_call['args']
            logger.info(f"Agent wants to use tool: {tool_name} with args {args}")
            
            tool = self.tools.get_tool(tool_name)
            if tool:
                # Map tool to descriptive English activity
                activity_map = {
                    "file_tool": "Managing files",
                    "system_tool": "Checking system",
                    "web_tool": "Surfing the web",
                    "time_tool": "Checking time",
                    "math_tool": "Learning with numbers",
                    "weather_tool": "Watching weather",
                    "code_tool": "Learning to code",
                    "note_tool": "Taking notes",
                    "git_tool": "Managing version control",
                    "database_tool": "Organizing data",
                    "rss_tool": "Reading news feeds",
                    "translate_tool": "Translating languages",
                    "wikipedia_tool": "Learning from Wikipedia"
                }
                activity_desc = activity_map.get(tool_name, f"Using tool: {tool_name}")
                await self.discord.update_activity(activity_desc)
                
                result = await tool._execute_with_logging(**args)
                
                # Track usage
                self.tool_usage_count[tool_name] = self.tool_usage_count.get(tool_name, 0) + 1
                self._save_tool_stats()
                
                self.actions_without_tools = 0  # Reset counter
                self.last_tool_used = tool_name
                self.last_tool_time = time.time()
                logger.info(f"Tool output: {result}")
                
                # Store result in memory
                self.memory.add_memory(
                    content=f"Tool {tool_name} executed. Result: {result[:100]}...",
                    metadata={"type": "tool_execution", "tool": tool_name}
                )
                
                # Report learning
                await self.report_learning(f"I successfully used the tool `{tool_name}` with arguments `{args}`.\nResult: {result[:200]}...")
                
                # Track usage in registry
                self.tools.increment_usage(tool_name)
                
                # Track timestamp
                self.tool_last_used[tool_name] = time.time()
                self._save_tool_timestamps()
                
                # Track timestamp
                self.tool_last_used[tool_name] = time.time()
                self._save_tool_timestamps()
                
                self.successful_learnings += 1
                
                # Add to action history
                self._add_to_history(f"Used tool: {tool_name}")

                # Reduce boredom significantly for successful tool use

                # Reduce boredom significantly for successful tool use
                self.reduce_boredom(0.8)
            else:
                logger.error(f"Tool {tool_name} not found.")
        else:
            # Normal action execution
            simplified = self._simplify_action(response)
            await self.discord.update_activity(simplified)
            await self.execute_action(response)
            self.actions_without_tools += 1  # Increment counter
            
            # Add to action history
            self._add_to_history(simplified)
            
            # Store memory (excluding boredom score to keep memories clean)
            clean_context = context.split(". ", 1)[1] if ". " in context else context
            self.memory.add_memory(
                content=f"Context: {clean_context} -> Action: {response}",
                metadata={"type": "autonomous_decision"}
            )
            
            # Calculate difficulty/satisfaction based on action type
            reduction = 0.2 
            if any(word in response.lower() for word in ["analyze", "report", "scan", "investigate"]):
                reduction = 0.5
            if any(word in response.lower() for word in ["mitigate", "block", "attack", "emergency"]):
                reduction = 0.8
                
            self.reduce_boredom(reduction)
        
        self.is_processing = False

    async def report_learning(self, message: str):
        """Reports new skills/learnings to the specific Discord channel."""
        LEARNING_CHANNEL_ID = 1442261590404497580
        try:
            # Save to memory
            self.memory.add_memory(
                content=f"Learned: {message}",
                metadata={"type": "learning", "importance": "high"}
            )
            
            await self.discord.send_message(LEARNING_CHANNEL_ID, f"🧠 **New Skill/Knowledge Acquired:**\n{message}")
            logger.info(f"Reported learning to channel {LEARNING_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Failed to report learning: {e}")

    async def execute_action(self, action: str):
        """Executes a decided action."""
        logger.info(f"Executing action: {action}")
        
        # Mock logic to send to discord if action implies communication
        if "status" in action.lower() or "report" in action.lower():
             # Use smart DM for autonomous reports
            await self.send_admin_dm(f"🤖 **Autonomous Report:**\n{action}", category="report")

    def reduce_boredom(self, amount: float):
        """Reduces boredom score based on action difficulty."""
        old_score = self.boredom_score
        self.boredom_score = max(0.0, self.boredom_score - amount)
        self.last_activity_time = time.time()
        logger.debug(f"Boredom reduced by {amount:.2f} (from {old_score:.2f} to {self.boredom_score:.2f}).")
        self._save_agent_state()

    def reset_boredom(self):
        """Resets boredom score completely (e.g. external stimulus)."""
        self.boredom_score = 0.0
        self.last_activity_time = time.time()
        logger.debug("Boredom reset to 0.")
        self._save_agent_state()
    
    def _simplify_action(self, action: str) -> str:
        """Simplifies action string for status display."""
        # Simple truncation for now
        return action[:50] + "..." if len(action) > 50 else action

    
    async def handle_command_immediate(self, msg: dict):
        """Handles commands immediately without queuing (for instant ! command processing)."""
        try:
            logger.info(f"Immediate command processing: {msg['content'][:50]}")
            await self.command_handler._execute_command(msg)
        except Exception as e:
            logger.error(f"Error in immediate command processing: {e}", exc_info=True)
            try:
                await self.discord.send_message(msg['channel_id'], f"❌ Command error: {e}")
            except:
                pass
    
    async def handle_command(self, msg: dict):
        """Handle Discord commands."""
        await self.command_handler.handle_command(msg)

    def _add_to_history(self, action: str):
        """Add action to history and keep it trimmed."""
        self.action_history.append({
            'action': action,
            'timestamp': time.time()
        })
        # Keep last 100 actions
        if len(self.action_history) > 100:
            self.action_history.pop(0)

    def get_debug_info(self, area=None):
        """Get debug information for specified area or all areas."""
        import time
        
        debug_info = {}
        
        # 1. Boredom System
        if area is None or area == 'boredom':
            time_since_activity = time.time() - self.last_activity_time
            next_trigger = max(0, (self.BOREDOM_THRESHOLD_HIGH - self.boredom_score) / self.BOREDOM_DECAY_RATE * self.BOREDOM_INTERVAL)
            
            debug_info['boredom'] = {
                'score': f"{self.boredom_score * 100:.1f}%",
                'threshold_low': f"{self.BOREDOM_THRESHOLD_LOW * 100:.0f}%",
                'threshold_high': f"{self.BOREDOM_THRESHOLD_HIGH * 100:.0f}%",
                'decay_rate': f"{self.BOREDOM_DECAY_RATE * 100:.1f}% per {self.BOREDOM_INTERVAL}s",
                'time_since_activity': f"{time_since_activity:.0f}s",
                'actions_without_tools': self.actions_without_tools,
                'next_trigger_in': f"{next_trigger:.0f}s" if self.boredom_score < self.BOREDOM_THRESHOLD_HIGH else "NOW"
            }
        
        # 2. Tool Usage
        if area is None or area == 'tools':
            total_tools = len(self.tools.tools)
            usage_stats = self.tools.get_usage_stats()
            used_tools = len([t for t in usage_stats.values() if t > 0])
            unused_tools = total_tools - used_tools
            total_uses = sum(usage_stats.values())
            
            debug_info['tools'] = {
                'total_registered': total_tools,
                'used': used_tools,
                'unused': unused_tools,
                'total_uses': total_uses,
                'diversity_score': f"{(used_tools / total_tools * 100):.0f}%" if total_tools > 0 else "0%",
                'last_tool': self.last_tool_used or "None",
                'last_tool_time': f"{time.time() - self.last_tool_time:.0f}s ago" if self.last_tool_time else "Never",
                'learning_mode': "Active" if self.is_learning_mode else "Inactive",
                'learning_queue': len(self.learning_queue)
            }
        
        # 3. Discord Message Handling
        if area is None or area == 'discord':
            debug_info['discord'] = {
                'messages_processed': self.messages_processed,
                'dm_count': self.dm_count,
                'channel_count': self.channel_count,
                'mention_count': self.mention_count,
                'last_message': self.last_message_content[:50] + "..." if self.last_message_content and len(self.last_message_content) > 50 else self.last_message_content or "None",
                'last_message_time': f"{time.time() - self.last_message_time:.0f}s ago" if self.last_message_time else "Never",
                'queue_size': self.discord.message_queue.qsize() if hasattr(self.discord, 'message_queue') else 0
            }
        
        # 4. Resource Management
        if area is None or area == 'resources':
            usage = self.resource_manager.check_resources()
            tier = self.resource_manager.get_tier(usage)
            
            resources_info = {
                'current_tier': f"Tier {tier}",
                'cpu_usage': f"{usage.cpu_percent:.1f}%",
                'memory_usage': f"{usage.ram_percent:.1f}%",
                'disk_usage': f"{usage.disk_percent:.1f}%",
                'llm_context': getattr(self.llm, 'current_n_ctx', 'Unknown'),
                'llm_max_tokens': getattr(self.llm, 'current_max_tokens', 'Unknown')
            }
            
            # Add RPI-specific health checks if on Linux
            if self.is_linux:
                rpi_health = self._check_rpi_health()
                if rpi_health:
                    resources_info.update(rpi_health)
            
            debug_info['resources'] = resources_info
        
        # 5. Network Monitoring
        if area is None or area == 'network':
            debug_info['network'] = {
                'status': "Online" if self.network_monitor.is_online else "Offline",
                'last_check': f"{time.time() - self.network_monitor.last_check:.0f}s ago" if hasattr(self.network_monitor, 'last_check') else "Never",
                'check_interval': f"{self.network_monitor.check_interval}s",
                'tools_disabled': self.network_monitor.tools_disabled,
                'uptime': f"{time.time() - self.start_time:.0f}s"
            }
        
        # 6. LLM Decision Making
        if area is None or area == 'llm':
            debug_info['llm'] = {
                'last_prompt': self.last_decision_prompt[:100] + "..." if self.last_decision_prompt and len(self.last_decision_prompt) > 100 else self.last_decision_prompt or "None",
                'last_response': self.last_decision_response[:100] + "..." if self.last_decision_response and len(self.last_decision_response) > 100 else self.last_decision_response or "None",
                'decision_history_size': len(self.decision_history),
                'model_path': getattr(self.llm, 'model_filename', 'Unknown') if hasattr(self, 'llm') else 'Not loaded'
            }
        
        return debug_info
    
    def _check_rpi_health(self) -> dict:
        """Check Raspberry Pi hardware health using vcgencmd (Linux only)."""
        if not self.is_linux:
            return {}
        
        health_info = {}
        
        try:
            import subprocess
            
            # 1. Throttling status
            try:
                result = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    throttled = result.stdout.strip()
                    # Parse throttled value (hex)
                    if 'throttled=' in throttled:
                        value = int(throttled.split('=')[1], 16)
                        # Bit 0: under-voltage
                        # Bit 1: arm frequency capped
                        # Bit 2: currently throttled
                        # Bit 16: under-voltage has occurred
                        # Bit 17: arm frequency capping has occurred
                        # Bit 18: throttling has occurred
                        
                        status_parts = []
                        if value & 0x1:
                            status_parts.append("⚠️ UNDERVOLTAGE")
                        if value & 0x2:
                            status_parts.append("⚠️ FREQ_CAPPED")
                        if value & 0x4:
                            status_parts.append("⚠️ THROTTLED")
                        if value & 0x10000:
                            status_parts.append("(UV occurred)")
                        if value & 0x20000:
                            status_parts.append("(FC occurred)")
                        if value & 0x40000:
                            status_parts.append("(Throttle occurred)")
                        
                        health_info['rpi_throttle'] = ' '.join(status_parts) if status_parts else "✅ OK"
            except:
                pass
            
            # 2. Temperature
            try:
                result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    temp = result.stdout.strip()
                    if 'temp=' in temp:
                        temp_val = temp.split('=')[1].replace("'C", "").strip()
                        health_info['rpi_temp'] = f"{temp_val}°C"
            except:
                pass
            
            # 3. Voltage
            try:
                result = subprocess.run(['vcgencmd', 'measure_volts'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    volts = result.stdout.strip()
                    if 'volt=' in volts:
                        health_info['rpi_voltage'] = volts.split('=')[1].strip()
            except:
                pass
            
            # 4. ARM Clock Speed
            try:
                result = subprocess.run(['vcgencmd', 'measure_clock', 'arm'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    clock = result.stdout.strip()
                    if 'frequency(' in clock:
                        freq_hz = int(clock.split('=')[1])
                        freq_mhz = freq_hz / 1000000
                        health_info['rpi_clock'] = f"{freq_mhz:.0f} MHz"
            except:
                pass
                
        except Exception as e:
            logger.debug(f"RPI health check failed: {e}")
        
        return health_info

    def _load_agent_state(self) -> dict:
        """Load agent state (boredom, last admin DM) from file."""
        state_file = "workspace/agent_state.json"
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load agent state: {e}")
        return {}

    def _save_agent_state(self):
        """Save agent state to file."""
        state_file = "workspace/agent_state.json"
        try:
            os.makedirs("workspace", exist_ok=True)
            state = {
                "boredom_score": self.boredom_score,
                "admin_dms": self.admin_dms
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")

    async def send_admin_dm(self, message: str, category: str = "default"):
        """
        Send DM to admin user. Edits last message in the same category if < 30m old.
        Categories: 'default', 'ssh', 'tier', 'error', 'report'
        """
        try:
            import config_settings
            if not config_settings.ADMIN_USER_IDS:
                logger.warning("No admin IDs configured")
                return
            
            admin_id = config_settings.ADMIN_USER_IDS[0]
            
            if self.discord.client and self.discord.is_ready:
                user = await self.discord.client.fetch_user(admin_id)
                
                # Get state for this category
                cat_state = self.admin_dms.get(category, {})
                last_id = cat_state.get("id")
                last_ts = cat_state.get("timestamp")
                
                # Smart DM Logic: Check if we can edit the last message
                current_time = time.time()
                edited = False
                
                if (last_id and last_ts and (current_time - last_ts) < 1800): # 30 minute window
                    logger.debug(f"Attempting to edit last Admin DM (Diff: {current_time - last_ts:.1f}s)")
                    
                    try:
                        # We need the DM channel to fetch the message
                        dm_channel = user.dm_channel
                        if not dm_channel:
                            dm_channel = await user.create_dm()
                        
                        last_msg = await dm_channel.fetch_message(last_id)
                        
                        # Append timestamp to show it was updated
                        update_str = f"\n\n*(Updated: <t:{int(current_time)}:R>)*"
                        new_content = message + update_str
                        
                        await last_msg.edit(content=new_content)
                        logger.info(f"Admin DM edited (Category: {category}, ID: {last_id})")
                        
                        # Update timestamp only, keep ID
                        if category not in self.admin_dms:
                            self.admin_dms[category] = {}
                        self.admin_dms[category]["timestamp"] = current_time
                        self.admin_dms[category]["id"] = last_id # Ensure ID is set
                        self._save_agent_state()
                        edited = True
                        
                    except (discord.NotFound, discord.Forbidden):
                        logger.warning(f"Could not edit last Admin DM (ID: {last_id}). Sending new one.")
                        edited = False # Fallback to new message
                    except Exception as e:
                        logger.error(f"Error editing Admin DM: {e}")
                        edited = False
                else:
                    if last_ts:
                        logger.debug(f"Last Admin DM too old to edit (Diff: {current_time - last_ts:.1f}s > 1800s)")
                
                if not edited:
                    # Send new message
                    msg_obj = await user.send(message)
                    logger.info(f"Admin DM sent ({category}): {message[:50]}...")
                    
                    # Update state
                    self.admin_dms[category] = {
                        "id": msg_obj.id,
                        "channel_id": msg_obj.channel.id,
                        "timestamp": current_time
                    }
                    self._save_agent_state()
                    
            else:
                logger.warning(f"Discord not ready, admin message: {message[:100]}...")
        except Exception as e:
            logger.error(f"Failed to send admin DM: {e}")

    def _load_tool_stats(self) -> dict:
        """Load tool usage stats from file."""
        import json
        import os
        stats_file = "workspace/tool_stats.json"
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load tool stats: {e}")
        return {}

    def _save_tool_stats(self):
        """Save tool usage stats to file."""
        import json
        import os
        stats_file = "workspace/tool_stats.json"
        try:
            os.makedirs("workspace", exist_ok=True)
            with open(stats_file, 'w') as f:
                json.dump(self.tool_usage_count, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tool stats: {e}")

    def _load_tool_timestamps(self) -> dict:
        """Load tool timestamp stats from file."""
        import json
        import os
        stats_file = "workspace/tool_timestamps.json"
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load tool timestamps: {e}")
        return {}

    def _save_tool_timestamps(self):
        """Save tool timestamp stats to file."""
        import json
        import os
        stats_file = "workspace/tool_timestamps.json"
        try:
            os.makedirs("workspace", exist_ok=True)
            with open(stats_file, 'w') as f:
                json.dump(self.tool_last_used, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tool timestamps: {e}")
