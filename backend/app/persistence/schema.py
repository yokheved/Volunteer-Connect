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


# Free-text columns that must hold Hebrew. On SQL Server, VARCHAR with a Latin
# collation stores Hebrew as "?", so these are NVARCHAR.
_UNICODE_COLUMNS = (
    ("users", "name", "NVARCHAR(255) NOT NULL"),
    ("users", "address", "NVARCHAR(500) NOT NULL"),
    ("users", "about_me", "NVARCHAR(MAX) NULL"),
    ("volunteer_requests", "location", "NVARCHAR(500) NOT NULL"),
    ("volunteer_requests", "description", "NVARCHAR(MAX) NOT NULL"),
)


def ensure_unicode_text_columns() -> None:
    """Converts older VARCHAR columns to NVARCHAR. Existing text is kept."""
    if db.engine.dialect.name != "mssql":
        return

    changed = False
    for table, column, definition in _UNICODE_COLUMNS:
        data_type = db.session.execute(
            text(
                "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = :table AND COLUMN_NAME = :column"
            ),
            {"table": table, "column": column},
        ).scalar()
        if data_type is None or data_type.lower() == "nvarchar":
            continue
        db.session.execute(text(f"ALTER TABLE {table} ALTER COLUMN {column} {definition}"))
        changed = True
    if changed:
        db.session.commit()
