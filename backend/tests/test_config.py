import pytest

from app.config import build_database_uri, _sql_port


def test_build_database_uri_requires_settings(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("sqlServerAddress", "")
    monkeypatch.setenv("loginName", "")
    monkeypatch.setenv("loginPassword", "")

    with pytest.raises(RuntimeError, match="Database configuration is missing"):
        build_database_uri()


def test_sql_port_defaults_to_1433(monkeypatch):
    monkeypatch.delenv("sqlServerPort", raising=False)
    monkeypatch.setenv("connectionString", "initial catalog=VolunteerConnect")

    assert _sql_port() == 1433


def test_sql_port_reads_environment(monkeypatch):
    monkeypatch.setenv("sqlServerPort", "14333")

    assert _sql_port() == 14333
