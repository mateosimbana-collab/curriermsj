import os
from flask import Flask, request
from flask_cors import CORS


def create_app() -> Flask:
    jwt_secret = os.getenv("JWT_SECRET", "")
    if len(jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET debe tener al menos 32 caracteres")

    app = Flask(__name__, static_folder=None)

    app.config["SECRET_KEY"] = jwt_secret
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", str(1024 * 1024)))

    cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    from backend.interfaces.api import api, serve_frontend
    app.register_blueprint(api)

    # WhatsApp webhook (bot-mensajeria integration)
    from backend.interfaces.webhook import webhook_bp
    app.register_blueprint(webhook_bp)

    frontend_handler = serve_frontend()

    @app.route("/")
    @app.route("/<path:path>")
    def frontend(path=""):
        return frontend_handler(path)

    @app.errorhandler(404)
    def not_found(e):
        return {"ok": False, "error": "Not found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"ok": False, "error": "Internal server error"}, 500

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cache-Control", "no-store" if request.path.startswith("/api/") else "no-cache")
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    return app
