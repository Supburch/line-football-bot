import os
from dotenv import load_dotenv

load_dotenv()

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
