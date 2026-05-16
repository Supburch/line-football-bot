import os
import sys
import traceback
from dotenv import load_dotenv

# Force unbuffered output so we see logs in Render immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()

print("🚀 BOOTING APP...", flush=True)

try:
    from app.config import Config
    print(f"✅ LINE_TOKEN: {bool(Config.LINE_TOKEN)}", flush=True)
    print(f"✅ FOOTBALL_API_KEY: {bool(Config.FOOTBALL_API_KEY)}", flush=True)
    
    from app.main import create_app
    app = create_app()
    print("✅ create_app() success!", flush=True)

except Exception as e:
    print("❌ FATAL CRASH DURING BOOT:", flush=True)
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
