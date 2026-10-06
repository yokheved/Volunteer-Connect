from app.errors import NotFoundError
from app.persistence.user_repository import UserRepository


class GetUserProfile:
    def __init__(self, users: UserRepository | None = None):
        self.users = users or UserRepository()

    def execute(self, user_id: int) -> dict:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "roles": user.roles(),
            "monthly_hours_goal": user.monthly_hours_goal,
            "about_me": user.about_me,
        }
