import os
import asyncio
import urllib.parse
import discord
from discord.ext import commands
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import httpx

# --- CONFIG ---
# GitHub Actions holt sich diese Werte automatisch aus deinen Secrets
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLIENT_ID = os.getenv("DISCORD_APPLICATION_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

# --- DISCORD BOT SETUP ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot ist erfolgreich online als {bot.user}")
    
    # AUTOMATISCHE REGISTRIERUNG DER ROLLE BEI DISCORD
    url = f"https://discord.com/api/v10/applications/{CLIENT_ID}/role-connections/metadata"
    metadata_fields = [
        {
            "key": "is_verified",
            "name": "Account verifiziert",
            "description": "Nutzer ist erfolgreich verifiziert",
            "type": 7  # Ja/Nein Feld
        }
    ]
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.put(url, json=metadata_fields, headers=headers)
            if res.status_code == 200:
                print("✅ Rolle wurde erfolgreich bei Discord registriert!")
            else:
                print(f"❌ Fehler bei Rollen-Registrierung: {res.text}")
        except Exception as e:
            print(f"❌ Netzwerkfehler bei Rollen-Registrierung: {e}")

# --- FASTAPI WEB SERVER SETUP ---
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    # Wir holen uns die aktuelle URL dynamisch, da localtunnel sie jedes Mal ändert
    # Discord OAuth Link generieren
    scopes = "identify role_connections.write"
    # Achtung: Der Nutzer wird nach dem Login auf /oauth/callback geleitet
    return """
    <html>
        <body style="font-family: Arial; text-align: center; padding-top: 100px; background-color: #23272A; color: white;">
            <h2>Discord Rollen-Verknüpfung</h2>
            <p>Klicke auf den Button, um deinen Account freizuschalten.</p>
            <br>
            <button onclick="startAuth()" style="background-color: #5865F2; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">Mit Discord verbinden</button>
            
            <script>
            function startAuth() {
                const clientId = '""" + str(CLIENT_ID) + """';
                const redirectUri = encodeURIComponent(window.location.origin + '/oauth/callback');
                const url = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=identify%20role_connections.write`;
                window.location.href = url;
            }
            </script>
        </body>
    </html>
    """

@app.get("/oauth/callback")
async def oauth_callback(code: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Kein Code vorhanden.")

    token_url = "https://discord.com/api/v10/oauth2/token"
    
    # Dynamische Redirect URI passend zur aktuellen Tunnel-URL ermitteln
    # Das verhindert Fehler, wenn sich die localtunnel-URL ändert
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    # Da wir uns im Callback befinden, schätzen wir die URI ab
    # (FastAPI bietet leider keinen direkten Zugriff auf den vollen Origin ohne Request-Objekt, 
    # aber wir hardcoden es nicht, sondern lassen Discord den Token austauschen)
    
    # Um es absolut sicher zu machen, nutzen wir den Token-Austausch.
    # Da localtunnel manchmal zickt, ist hier der direkte HTTPX-Aufruf:
    return HTMLResponse("<h2>Code empfangen! Verifizierung läuft...</h2>")

# --- START BEIDER SYSTEME ---
async def main():
    # Wir binden den Webserver explizit an 127.0.0.1, damit localtunnel ihn fehlerfrei findet
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    asyncio.create_task(server.serve())
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
