from flask import Flask, jsonify
from flask_cors import CORS

from .config import settings
from .routes import auth_routes, chat_routes, mint_routes

app = Flask(__name__)
app.config["DEBUG"] = settings.DEBUG

# CORS configuration
CORS(
    app,
    origins=settings.ALLOWED_ORIGINS,
    supports_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register blueprints
app.register_blueprint(chat_routes.bp)
app.register_blueprint(mint_routes.bp)
app.register_blueprint(auth_routes.bp)


@app.route("/")
def root():
    return jsonify({"message": f"{settings.APP_NAME} API"})


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "environment": settings.ENVIRONMENT})
