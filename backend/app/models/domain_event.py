from datetime import datetime, timezone

from app.extensions import db


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DomainEvent(db.Model):
    __tablename__ = "domain_events"

    id = db.Column(db.Integer, primary_key=True)
    aggregate_type = db.Column(db.String(100), nullable=False)
    aggregate_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    event_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utc_now)
