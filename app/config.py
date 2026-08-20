import os
import pytz
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, required: bool = False) -> str:
    val = os.getenv(key)
    if required and not val:
        raise RuntimeError(f"Missing required ENV: {key}")
    return val or ""

class Config:
    LINE_TOKEN = get_env("LINE_CHANNEL_ACCESS_TOKEN", required=True)
    LINE_SECRET = get_env("LINE_CHANNEL_SECRET", required=True)
    FOOTBALL_API_KEY = get_env("FOOTBALL_API_KEY", required=True)
    SUPABASE_URL = get_env("SUPABASE_URL")
    SUPABASE_KEY = get_env("SUPABASE_KEY")

    # The public URL of the bot, needed to serve local images to LINE.
    # LINE requires HTTPS for image URLs, so normalize any non-localhost
    # http:// value (Render terminates TLS and forwards http to the app).
    BASE_URL = os.getenv("BASE_URL")
    if BASE_URL:
        BASE_URL = BASE_URL.rstrip('/')
        if BASE_URL.startswith("http://") and "localhost" not in BASE_URL and "127.0.0.1" not in BASE_URL:
            BASE_URL = BASE_URL.replace("http://", "https://", 1)

    TZ = pytz.timezone("Asia/Bangkok")
