from app.extensions import db


class VolunteerCategory(db.Model):
    __tablename__ = "volunteer_categories"

    volunteer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        primary_key=True,
        nullable=False,
    )
    category = db.Column(db.String(100), primary_key=True, nullable=False)
