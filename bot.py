import os
import asyncio
import urllib.parse
import discord
from discord.ext import commands
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import httpx
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLIENT_ID = os.getenv("DISCORD_APPLICATION_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
# Da GitHub Actions eine temporäre IP hat, nutzen wir ngrok oder localhost zum Testen,
# bzw. für den lokalen Test reicht das völlig aus:
REDIRECT_URI = "http://localhost:8000/oauth/callback" 

# --- DISCORD BOT BOT-SETUP ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot ist erfolgreich online als {bot.user}")

# --- FASTAPI WEB-SETUP ---
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    scopes = "identify role_connections.write"
    encoded_redirect = urllib.parse.quote(REDIRECT_URI, safe='')
    discord_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={encoded_redirect}"
        f"&response_type=code"
        f"&scope={scopes}"
    )
    return f"""
    <html>
        <body style="font-family: Arial; text-align: center; padding-top: 100px; background-color: #23272A; color: white;">
            <h2>Discord Rollen-Verknüpfung via GitHub Backend</h2>
            <br>
            <a href="{discord_url}" style="background-color: #5865F2; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Mit Discord verbinden</a>
        </body>
    </html>
    """

@app.get("/oauth/callback")
async def oauth_callback(code: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Kein Code vorhanden.")

    token_url = "https://discord.com/api/v10/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data, headers=headers)
        token_data = token_res.json()
        
        if "access_token" not in token_data:
            return HTMLResponse(f"Fehler: {token_data}")
            
        access_token = token_data["access_token"]
        
        # Nutzerdaten holen
        user_res = await client.get("https://discord.com/api/v10/users/@me", headers={"Authorization": f"Bearer {access_token}"})
        username = user_res.json().get("username", "Nutzer")

        # Metadaten setzen
        connection_url = f"https://discord.com/api/v10/users/@me/applications/{CLIENT_ID}/role-connection"
        connection_body = {"platform_name": "GitHub Verifizierung", "platform_username": username, "metadata": {"is_verified": 1}}
        
        await client.put(connection_url, json=connection_body, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})

        return HTMLResponse(f"<h2>Erfolgreich verifiziert, {username}! Du kannst das Fenster schließen.</h2>")

# --- START BEIDER SYSTEME ---
async def main():
    # Startet den Webserver im Hintergrund
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    asyncio.create_task(server.serve())
    
    # Startet den Discord Bot
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
