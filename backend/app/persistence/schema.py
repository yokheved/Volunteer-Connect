from sqlalchemy import inspect, text

from app.extensions import db

_LOCATION_COLUMNS = (
    ("google_place_id", "VARCHAR(255)", "VARCHAR(255) NULL"),
    ("latitude", "FLOAT", "FLOAT NULL"),
    ("longitude", "FLOAT", "FLOAT NULL"),
    ("location_cached_at", "DATETIME", "DATETIME NULL"),
)


def ensure_user_location_columns() -> None:
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("users")}
    dialect = db.engine.dialect.name
    added = False
    for name, sqlite_type, mssql_type in _LOCATION_COLUMNS:
        if name in existing:
            continue
        if dialect == "sqlite":
            db.session.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sqlite_type}"))
        else:
            db.session.execute(text(f"ALTER TABLE users ADD {name} {mssql_type}"))
        added = True
    if added:
        db.session.commit()
