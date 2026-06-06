import os
import requests
from dotenv import load_dotenv

# Lädt die IDs und Token sicher aus deiner lokalen .env Datei
load_dotenv()

APP_ID = os.getenv("DISCORD_APPLICATION_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not APP_ID or not BOT_TOKEN:
    print("❌ Fehler: DISCORD_APPLICATION_ID oder DISCORD_BOT_TOKEN fehlt in der .env-Datei!")
    exit(1)

# Die URL, um die Linked Roles für deine App bei Discord zu registrieren
url = f"https://discord.com/api/v10/applications/{APP_ID}/role-connections/metadata"

# Hier definierst du die "Felder", die deine Hugging Face Space später beschreiben darf
metadata_fields = [
    {
        "key": "is_verified", # Das ist der interne Name für deinen Code (wichtig für die HF Space!)
        "name": "Account verifiziert", # Das sieht der Admin/Nutzer in Discord
        "description": "Nutzer hat sich erfolgreich auf der HF Space angemeldet",
        "type": 7  # Typ 7 steht bei Discord für ein Boolean-Feld (True/False oder 1/0)
    }
]

headers = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

print("🔄 Sende Metadaten an Discord...")
response = requests.put(url, json=metadata_fields, headers=headers)

if response.status_code == 200:
    print("✅ Erfolg! Die Linked Roles Metadaten wurden bei Discord registriert.")
    print("Du kannst jetzt in deinen Discord-Servereinstellungen die Verknüpfung sehen.")
else:
    print(f"❌ Fehler aufgetreten: {response.status_code}")
    print(response.text)
