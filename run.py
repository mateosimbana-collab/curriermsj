"""CurrierMsj unified Flask entry point."""
import os

from dotenv import load_dotenv
from backend.config.app import create_app

load_dotenv()

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"CurrierMsj Backend v2.0 - http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
