from app.extensions import db
from app.models.volunteer_category import VolunteerCategory


class CategoryRepository:
    def list_for_volunteer(self, volunteer_id: int) -> list[str]:
        return list(
            db.session.execute(
                db.select(VolunteerCategory.category)
                .where(VolunteerCategory.volunteer_id == volunteer_id)
                .order_by(VolunteerCategory.category)
            ).scalars()
        )

    def replace_for_volunteer(self, volunteer_id: int, categories: list[str]) -> None:
        db.session.execute(
            db.delete(VolunteerCategory).where(
                VolunteerCategory.volunteer_id == volunteer_id
            )
        )
        for category in categories:
            db.session.add(
                VolunteerCategory(volunteer_id=volunteer_id, category=category)
            )
