from datetime import datetime, timezone

from app.extensions import db


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    is_client = db.Column(db.Boolean, nullable=False, default=False)
    is_volunteer = db.Column(db.Boolean, nullable=False, default=False)
    monthly_hours_goal = db.Column(db.Integer, nullable=True)
    about_me = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utc_now)

    def roles(self) -> list[str]:
        assigned: list[str] = []
        if self.is_client:
            assigned.append("CLIENT")
        if self.is_volunteer:
            assigned.append("VOLUNTEER")
        return assigned
