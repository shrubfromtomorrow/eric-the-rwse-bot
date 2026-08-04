import aiohttp
import time
import os
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.environ['TWITCH_CLIENT_ID']
CLIENT_SECRET = os.environ['TWITCH_CLIENT_SECRET']
CHANNEL_ID = "806548337"  # Twitch user ID

_token = None
_token_expiry = 0

# I have no idea what the fuck im doing dawg im sorry if this breaks

async def get_token():
    global _token, _token_expires

    if _token and time.time() < _token_expires:
        return _token

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        ) as r:
            data = await r.json()

            if "access_token" not in data:
                raise RuntimeError(f"Twitch token error: {data}")

    _token = data["access_token"]
    _token_expires = time.time() + data["expires_in"] - 300

    return _token

async def get_latest_vod():
    token = await get_token()

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(
            "https://api.twitch.tv/helix/videos",
            params={
                "user_id": CHANNEL_ID,
                "type": "archive",
                "first": 1,
            },
        ) as r:

            if r.status == 401:
                global _token
                _token = None
                return await get_latest_vod()

            data = await r.json()

    if not data.get("data"):
        return None

    return data["data"][0]["url"]