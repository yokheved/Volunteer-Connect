from app.extensions import db
from app.models.user import User


class UserRepository:
    def add(self, user: User) -> None:
        db.session.add(user)

    def get_by_id(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return db.session.execute(
            db.select(User).where(User.email == email.lower())
        ).scalar_one_or_none()

    def list_volunteers(self) -> list[User]:
        return list(
            db.session.execute(
                db.select(User)
                .where(User.is_volunteer.is_(True))
                .order_by(User.name, User.id)
            ).scalars()
        )
