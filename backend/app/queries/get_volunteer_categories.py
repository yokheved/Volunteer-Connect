from app.errors import ForbiddenError, NotFoundError
from app.persistence.category_repository import CategoryRepository
from app.persistence.user_repository import UserRepository


class GetVolunteerCategories:
    def __init__(
        self,
        users: UserRepository | None = None,
        categories: CategoryRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.categories = categories or CategoryRepository()

    def execute(self, user_id: int) -> dict:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if "VOLUNTEER" not in user.roles():
            raise ForbiddenError("Volunteer role is required")

        return {"categories": self.categories.list_for_volunteer(user.id)}
