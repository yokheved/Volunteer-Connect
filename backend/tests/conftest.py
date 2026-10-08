import pytest

from app import create_app
from app.extensions import db, jwt_blocklist


@pytest.fixture
def app(tmp_path):
    jwt_blocklist.clear()
    database_uri = "sqlite:///" + (tmp_path / "test.db").as_posix()
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": database_uri,
            "JWT_SECRET_KEY": "test-secret-key-must-be-at-least-32-chars",
            "FRONTEND_ORIGIN": "http://localhost:5174",
        }
    )
    yield application
    jwt_blocklist.clear()
    with application.app_context():
        db.drop_all()
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()
