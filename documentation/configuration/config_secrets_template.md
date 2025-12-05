# 🔐 config_secrets.py Template

> **Navigace:** [📂 Dokumentace](../README.md) | [⚙️ Konfigurace](../README.md#konfigurace) | [config_secrets.py Template](config_secrets_template.md)

> Šablona pro soubor s tajnými klíči. Tento soubor **NIKDY** necommitujte do Gitu!
> **Verze:** Alpha

---

<a name="použití"></a>
## 📝 Použití

1. Vytvořte soubor `config_secrets.py` v kořenovém adresáři (vedle `main.py`).
2. Zkopírujte obsah níže.
3. Nahraďte hodnoty svými skutečnými klíči.

---

<a name="template"></a>

<a name="šablona"></a>
## 📄 Šablona

```python
# config_secrets.py
# ⚠️ NIKDY NECOMMITUJ DO GITU!

# === DISCORD BOT TOKEN ===
# Získej z: https://discord.com/developers/applications
# Musí začínat "MT"
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"

# === ADMIN USER IDS ===
# Seznam ID uživatelů, kteří mají plný přístup k agentovi
ADMIN_USER_IDS = [
    123456789012345678  # Tvoje Discord User ID
]

# === NGROK (Optional) ===
# Získej z: https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTH_TOKEN = "your_ngrok_token_here"

# === GITHUB TOKEN (Optional) ===
# Pro auto-release funkcionalitu
GITHUB_TOKEN = "your_github_token_here"

# === API KEYS (Optional) ===
# Add any future API keys here
```

---

<a name="getting-discord-token"></a>

<a name="získání-discord-bot-tokenu"></a>
## 🔐 Získání Discord Bot Tokenu

1. **Jdi na:** https://discord.com/developers/applications
2. **Vytvoř aplikaci:** "New Application"
3. **Bot tab:** Add Bot
4. **Token:** Reset Token → **Copy**
5. **Intents:** ZAPNI všechny:
   - ✅ **MESSAGE CONTENT INTENT** (CRITICAL!)
   - ✅ Presence Intent
   - ✅ Server Members Intent
6. **OAuth2:** Generate invite URL s permissions:
   - `bot`
   - `applications.commands`
   - Permissions: `Send Messages`, `Read Messages`, `Embed Links`, `Attach Files`

---

<a name="security-best-practices"></a>
## 🛡️ Security Best Practices

Ujistěte se, že váš `.gitignore` obsahuje:
```bash
config_secrets.py
*.db
agent.log
```

---
Poslední aktualizace: 2025-12-04  
Verze: Alpha  
Tip: Použij Ctrl+F pro vyhledávání
