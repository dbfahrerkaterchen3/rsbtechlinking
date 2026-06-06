import os
import discord
from discord.ext import commands
import httpx

# 1. BOT SETUP
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Hier holen wir die Daten aus den GitHub "Secrets", die du angelegt hast
APP_ID = os.getenv("DISCORD_APPLICATION_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

@bot.event
async def on_ready():
    print(f"🤖 Bot ist online als {bot.user}")
    
    # AUTOMATISCHE REGISTRIERUNG DER ROLLE (Ersetzt register_metadata.py!)
    url = f"https://discord.com/api/v10/applications/{APP_ID}/role-connections/metadata"
    metadata_fields = [
        {
            "key": "is_verified",
            "name": "Account verifiziert", # So heißt deine Bedingung in Discord
            "description": "Nutzer ist erfolgreich verifiziert",
            "type": 7  # Ja/Nein Feld
        }
    ]
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Wir schicken das einmal kurz an Discord
    async with httpx.AsyncClient() as client:
        res = await client.put(url, json=metadata_fields, headers=headers)
        if res.status_code == 200:
            print("✅ Überraschung! Die Rolle wurde ganz ohne Extra-Skript bei Discord registriert!")
        else:
            print(f"❌ Fehler beim Registrieren: {res.text}")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
