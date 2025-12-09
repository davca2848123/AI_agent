import asyncio
import logging
import sys
import os
import platform
import signal

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import sanitizer for console IP masking
from agent.sanitizer import sanitize_output
import config_settings

# Custom formatter for console with IP sanitization
class SanitizingFormatter(logging.Formatter):
    """Formatter that sanitizes IP addresses in console output."""
    def format(self, record):
        formatted = super().format(record)
        if getattr(config_settings, 'IP_SANITIZATION_ENABLED', True):
            return sanitize_output(formatted)
        return formatted

# Configure logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(SanitizingFormatter(
    f'%(asctime)s - [{platform.system()}/{platform.node()}] - %(name)s - %(levelname)s - %(message)s'
))

file_handler = logging.FileHandler(config_settings.LOG_FILE_MAIN, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    f'%(asctime)s - [{platform.system()}/{platform.node()}] - %(name)s - %(levelname)s - %(message)s'
))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[console_handler, file_handler]
)

# Silence noisy libraries
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("discord.client").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)
logging.getLogger("pyngrok").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Configure separate logger for tools (no duplication)
tools_logger = logging.getLogger('agent.tools')
tools_handler = logging.FileHandler(config_settings.LOG_FILE_TOOLS, encoding='utf-8')
tools_formatter = logging.Formatter(
    f'%(asctime)s - [{platform.system()}/{platform.node()}] - %(name)s - %(levelname)s - %(message)s'
)
tools_handler.setFormatter(tools_formatter)
tools_logger.addHandler(tools_handler)
tools_logger.propagate = False  # Prevent logging to agent.log

logger = logging.getLogger(__name__)

# Global reference for cleanup
agent_instance = None

async def shutdown(sig=None):
    """Gracefully shutdown the agent and Discord connection."""
    if sig:
        logger.info(f"Received exit signal {sig.name}...")
    else:
        logger.info("Shutting down...")
    
    # Close Discord connection immediately to go offline
    if agent_instance and agent_instance.discord and agent_instance.discord.client:
        logger.info("Closing Discord connection...")
        await agent_instance.discord.client.close()
    
    # Close database connection
    if agent_instance and hasattr(agent_instance.memory, 'conn'):
        agent_instance.memory.conn.close()
    
    logger.info("Shutdown complete.")

async def main():
    global agent_instance
    
    # Check startup failure tracking
    import config_settings
    from agent.startup_tracker import check_should_wait, record_failure, record_success
    
    should_wait, wait_time = check_should_wait(
        retry_limit=config_settings.STARTUP_RETRY_LIMIT,
        wait_hours=config_settings.STARTUP_FAILURE_WAIT // 3600
    )
    
    if should_wait:
        hours = int(wait_time // 3600)
        minutes = int((wait_time % 3600) // 60)
        logger.critical(
            f"🛑 STARTUP BLOCKED: Too many consecutive failures. "
            f"Waiting {hours}h {minutes}m before retry. "
            f"(Retry limit: {config_settings.STARTUP_RETRY_LIMIT})"
        )
        # Wait and exit
        await asyncio.sleep(wait_time)
        logger.info("Wait period complete, exiting for restart...")
        return
    
    logger.info("Starting Autonomous Embedded AI Agent (Windows Prototype)...")
    
    # Load Secrets
    try:
        import config_secrets
        discord_token = config_secrets.DISCORD_TOKEN
        github_token = getattr(config_secrets, 'GITHUB_TOKEN', None)
    except ImportError:
        logger.warning("config_secrets.py not found. Discord functionality may be limited.")
        discord_token = None
        github_token = None

    # GitHub Auto-Release - DISABLED to prevent restart loop
    # Now available only via !upload command with rate limiting
    # if github_token:
    #     async def run_github_release():
    #         """Run GitHub release in background"""
    #         try:
            #             from scripts.github_release import create_release
    #             logger.info("Starting GitHub auto-release...")
    #             success = create_release(
    #                 github_token=github_token,
    #                 repo_name="davca2848123/AI_agent"
    #             )
    #             if success:
    #                 logger.info("GitHub release completed successfully")
    #             else:
    #                 logger.warning("GitHub release failed")
    #         except Exception as e:
    #             logger.error(f"GitHub release error: {e}")
    #     
    #     # Start release in background (don't wait for it)
    #     asyncio.create_task(run_github_release())
    # else:
    #     logger.info("GitHub token not found, skipping  auto-release")
    
    logger.info("GitHub auto-release disabled. Use !upload command for manual releases.")

    # Initialize global stats early for error tracking
    daily_stats = None
    try:
        from agent.reports import DailyStats, DailyStatsLoggingHandler
        daily_stats = DailyStats()
        stats_handler = DailyStatsLoggingHandler(daily_stats)
        stats_handler.setLevel(logging.ERROR)
        logging.getLogger().addHandler(stats_handler)
        logger.info("Daily statistics tracking initialized early")
    except ImportError as e:
        logger.warning(f"Could not initialize daily stats early: {e}")

    # Initialize Agent with comprehensive error handling
    try:
        from agent.core import AutonomousAgent
        logger.info("Importing AutonomousAgent...")
        agent_instance = AutonomousAgent(discord_token=discord_token, daily_stats=daily_stats)
        logger.info("Agent instance created successfully")
    except ImportError as e:
        logger.critical(f"FATAL: Failed to import agent.core: {e}", exc_info=True)
        record_failure()
        raise
    except Exception as e:
        logger.critical(f"FATAL: Failed to initialize AutonomousAgent: {e}", exc_info=True)
        record_failure()
        raise
    
    # Run the agent with error handling
    try:
        logger.info("Starting agent...")
        await agent_instance.start()
        logger.info("Agent started successfully, entering main loop")
        # Record successful startup
        record_success()
    except Exception as e:
        logger.critical(f"FATAL: Agent.start() failed: {e}", exc_info=True)
        record_failure()
        raise
    
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Received shutdown signal")
        await shutdown()

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    if platform.system() != 'Windows':
        # Unix signals
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Windows uses KeyboardInterrupt
        pass
