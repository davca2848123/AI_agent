# 🤖 Discord Client API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Discord Client](discord-client.md)

Dokumentace pro `DiscordClient` v `agent/discord_client.py`.

<a name="přehled"></a>
## 📋 Přehled

Wrapper kolem `discord.py` knihovny, který zjednodušuje odesílání zpráv, správu stavu a příjem příkazů.

<a name="třída-discordclient"></a>
## 🔧 Třída DiscordClient

```python
class DiscordClient:
    def __init__(self, token: Optional[str] = None)
```

<a name="hlavní-metody"></a>
### Hlavní Metody

<a name="startself"></a>
#### `start(self)`
Spustí Discord klienta na pozadí (asyncio task).

<a name="send_messageself-channel_id-int-content-str-none"></a>
#### `send_message(self, channel_id: int, content: str = None, ...)`
Odešle zprávu do kanálu.
- **file_path**: Cesta k souboru pro upload.
- **embed**: Discord Embed objekt.
- **view**: Discord UI View (tlačítka).

<a name="get_messagesself"></a>
#### `get_messages(self)`
Vrátí seznam přijatých zpráv z fronty.

<a name="update_activityself-status-str"></a>
#### `update_activity(self, status: str)`
Změní status bota (např. "Playing Minecraft").

<a name="get_online_activitiesself"></a>
#### `get_online_activities(self)`
Vrátí seznam aktivit ostatních uživatelů na serveru (pro monitoring).

<a name="související"></a>
## 🔗 Související
- [📖 Discord Client Guide](../core/discord-client.md) - Detailní popis integrace a eventů
- [🏗️ Architektura](../architecture.md)
- **📂 Source Code:** `agent/`
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
