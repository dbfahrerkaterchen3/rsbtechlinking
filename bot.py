import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Lädt Variablen aus einer lokalen .env Datei (wichtig für die lokale Entwicklung)
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Bot-Intents festlegen
intents = discord.Intents.default()
intents.message_content = True  # Falls der Bot Nachrichten lesen soll

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot ist erfolgreich online als {bot.user}")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Fehler: Kein DISCORD_BOT_TOKEN in den Umgebungsvariablen gefunden!")
