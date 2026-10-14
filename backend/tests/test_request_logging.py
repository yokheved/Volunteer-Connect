import logging
from pathlib import Path

from app import create_app
from app.logging_config import ACCESS_LOGGER_NAME, close_logging
from app.extensions import jwt_blocklist


def _flush_logs(app):
    for logger in (app.logger, logging.getLogger(ACCESS_LOGGER_NAME)):
        for handler in logger.handlers:
            handler.flush()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def test_access_log_records_unauthorized_profile_request(client, app):
    response = client.get("/api/users/me")
    assert response.status_code == 401

    _flush_logs(app)
    access = _read(Path(app.config["LOG_DIR"]) / "access.log")
    assert "method=GET" in access
    assert "path=/api/users/me" in access
    assert "status=401" in access
    assert "ip=" in access


def test_login_password_is_not_written_to_logs(client, app):
    secret = "super-secret-password-do-not-log"
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": secret},
    )
    assert response.status_code in {400, 401}

    _flush_logs(app)
    log_dir = Path(app.config["LOG_DIR"])
    combined = _read(log_dir / "access.log") + _read(log_dir / "app.log")
    assert secret not in combined
    assert "Bearer" not in combined


def test_error_logger_writes_marker_to_error_file(app):
    app.logger.error("marker")
    _flush_logs(app)

    log_dir = Path(app.config["LOG_DIR"])
    assert "marker" in _read(log_dir / "error.log")
    assert "marker" not in _read(log_dir / "access.log")


def test_access_logger_failure_still_returns_response(client, monkeypatch):
    access_logger = logging.getLogger(ACCESS_LOGGER_NAME)

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(access_logger, "info", boom)
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert response.get_json()["error"]


def test_small_max_bytes_creates_rotated_backup(tmp_path):
    jwt_blocklist.clear()
    log_dir = tmp_path / "rotate-logs"
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (tmp_path / "rotate.db").as_posix(),
            "JWT_SECRET_KEY": "test-secret-key-must-be-at-least-32-chars",
            "FRONTEND_ORIGIN": "http://localhost:5174",
            "LOG_DIR": str(log_dir),
            "LOG_MAX_BYTES": 400,
            "LOG_BACKUP_COUNT": 5,
        }
    )
    try:
        access_logger = logging.getLogger(ACCESS_LOGGER_NAME)
        for _ in range(40):
            access_logger.info(
                "ip=127.0.0.1 origin=- method=GET path=/api/users/me status=401 extra=%s",
                "x" * 80,
            )
            _flush_logs(application)
        names = {path.name for path in log_dir.iterdir()}
        assert "access.log" in names
        assert any(name.startswith("access.log.") for name in names)
    finally:
        close_logging(application)
        jwt_blocklist.clear()
