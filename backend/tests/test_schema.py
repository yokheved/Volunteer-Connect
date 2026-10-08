from sqlalchemy import create_engine, inspect, text

from app import create_app
from app.extensions import db


def test_ensure_user_location_columns_adds_missing(tmp_path):
    database_uri = "sqlite:///" + (tmp_path / "legacy.db").as_posix()
    engine = create_engine(database_uri)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    phone VARCHAR(50) NOT NULL,
                    address VARCHAR(500) NOT NULL,
                    is_client BOOLEAN NOT NULL,
                    is_volunteer BOOLEAN NOT NULL,
                    monthly_hours_goal INTEGER,
                    about_me TEXT,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
    engine.dispose()

    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": database_uri,
            "JWT_SECRET_KEY": "test-secret-key-must-be-at-least-32-chars",
            "FRONTEND_ORIGIN": "http://localhost:5173",
        }
    )
    with application.app_context():
        names = {column["name"] for column in inspect(db.engine).get_columns("users")}
        assert "google_place_id" in names
        assert "latitude" in names
        assert "longitude" in names
        assert "location_cached_at" in names
        db.session.remove()
        db.drop_all()
