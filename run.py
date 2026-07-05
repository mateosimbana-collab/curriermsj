"""
CurrierMsj v2.0 - Clean Architecture / DDD / SOLID
"""
from backend.config.app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"CurrierMsj Backend v2.0 - http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
