import os
import asyncio
import urllib.parse
import discord
from discord.ext import commands
from fastapi import FastAPI, HTTPException
from fastapi import Request
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
    
    # 🔒 DIESE URL IST JETZT DURCH DIE YML FESTGEZURRT UND ÄNDERT SICH NIE WIEDER!
    TUNNEL_URL = "https://rsbtech-verify.loca.lt" 
    
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{TUNNEL_URL}/oauth/callback"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient() as client:
        try:
            token_res = await client.post(token_url, data=data, headers=headers)
            token_data = token_res.json()
            
            if "access_token" not in token_data:
                return HTMLResponse(f"""
                <body style="font-family: Arial; background-color: #23272A; color: white; padding: 20px;">
                    <h3 style="color: #ED4245;">Fehler beim Token-Austausch!</h3>
                    <p><b>Discord sagt:</b> {token_data}</p>
                    <p><b>Gesendete URI war:</b> {TUNNEL_URL}/oauth/callback</p>
                </body>
                """)
                
            access_token = token_data["access_token"]
            
            user_res = await client.get("https://discord.com/api/v10/users/@me", headers={
                "Authorization": f"Bearer {access_token}"
            })
            username = user_res.json().get("username", "Nutzer")

            connection_url = f"https://discord.com/api/v10/users/@me/applications/{CLIENT_ID}/role-connection"
            connection_body = {
                "platform_name": "Verifizierung",
                "platform_username": username,
                "metadata": {"is_verified": 1}
            }
            
            await client.put(connection_url, json=connection_body, headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            })

            return HTMLResponse(f"""
            <body style="font-family: Arial; text-align: center; padding-top: 100px; background-color: #23272A; color: white;">
                <h2 style="color: #57F287;">Perfekt, {username}!</h2>
                <p>Dein Account wurde verifiziert. Du kannst dieses Fenster jetzt schließen und deine Rolle auf Discord abholen!</p>
            </body>
            """)
            
        except Exception as e:
            return HTMLResponse(f"<h3 style='color:red;'>Fehler im Backend: {str(e)}</h3>")

# --- START BEIDER SYSTEME ---
async def main():
    # Wir binden den Webserver explizit an 127.0.0.1, damit localtunnel ihn fehlerfrei findet
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    asyncio.create_task(server.serve())
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
