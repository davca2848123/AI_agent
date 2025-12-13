# Discord Client

> **Navigace:** [📂 Dokumentace](../README.md) | [🧠 Core](../README.md#core-jádro) | [Discord Client](discord-client.md)

> Integrace s Discord API pro komunikaci.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

`DiscordClient` třída poskytuje asynchronní rozhraní pro komunikaci s Discord serverem.

---

<a name="initialization"></a>

<a name="inicializace"></a>
## Inicializace

<a name="constructor"></a>
### 🔧 Constructor

```python
from agent.discord_client import DiscordClient

discord = DiscordClient(token="DISCORD_TOKEN")
```

**Parametry:**
- `token` *(optional)* - Discord bot token (nebo z ENV)

---

<a name="starting"></a>

<a name="spuštění"></a>
## Spuštění

<a name="start"></a>
### ⚙️ start()

```python
await discord.start()
```

Spustí Discord klienta v background task a registruje event handlery.

<a name="event-handlers"></a>
### 💡 Event Handlers

**on_ready:**
```python
@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    self.is_ready = True
```

**on_message:**
```python
@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return
    
    # Queue message for agent
    await message_queue.put({
        "content": message.content,
        "author": message.author.name,
        "author_id": message.author.id,
        "channel_id": message.channel.id,
        "is_dm": isinstance(message.channel, discord.DMChannel),
        "mentions_bot": client.user in message.mentions
    })
```

---

<a name="sending-messages"></a>

<a name="posílání-zpráv"></a>
## Posílání Zpráv

<a name="send_message"></a>
### 📤 send_message()

```python
msg = await discord.send_message(
    channel_id=123456789,
    content="Hello world!",
    file_path="/path/to/file.txt",  # optional
    view=custom_view  # optional
)
```

**Parametry:**
- `channel_id` *(required)* - ID Discord kanálu
- `content` *(required)* - Text zprávy
- `file_path` *(optional)* - Cesta k souboru pro attachment
- `view` *(optional)* - Discord UI View (tlačítka)

**Vrací:**
- Discord Message object (pro editaci)

<a name="příklady"></a>
### 💡 Příklady

**Jednoduchá zpráva:**
```python
await discord.send_message(
    channel_id=123456789,
    content="✅ Task completed!"
)
```

**S attachmentem:**
```python
await discord.send_message(
    channel_id=123456789,
    content="📊 Here are the logs:",
    file_path="logs_export.txt"
)
```

**S interaktivními tlačítky:**
```python
class MyView(discord.ui.View):
    @discord.ui.button(label="Click me", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, button):
        await interaction.response.send_message("Button clicked!")

view = MyView()
await discord.send_message(
    channel_id=123456789,
    content="Interactive message:",
    view=view
)
```

---

<a name="receiving-messages"></a>

<a name="příjem-zpráv"></a>
## Příjem Zpráv

<a name="get_messages"></a>
### 📥 get_messages()

```python
messages = await discord.get_messages()
```

Vrátí všechny zprávy z fronty (FIFO).

**Formát zprávy:**
```python
{
    "content": "!help",
    "author": "Username",
    "author_id": 123456789,
    "channel_id": 987654321,
    "is_dm": False,
    "mentions_bot": True
}
```

---

<a name="activity-status"></a>
## Activity Status

<a name="update_activity"></a>
### 🎮 update_activity()

```python
await discord.update_activity("Playing Minecraft")
```

Aktualizuje Discord status bota (zobrazuje se u jména).

**Použití v agentovi:**
```python
# Show boredom level
await discord.update_activity(f"Boredom: {int(boredom * 100)}%")

# Show current action
await discord.update_activity("Learning web_tool")
```

---

<a name="online-activities"></a>

<a name="online-aktivity"></a>
## Online Aktivity

<a name="get_online_activities"></a>
### 👥 get_online_activities()

```python
activities = await discord.get_online_activities()
```

Vrátí seznam aktivit (her, aplikací) online uživatelů.

**Formát:**
```python
[
    {
        "name": "Minecraft",
        "user_id": 123456789,
        "user_name": "John"
    },
    {
        "name": "Spotify",
        "user_id": 987654321,
        "user_name": "Sarah"
    }
]
```

**Využití:**
- Agent sleduje co uživatelé dělají
- Research neznámých aktivit pomocí web_tool
- Ukládání do paměti

---

<a name="configuration"></a>

<a name="konfigurace"></a>
## Konfigurace

<a name="intents"></a>
### 🔧 Intents

```python
intents = discord.Intents.default()
intents.message_content = True  # Read message content
intents.presences = True        # See user status/activities
intents.members = True          # Access member list

client = discord.Client(intents=intents, max_messages=10)
```

**max_messages=10:**
- Omezený cache (úspora paměti)
- Starší zprávy se automaticky zapomínají

---

<a name="mock-mode"></a>
## Mock Mode

<a name="běh-bez-discord-tokenu"></a>
### 🧪 Běh Bez Discord Tokenu

Pokud token není poskytnut, klient běží v mock mode:

```python
discord = DiscordClient()  # No token

# Mock responses
await discord.send_message(123, "Hello")
# Output: [MOCK DISCORD] Sending to 123: Hello
```

**Využití:**
- Testování bez Discord připojení
- Development na lokálním stroji
- CI/CD testy

---

<a name="error-handling"></a>
## Error Handling

<a name="graceful-degradation"></a>
### ⚠️ Graceful Degradation

```python
async def send_message(self, channel_id, content, ...):
    if not self.is_ready:
        logger.warning("Discord client not ready yet.")
        return
    
    try:
        channel = self.client.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found.")
            return
        
        await channel.send(content, ...)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
```

**Chování:**
- Pokud klient není ready, loguje warning
- Pokud kanál neexistuje, loguje error
- Pokud send selže, zachytí exception

---

---

<a name="connectivity"></a>
## Connectivity & Resilience

<a name="auto-reconnect"></a>
### 🔄 Reconnection Loop
The client is wrapped in a permanent **reconnection loop** to handle network failures and critical errors (e.g., `ClientConnectionResetError`).
- If the connection drops or the client crashes internally, the agent waits 5 seconds and attempts to restart the client entirely (`connector.start()`).
- This ensures the agent stays online even after temporary internet outages or API glitches.

<a name="startup-notifications"></a>
### 🔔 Reliable Notifications
Startup notifications (sent when agent comes online) have enhanced reliability:
- **Resilient Channel Cache**: If the Discord channel cache isn't ready immediately after login (common race condition), the agent fetches the channel directly from the API.
- **Retry Logic**: If sending the startup notification fails, it retries with exponential backoff (up to 3 times).

---

<a name="v-corepy"></a>
### 🔧 V core.py

```python
# Initialize Discord
self.discord = DiscordClient(token=discord_token)

# Start in background
asyncio.create_task(self.discord.start())

# Wait for ready
while not self.discord.is_ready:
    await asyncio.sleep(0.1)

# Process messages
while True:
    messages = await self.discord.get_messages()
    for msg in messages:
        await self.handle_command(msg)
    await asyncio.sleep(1)
```

---

<a name="související"></a>
## 🔗 Související

- [📖 Autonomous Behavior](autonomous-behavior.md) - Reakce na tier changes
- [📚 API Reference](../api/discord-client.md)
- [🏗️ Architektura](../architecture.md)
---
Poslední aktualizace: 2025-12-13  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
