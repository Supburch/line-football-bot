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

    TZ = pytz.timezone("Asia/Bangkok")
