from app.extensions import db


def flush() -> None:
    db.session.flush()


def commit() -> None:
    db.session.commit()


def rollback() -> None:
    db.session.rollback()
