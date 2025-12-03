import discord
import asyncio
import sys
import os

# Add parent directory to path to import config_settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import config_settings
    import config_secrets
except ImportError:
    print("Error: Could not import config_settings or config_secrets. Make sure you are running this from the correct directory.")
    sys.exit(1)

class DMCleaner(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.dm_messages = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        
        if not config_settings.ADMIN_USER_IDS:
            print("No ADMIN_USER_IDS defined in config.")
            await self.close()
            return

        admin_id = config_settings.ADMIN_USER_IDS[0]
        try:
            # Load active message IDs to skip
            import json
            active_msg_ids = set()
            try:
                with open("workspace/agent_state.json", "r") as f:
                    state = json.load(f)
                    
                    # Handle new format (admin_dms dict)
                    if "admin_dms" in state:
                        for category, data in state["admin_dms"].items():
                            if "id" in data:
                                active_msg_ids.add(data["id"])
                    
                    # Handle legacy format (fallback)
                    if "last_admin_dm_id" in state:
                        active_msg_ids.add(state["last_admin_dm_id"])
                        
                    print(f"Skipping active message IDs: {active_msg_ids}")
            except Exception as e:
                print(f"Could not load agent state (will delete all): {e}")

            user = await self.fetch_user(admin_id)
            print(f"Target Admin: {user.name} ({user.id})")
            
            dm_channel = await user.create_dm()
            print("Fetching message history...")
            
            deleted_count = 0
            async for msg in dm_channel.history(limit=None):
                if msg.author == self.user:
                    # Skip active messages
                    if msg.id in active_msg_ids:
                        print(f"Skipping active message {msg.id}")
                        continue

                    try:
                        await msg.delete()
                        deleted_count += 1
                        if deleted_count % 10 == 0:
                            print(f"Deleted {deleted_count} messages...", end='\r')
                    except Exception as e:
                        print(f"Failed to delete message {msg.id}: {e}")
            
            print(f"\nDone! Deleted {deleted_count} messages.")
            print("Note: Bots cannot delete messages sent by other users in DMs.")
            
        except Exception as e:
            print(f"Error: {e}")
        
        await self.close()

if __name__ == "__main__":
    if not hasattr(config_secrets, 'DISCORD_TOKEN') or not config_secrets.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in config_secrets.")
        sys.exit(1)
        
    client = DMCleaner()
    client.run(config_secrets.DISCORD_TOKEN)
