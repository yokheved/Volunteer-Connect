import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _catalog_from_connection_string(connection_string: str) -> str:
    for part in connection_string.split(";"):
        if part.lower().startswith("initial catalog="):
            return part.split("=", 1)[1]
    return "VolunteerConnect"


def _port_from_connection_string(connection_string: str) -> int | None:
    for part in connection_string.split(";"):
        key, _, value = part.partition("=")
        normalized_key = key.strip().lower()
        if normalized_key not in {"data source", "server"}:
            continue
        host = value.strip()
        if "," in host:
            maybe_port = host.rsplit(",", 1)[1].strip()
            if maybe_port.isdigit():
                return int(maybe_port)
        if ":" in host and "\\" not in host:
            maybe_port = host.rsplit(":", 1)[1].strip()
            if maybe_port.isdigit():
                return int(maybe_port)
    return None


def _sql_port() -> int:
    explicit = os.getenv("sqlServerPort", "").strip()
    if explicit:
        return int(explicit)
    from_connection_string = _port_from_connection_string(
        os.getenv("connectionString", "")
    )
    if from_connection_string is not None:
        return from_connection_string
    return 1433


def _odbc_driver() -> str:
    try:
        import pyodbc
    except ImportError:
        return "ODBC Driver 18 for SQL Server"

    preferred = (
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    )
    available = pyodbc.drivers()
    for driver in preferred:
        if driver in available:
            return driver
    return preferred[0]


def build_database_uri() -> str:
    explicit_uri = os.getenv("DATABASE_URL")
    if explicit_uri:
        return explicit_uri

    host = os.getenv("sqlServerAddress", "").strip()
    username = os.getenv("loginName", "").strip()
    password = os.getenv("loginPassword", "")
    catalog = _catalog_from_connection_string(os.getenv("connectionString", ""))
    if not host or not username or not password:
        raise RuntimeError(
            "Database configuration is missing. Set DATABASE_URL or "
            "sqlServerAddress, loginName, and loginPassword."
        )

    driver = quote_plus(_odbc_driver())
    port = _sql_port()
    return (
        f"mssql+pyodbc://{quote_plus(username)}:{quote_plus(password)}"
        f"@{host}:{port}/{catalog}"
        f"?driver={driver}&TrustServerCertificate=yes&Encrypt=yes"
    )


class Config:
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_BLOCKLIST_ENABLED = True
    JWT_BLOCKLIST_TOKEN_CHECKS = ["access"]
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
