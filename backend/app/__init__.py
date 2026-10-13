from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.config import Config, build_database_uri
from app.errors import AppError
from app.extensions import cors, db, jwt


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()

    uri = app.config.get("SQLALCHEMY_DATABASE_URI") or ""
    if uri.startswith("mssql+pyodbc"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"timeout": 15},
        }
    elif uri.startswith("mssql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"login_timeout": 10, "timeout": 10},
        }
    else:
        app.config.pop("SQLALCHEMY_ENGINE_OPTIONS", None)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["FRONTEND_ORIGIN"],
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            }
        },
    )

    from app.models import DomainEvent, User, VolunteerCategory  # noqa: F401
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.volunteers import volunteers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(volunteers_bp)
    _register_error_handlers(app)
    _register_jwt_handlers(app)

    with app.app_context():
        db.create_all()
        from app.persistence.schema import ensure_user_location_columns

        ensure_user_location_columns()

    return app


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500


def _register_jwt_handlers(app: Flask) -> None:
    from app.extensions import jwt_blocklist

    @jwt.token_in_blocklist_loader
    def is_token_revoked(_jwt_header, jwt_payload) -> bool:
        return jwt_payload.get("jti") in jwt_blocklist

    @jwt.unauthorized_loader
    def missing_token(reason: str):
        return jsonify({"error": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason: str):
        return jsonify({"error": reason}), 401

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_payload):
        return jsonify({"error": "Token has been revoked"}), 401

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return jsonify({"error": "Token has expired"}), 401
