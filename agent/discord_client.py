import asyncio
import logging
import os
import time
from typing import Optional

try:
    import discord
except ImportError:
    discord = None

# Import sanitizer for IP masking
from .sanitizer import sanitize_output
import config_settings

logger = logging.getLogger(__name__)

# Setup specific logger for Discord messages
msg_logger = logging.getLogger('discord_messages')
msg_logger.setLevel(logging.INFO)
# Prevent propagation to root logger to avoid duplication in agent.log if not desired
# But user wants "Match agent.log format", so maybe we want it separate?
# "Create new logger... Log all sent messages... Include channel_id"
# We'll add a FileHandler.
if not msg_logger.handlers:
    try:
        msg_handler = logging.FileHandler('discord_messages.log', encoding='utf-8')
        msg_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        msg_logger.addHandler(msg_handler)
    except Exception as e:
        logger.error(f"Failed to setup discord_messages.log: {e}")

class DiscordClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("DISCORD_TOKEN")
        self.client = None
        self.is_ready = False
        
        if discord:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.presences = True
            intents.members = True
            # Disable cache for memory efficiency as per spec
            self.client = discord.Client(intents=intents, max_messages=10)
            
        self.message_queue = asyncio.Queue()
        self.last_message_history = []
        self.last_message_id = None
        self.current_command_messages = [] # List of {id, content, timestamp, edits: []}

    async def start(self):
        """Starts the Discord client in a background task."""
        if not self.token:
            logger.warning("No Discord token provided. Running in mock mode.")
            self.is_ready = True
            return

        if not self.client:
            logger.error("discord.py not installed.")
            return

        @self.client.event
        async def on_ready():
            logger.info(f"Logged in as {self.client.user}")
            self.is_ready = True

        @self.client.event
        async def on_message(message):
            # Ignore own messages
            if message.author == self.client.user:
                return
            
            # Put message into queue for the agent to process
            await self.message_queue.put({
                "content": message.content,
                "author": message.author.name,
                "author_id": message.author.id,
                "channel_id": message.channel.id,
                "is_dm": isinstance(message.channel, discord.DMChannel),
                "mentions_bot": self.client.user in message.mentions
            })
            logger.info(f"Received message from {message.author.name}: {message.content}")

        @self.client.event
        async def on_message_edit(before, after):
            # Track edits to our own last message
            if before.author == self.client.user:
                if self.last_message_id and before.id == self.last_message_id:
                    # Append new version to history
                    self.last_message_history.append({
                        "timestamp": time.time(),
                        "content": after.content
                    })
                    logger.debug(f"Tracked message edit: {after.content[:50]}...")
            
            # Also update in current_command_messages
            for msg_entry in self.current_command_messages:
                if msg_entry['id'] == before.id:
                    msg_entry['edits'].append({
                        "timestamp": time.time(),
                        "content": after.content
                    })
                    break

        # Run client in background
        async def run_client():
            try:
                await self.client.start(self.token)
            except Exception as e:
                logger.critical(f"Discord client failed to start: {e}")
                self.is_ready = False # Ensure it stays false
        
        asyncio.create_task(run_client())

    def clear_message_history(self):
        """Clears the history of messages sent during the current command."""
        self.current_command_messages = []



    async def get_messages(self):
        """Retrieves queued messages."""
        messages = []
        while not self.message_queue.empty():
            messages.append(await self.message_queue.get())
        return messages

    async def send_message(self, channel_id: int, content: str = None, file_path: Optional[str] = None, view=None, embed=None):
        """Sends a message to a specific channel, optionally with a file, view, or embed."""
        if not self.token or not self.client:
            logger.info(f"[MOCK DISCORD] Sending to {channel_id}: {content} (File: {file_path})")
            return

        if not self.is_ready:
            logger.warning("Discord client not ready yet.")
            return

        try:
            channel = self.client.get_channel(channel_id)
            
            # Apply IP sanitization if enabled
            should_sanitize = getattr(config_settings, 'IP_SANITIZATION_ENABLED', True)
            
            if should_sanitize and content:
                # Default to True
                is_safe_admin_dm = False
                
                if channel and isinstance(channel, discord.DMChannel):
                    # Check if recipient is admin
                    if hasattr(channel, 'recipient') and channel.recipient.id in config_settings.ADMIN_USER_IDS:
                        is_safe_admin_dm = True
                
                if not is_safe_admin_dm:
                    content = sanitize_output(content)
            
            if channel:
                if file_path and os.path.exists(file_path):
                    file = discord.File(file_path)
                    msg = await channel.send(content, file=file, view=view, embed=embed)
                else:
                    msg = await channel.send(content, view=view, embed=embed)
                
                # Log outgoing messages for debugging
                log_content = content if content else (f"[Embed: {embed.title}]" if embed else "[No content]")
                logger.info(f"Sent message to channel {channel_id}: {log_content[:100]}{'...' if len(log_content) > 100 else ''}")
                
                # Log to dedicated discord_messages.log
                try:
                    msg_logger.info(f"Channel: {channel_id} | Type: {'Embed' if embed else 'Text'} | Content: {log_content}")
                except Exception as e:
                    logger.error(f"Failed to log to discord_messages.log: {e}")
                
                # Store last sent message for reporting
                self.last_sent_message = content # Keep for backward compatibility
                self.last_message_id = msg.id
                self.last_message_history = [{
                    "timestamp": time.time(),
                    "content": content
                }]
                
                # Add to current command messages
                self.current_command_messages.append({
                    "id": msg.id,
                    "content": content,
                    "timestamp": time.time(),
                    "edits": []
                })
                return msg
            else:
                logger.error(f"Channel {channel_id} not found.")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")


    async def update_activity(self, status: str):
        """Updates the bot's activity status."""
        if not self.token or not self.client or not self.is_ready:
            logger.debug(f"[MOCK DISCORD] Status update: {status}")
            return

        try:
            activity = discord.Game(name=status)
            await self.client.change_presence(activity=activity)
            logger.debug(f"Discord status updated to: {status}")
        except Exception as e:
            logger.error(f"Failed to update activity: {e}")

    async def get_online_activities(self) -> list:
        """Returns a list of activities with user info currently being performed by online users."""
        if not self.token or not self.client or not self.is_ready:
            return []
            
        activities = []
        try:
            for guild in self.client.guilds:
                for member in guild.members:
                    if not member.bot and member.activities:
                        for activity in member.activities:
                            # Filter for playing games or custom status
                            if activity.type == discord.ActivityType.playing:
                                activities.append({
                                    "name": activity.name,
                                    "user_id": member.id,
                                    "user_name": member.name
                                })
        except Exception as e:
            logger.error(f"Error fetching activities: {e}")
            
        return activities
