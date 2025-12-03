# Discord Client

> Integrace s Discord API pro komunikaci

## 📋 Přehled

`DiscordClient` třída poskytuje asynchronní rozhraní pro komunikaci s Discord serverem.

---

## Inicializace

### 🔧 Constructor

```python
from agent.discord_client import DiscordClient

discord = DiscordClient(token="DISCORD_TOKEN")
```

**Parametry:**
- `token` *(optional)* - Discord bot token (nebo z ENV)

---

## Spuštění

### ⚙️ start()

```python
await discord.start()
```

Spustí Discord klienta v background task a registruje event handlery.

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

## Posílání Zpráv

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

## Příjem Zpráv

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

## Activity Status

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

## Online Aktivity

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

## Konfigurace

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

## Mock Mode

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

## Error Handling

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

## Integration

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

## 🔗 Související

- [Commands](../commands/) - Příkazy přes Discord
- [Autonomous Behavior](autonomous-behavior.md) - Agent posílá updates
- [Admin Commands](../commands/admin.md#ssh) - SSH notifications

---

**Poslední aktualizace:** 2025-12-02  
**Verze:** 1.0.0
