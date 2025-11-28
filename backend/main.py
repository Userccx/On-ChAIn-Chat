import logging

from flask import Flask, jsonify
from flask_cors import CORS

from .config import settings
from .routes import auth_routes, chat_routes, mint_routes
from .utils.logger import setup_logger, set_global_log_level

# 初始化日志系统
log_level = logging.DEBUG if settings.DEBUG else logging.INFO
set_global_log_level(log_level)  # 设置全局日志级别，让所有模块使用
logger = setup_logger("flask_app", log_level)
logger.info(f"Starting {settings.APP_NAME}")
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Debug mode: {settings.DEBUG}")

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
