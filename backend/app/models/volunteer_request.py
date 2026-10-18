from datetime import datetime, timezone

from app.extensions import db

PENDING = "PENDING"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VolunteerRequest(db.Model):
    __tablename__ = "volunteer_requests"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(500), nullable=False)
    google_place_id = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_cached_at = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
