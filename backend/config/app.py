import os
from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "curriermsj-secret")
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from backend.interfaces.api import api, serve_frontend, FRONTEND_DIR
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

    return app
