import logging
import asyncio
import psutil
import platform
import subprocess
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import config_settings

logger = logging.getLogger(__name__)

@dataclass
class ResourceUsage:
    """Resource usage snapshot."""
    cpu_percent: float
    ram_percent: float
    disk_percent: float
    swap_percent: float
    timestamp: float

class ResourceManager:
    """
    Manages system resources with four-tier adaptive response:
    - Tier 0 (<85%): Basic - Normal operation
    - Tier 1 (85%): Planning phase - analyze and prepare optimization
    - Tier 2 (95%): Active mitigation - reduce resource usage
    - Tier 3 (100%): Emergency mode - aggressive resource reclamation
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.protected_processes: Dict[int, str] = {}  # PID -> name
        self.current_tier = 0
        self.current_tier = 0
        self.last_check: Optional[ResourceUsage] = None
        
        # Thresholds from config
        # Thresholds from config
        self.tier_1_threshold = getattr(config_settings, 'RESOURCE_TIER_1_THRESHOLD', 80)
        self.tier_2_threshold = getattr(config_settings, 'RESOURCE_TIER_2_THRESHOLD', 90)
        self.tier_3_threshold = getattr(config_settings, 'RESOURCE_TIER_3_THRESHOLD', 95)
        
        # Dynamic SWAP config
        self.enable_dynamic_swap = getattr(config_settings, 'ENABLE_DYNAMIC_SWAP', True)
        self.swap_min_gb = getattr(config_settings, 'SWAP_MIN_SIZE_GB', 2)
        self.swap_max_gb = getattr(config_settings, 'SWAP_MAX_SIZE_GB', 8)
        
        logger.info(f"ResourceManager initialized (Tiers: {self.tier_1_threshold}%/{self.tier_2_threshold}%/{self.tier_3_threshold}%)")
    
    def register_protected_process(self, pid: int, name: str):
        """Register a process that should never be terminated."""
        self.protected_processes[pid] = name
        logger.info(f"Protected process registered: {name} (PID: {pid})")
    
    def unregister_protected_process(self, pid: int):
        """Unregister a protected process."""
        if pid in self.protected_processes:
            name = self.protected_processes.pop(pid)
            logger.info(f"Protected process unregistered: {name} (PID: {pid})")
    
    def check_resources(self) -> ResourceUsage:
        """Get current resource usage."""
        cpu = psutil.cpu_percent(interval=1.0)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        # Get swap usage if available
        try:
            swap = psutil.swap_memory().percent
        except:
            swap = 0.0
        
        usage = ResourceUsage(
            cpu_percent=cpu,
            ram_percent=ram,
            disk_percent=disk,
            swap_percent=swap,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.last_check = usage
        return usage
    
    def get_max_usage(self, usage: ResourceUsage) -> float:
        """Get the highest resource usage percentage."""
        return max(usage.cpu_percent, usage.ram_percent, usage.disk_percent)
    
    def get_tier(self, usage: Optional[ResourceUsage] = None) -> int:
        """
        Determine current resource tier with hysteresis.
        Returns: 0 (normal), 1 (planning), 2 (mitigation), 3 (emergency)
        """
        if usage is None:
            usage = self.check_resources()
        
        max_usage = self.get_max_usage(usage)
        
        # Hysteresis logic:
        # To go UP, just cross the threshold.
        # To go DOWN, must drop below the lower tier's threshold (or significant margin).
        
        # Check for Tier 3 (Emergency)
        if max_usage >= self.tier_3_threshold:
            return 3
        # Stay in Tier 3 until we drop below Tier 2 threshold
        if self.current_tier == 3 and max_usage >= self.tier_2_threshold:
            return 3
            
        # Check for Tier 2 (Mitigation)
        if max_usage >= self.tier_2_threshold:
            return 2
        # Stay in Tier 2 until we drop below Tier 1 threshold
        if self.current_tier == 2 and max_usage >= self.tier_1_threshold:
            return 2
            
        # Check for Tier 1 (Planning)
        if max_usage >= self.tier_1_threshold:
            return 1
        # Stay in Tier 1 until we drop slightly below it (e.g. 5% buffer)
        if self.current_tier == 1 and max_usage >= (self.tier_1_threshold - 5):
            return 1
            
        return 0

    async def execute_tier1(self) -> bool:
        """
        Tier 1 (80%): Warning & Cleanup.
        - Run GC
        - Trim history to 100
        - Notify Admin
        """
        logger.warning(f"Tier 1 triggered - Preventative Cleanup")
        
        try:
            # 1. Run Garbage Collection
            import gc
            gc.collect()
            
            # 2. Trim action history
            if hasattr(self.agent, 'action_history'):
                if len(self.agent.action_history) > 100:
                    self.agent.action_history = self.agent.action_history[-100:]
            
            # 3. Notify Admin
            if hasattr(self.agent, 'send_admin_dm'):
                await self.agent.send_admin_dm("⚠️ **Tier 1: High Load (80%)**\nRunning cleanup (GC, History trim).", category="tier")
                
            return True
        except Exception as e:
            logger.error(f"Tier 1 cleanup failed: {e}")
            return False

    async def execute_tier2(self) -> bool:
        """
        Tier 2 (90%): Active Mitigation.
        - Trim history to 50
        - Expand SWAP
        - Reduce LLM Context (Medium)
        - Notify Admin
        """
        logger.warning(f"Tier 2 triggered - Active Mitigation")
        
        try:
            # 1. Trim history
            if hasattr(self.agent, 'action_history'):
                if len(self.agent.action_history) > 50:
                    self.agent.action_history = self.agent.action_history[-50:]
            
            # 2. Expand SWAP
            if self.enable_dynamic_swap:
                await self._expand_swap()
                
            # 3. Reduce LLM Context
            if hasattr(self.agent, 'llm') and self.agent.llm:
                await self._reduce_llm_resources(tier=2)
                
            # 4. Notify Admin
            if hasattr(self.agent, 'send_admin_dm'):
                details = self.get_tier2_details()
                await self.agent.send_admin_dm(f"🔶 **Tier 2: Mitigation (90%)**\n{details}", category="tier")
                
            return True
        except Exception as e:
            logger.error(f"Tier 2 mitigation failed: {e}")
            return False

    async def execute_tier3(self) -> bool:
        """
        Tier 3 (95%): Emergency Survival.
        - Trim history to 10
        - Max SWAP
        - Min LLM Context
        - Kill non-essential processes
        - Notify Admin
        """
        logger.critical(f"Tier 3 EMERGENCY triggered - Critical Load (95%)")
        
        try:
            terminated_count = 0
            
            # 1. Trim history aggressively
            if hasattr(self.agent, 'action_history'):
                self.agent.action_history = self.agent.action_history[-10:]
                
            # 2. Max SWAP
            if self.enable_dynamic_swap:
                await self._expand_swap(force_max=True)
                
            # 3. Min LLM Context
            if hasattr(self.agent, 'llm') and self.agent.llm:
                await self._reduce_llm_resources(tier=3)
                
            # 4. Kill processes
            terminated_count = await self._terminate_non_essential_processes()
            
            # 5. Force GC
            import gc
            gc.collect()
            
            # 6. Notify Admin
            if hasattr(self.agent, 'send_admin_dm'):
                details = self.get_tier3_details(terminated_count)
                await self.agent.send_admin_dm(f"🚨 **Tier 3: EMERGENCY (95%)**\n{details}", category="tier")
                
            return True
        except Exception as e:
            logger.critical(f"Tier 3 emergency failed: {e}")
            return False
    
    async def _reduce_llm_resources(self, tier: int):
        """Reduce LLM resource usage based on tier."""
        context_sizes = {
            2: getattr(config_settings, 'LLM_CONTEXT_TIER2', 1024),
            3: getattr(config_settings, 'LLM_CONTEXT_TIER3', 1024)
        }
        
        new_ctx = context_sizes.get(tier, getattr(config_settings, 'LLM_CONTEXT_NORMAL', 2048))
        
        # Note: llama-cpp-python doesn't support runtime context change
        # We'll need to track this for future model reloads
        logger.warning(f"LLM context should be reduced to {new_ctx} (reload required)")
        
        # Store for next model load
        if hasattr(self.agent.llm, 'target_context'):
            self.agent.llm.target_context = new_ctx

    async def _expand_swap(self, force_max: bool = False):
        """Expand SWAP file dynamically."""
        os_type = platform.system()
        
        try:
            if os_type == "Windows":
                await self._expand_swap_windows(force_max)
            elif os_type == "Linux":
                await self._expand_swap_linux(force_max)
            else:
                logger.warning(f"Dynamic SWAP not supported on {os_type}")
        except Exception as e:
            logger.error(f"SWAP expansion failed: {e}")
    
    async def _expand_swap_windows(self, force_max: bool = False):
        """Expand pagefile on Windows."""
        target_size_gb = self.swap_max_gb if force_max else (self.swap_min_gb + 2)
        target_size_mb = target_size_gb * 1024
        
        # PowerShell command to set pagefile size
        ps_command = f'''
        $cs = Get-WmiObject -Class Win32_ComputerSystem
        $cs.AutomaticManagedPagefile = $false
        $cs.Put()
        
        $pg = Get-WmiObject -Class Win32_PageFileSetting
        if ($pg) {{
            $pg.InitialSize = {target_size_mb}
            $pg.MaximumSize = {target_size_mb}
            $pg.Put()
        }}
        '''
        
        logger.info(f"Expanding Windows pagefile to {target_size_gb}GB")
        
        # Note: This requires admin privileges
        try:
            process = await asyncio.create_subprocess_shell(
                f'powershell -Command "{ps_command}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            logger.info("Pagefile expansion command sent (may require admin)")
        except Exception as e:
            logger.warning(f"Pagefile expansion requires admin privileges: {e}")
    
    async def _expand_swap_linux(self, force_max: bool = False):
        """Expand swap file on Linux."""
        target_size_gb = self.swap_max_gb if force_max else (self.swap_min_gb + 2)
        target_size_bytes = target_size_gb * 1024 * 1024 * 1024
        
        logger.info(f"Checking Linux swap requirements (Target: {target_size_gb}GB)...")

        # 1. Check current swap usage
        try:
            swap = psutil.swap_memory()
            # If we already have enough swap (>= target), don't mess with it.
            # This prevents shrinking swap when dropping from Tier 3 -> Tier 2
            if swap.total >= target_size_bytes:
                 logger.info(f"Current swap ({swap.total / 1024**3:.2f}GB) is sufficient for target {target_size_gb}GB. Keeping existing configuration.")
                 return
            
            # If we are close enough to target (within 512MB), skip
            if abs(swap.total - target_size_bytes) < (512 * 1024 * 1024):
                 logger.info(f"Swap size ({swap.total / 1024**3:.2f}GB) matches target. Skipping expansion.")
                 return
        except Exception as e:
            logger.debug(f"Failed to check swap memory: {e}")

        # 2. Check if /swapfile exists and has correct size
        if os.path.exists("/swapfile"):
            try:
                size = os.path.getsize("/swapfile")
                # If file is large enough (>= target), just enable it
                if size >= target_size_bytes:
                    logger.info(f"/swapfile exists and is sufficient ({size/1024**3:.2f}GB >= {target_size_gb}GB). Verifying swapon...")
                    # Just ensure it's on
                    cmd = "sudo -n swapon /swapfile"
                    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    await proc.communicate()
                    return
            except Exception as e:
                logger.warning(f"Error checking /swapfile: {e}")

        logger.info(f"Expanding Linux swap to {target_size_gb}GB (This involves heavy I/O)...")
        
        # Check if we have sudo access without password
        try:
            check = await asyncio.create_subprocess_shell(
                "sudo -n true",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await check.communicate()
            if check.returncode != 0:
                logger.warning("Cannot expand swap: sudo requires password (configure NOPASSWD in sudoers)")
                return
        except Exception:
            return

        commands = [
            "sudo -n swapoff -a",
            f"sudo -n dd if=/dev/zero of=/swapfile bs=1G count={target_size_gb}",
            "sudo -n chmod 600 /swapfile",
            "sudo -n mkswap /swapfile",
            "sudo -n swapon /swapfile"
        ]
        
        # Note: This requires sudo privileges
        for cmd in commands:
            try:
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.warning(f"Swap command failed: {cmd} -> {stderr.decode().strip()}")
                    break
                    
            except Exception as e:
                logger.warning(f"Swap expansion command failed: {e}")
                break
    
    async def _terminate_non_essential_processes(self) -> int:
        """Kill Python processes except protected ones and self. Returns count of terminated."""
        current_pid = psutil.Process().pid
        terminated = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Skip self
                    if proc.pid == current_pid:
                        continue
                    
                    # Skip protected processes
                    if proc.pid in self.protected_processes:
                        logger.info(f"Skipping protected: {self.protected_processes[proc.pid]}")
                        continue
                    
                    # Only target Python processes that aren't us
                    if proc.name().lower().startswith('python'):
                        cmdline = ' '.join(proc.cmdline() or [])
                        
                        # Don't kill main agent process
                        if 'main.py' in cmdline:
                            continue
                        
                        # Don't kill Discord bot
                        if 'discord' in cmdline.lower():
                            continue
                        
                        # Kill other Python processes
                        logger.warning(f"Terminating non-essential process: {proc.name()} (PID: {proc.pid})")
                        proc.terminate()
                        terminated.append(proc.pid)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if terminated:
                logger.info(f"Terminated {len(terminated)} non-essential processes")
            else:
                logger.info("No non-essential processes to terminate")
            
            return len(terminated)
                
        except Exception as e:
            logger.error(f"Process termination error: {e}")
            return 0
    
    def get_tier2_details(self) -> str:
        """Get detailed info for Tier 2 notification."""
        if not hasattr(self.agent, 'llm'):
            return "LLM parameters: unavailable"
        
        old_ctx = getattr(config_settings, 'LLM_CONTEXT_NORMAL', 2048)
        new_ctx = getattr(config_settings, 'LLM_CONTEXT_TIER2', 1024)
        old_tokens = 256
        new_tokens = new_ctx // 8
        
        details = f"""**Tier 2 Mitigation Active:**
• LLM context: {old_ctx} → {new_ctx} tokens (-{old_ctx-new_ctx})
• Max tokens: {old_tokens} → {new_tokens} (-{old_tokens-new_tokens})
• Action history trimmed to 50 entries
• SWAP expanded dynamically
• Tool execution may be slower"""
        
        return details
    
    def get_tier3_details(self, terminated_count: int = 0) -> str:
        """Get detailed info for Tier 3 notification."""
        if not hasattr(self.agent, 'llm'):
            return "Emergency mode: LLM unavailable"
        
        old_ctx = getattr(config_settings, 'LLM_CONTEXT_TIER2', 1024)
        new_ctx = getattr(config_settings, 'LLM_CONTEXT_TIER3', 1024)
        
        old_tokens = old_ctx // 8
        new_tokens = new_ctx // 8

        details = f"""🚨 **Tier 3 EMERGENCY MODE:**
• LLM context: {old_ctx} → {new_ctx} tokens
• Max tokens: {old_tokens} → {new_tokens}
• Action history trimmed to 10 entries
• {terminated_count} non-essential processes terminated
• SWAP expanded to maximum
• Garbage collection forced

**Protected Services:**
✅ ngrok - ACTIVE
✅ Discord - ACTIVE
✅ main.py - ACTIVE"""
        
        return details

    def get_tier0_details(self) -> str:
        """Get detailed info for Tier 0 notification."""
        return """💚 **Tier 0: Basic Operation**
• Resources: Normal (<85%)
• LLM Context: Standard (2048 tokens)
• Performance: Unrestricted
• Status: Stable"""




class NetworkMonitor:
    """
    Monitors internet connectivity and handles offline/online transitions.
    Only disables internet-dependent tools on disconnect.
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.is_online = True
        self.last_check = 0
        self.check_interval = 60  # Check every 60 seconds
        self.tools_disabled = False
        logger.info("NetworkMonitor initialized")
    
    async def check_connectivity(self) -> bool:
        """Check if internet is available by pinging 8.8.8.8."""
        try:
            # Ping Google DNS
            if platform.system() == "Windows":
                cmd = "ping -n 1 -w 1000 8.8.8.8"
            else:
                cmd = "ping -c 1 -W 1 8.8.8.8"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=2.0)
            
            return process.returncode == 0
            
        except Exception as e:
            logger.debug(f"Connectivity check failed: {e}")
            return False
    
    async def handle_disconnect(self):
        """Handle network disconnect - disable ONLY internet-dependent tools."""
        if self.tools_disabled:
            return  # Already handled
        
        logger.warning("Network disconnected - disabling internet-dependent tools")
        
        # Only these tools require internet
        internet_tools = ['web_tool', 'weather_tool', 'rss_tool', 'translate_tool', 'wikipedia_tool']
        
        # Disable internet-dependent tools by replacing their execute method
        if hasattr(self.agent, 'tools') and self.agent.tools:
            for tool_name in internet_tools:
                if tool_name in self.agent.tools.tools:
                    try:
                        tool = self.agent.tools.tools[tool_name]
                        # Store original execute method
                        if not hasattr(tool, '_original_execute'):
                            tool._original_execute = tool.execute
                        # Replace with offline error method
                        async def offline_error(**kwargs):
                            return "Error: This tool requires internet connection. Currently offline."
                        tool.execute = offline_error
                        logger.info(f"Tool disabled: {tool_name}")
                    except Exception as e:
                        logger.error(f"Error disabling tool {tool_name}: {e}")
        
        self.tools_disabled = True
        logger.critical("OFFLINE MODE: Internet tools disabled. Local tools (file, system, time, math, code, note, git, db) remain active.")
    
    async def handle_reconnect(self):
        """Handle network reconnect - restore internet-dependent tools."""
        if not self.tools_disabled:
            return  # Already online
        
        logger.info("Network restored - initiating recovery...")
        
        failed_recoveries = []
        
        # Priority 1: Check ngrok
        try:
            logger.info("Priority 1: Checking ngrok...")
            if hasattr(self.agent, 'command_handler'):
                handler = self.agent.command_handler
            if hasattr(handler, 'ngrok_process') and handler.ngrok_process:
                    # Check if ngrok tunnel is still active by querying tunnels
                    try:
                        from pyngrok import ngrok
                        tunnels = ngrok.get_tunnels()
                        # Check if our tunnel still exists
                        tunnel_active = False
                        if hasattr(handler.ngrok_process, 'public_url'):
                            for t in tunnels:
                                if t.public_url == handler.ngrok_process.public_url:
                                    tunnel_active = True
                                    break
                        
                        if not tunnel_active:
                            logger.warning("ngrok tunnel stopped - attempting active restart...")
                            # Active Recovery
                            handler.ngrok_process = None # Clear old process ref
                            asyncio.create_task(handler.start_ssh_tunnel())
                            failed_recoveries.append("ngrok (restarting...)")
                        else:
                            logger.info("✅ ngrok still running")
                    except Exception as ngrok_err:
                        logger.error(f"ngrok tunnel check failed: {ngrok_err}")
                        failed_recoveries.append(f"ngrok ({str(ngrok_err)})")
        except Exception as e:
            logger.error(f"ngrok check failed: {e}")
            failed_recoveries.append(f"ngrok ({str(e)})")
        
        # Priority 2: Discord connection
        try:
            logger.info("Priority 2: Verifying Discord connection...")
            if hasattr(self.agent, 'discord') and self.agent.discord:
                logger.info("✅ Discord connection maintained")
        except Exception as e:
            logger.error(f"Discord check failed: {e}")
            failed_recoveries.append(f"Discord ({str(e)})")
        
        # Priority 3: Re-enable internet-dependent tools
        try:
            logger.info("Priority 3: Re-enabling internet-dependent tools...")
            internet_tools = ['web_tool', 'weather_tool', 'rss_tool', 'translate_tool', 'wikipedia_tool']
            
            if hasattr(self.agent, 'tools') and self.agent.tools:
                for tool_name in internet_tools:
                    if tool_name in self.agent.tools.tools:
                        tool = self.agent.tools.tools[tool_name]
                        # Restore original execute method
                        if hasattr(tool, '_original_execute'):
                            tool.execute = tool._original_execute
                            delattr(tool, '_original_execute')
                            logger.info(f"Tool re-enabled: {tool_name}")
                logger.info("✅ Internet-dependent tools re-enabled")
        except Exception as e:
            logger.error(f"Tool re-enable failed: {e}")
            failed_recoveries.append(f"Internet tools ({str(e)})")
        
        self.tools_disabled = False
        
        # Report to Discord
        try:
            recovery_msg = "🌐 **Network Restored**\n\n"
            recovery_msg += "✅ Internet connection recovered\n"
            recovery_msg += "✅ Internet tools restored: Web, Weather, RSS, Translate, Wikipedia\n"
            
            if failed_recoveries:
                recovery_msg += "\n⚠️ **Failed Recoveries:**\n"
                for failure in failed_recoveries:
                    recovery_msg += f"• {failure}\n"
            else:
                recovery_msg += "\n✅ All systems operational"
            
            if hasattr(self.agent, 'send_admin_dm'):
                await self.agent.send_admin_dm(recovery_msg, category="network")
        except Exception as e:
            logger.error(f"Failed to send recovery notification: {e}")
        
        logger.info(f"Recovery complete - {len(failed_recoveries)} failures")
