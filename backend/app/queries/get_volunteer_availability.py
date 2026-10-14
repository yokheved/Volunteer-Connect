from app.errors import ForbiddenError, NotFoundError
from app.persistence.availability_repository import AvailabilityRepository
from app.persistence.user_repository import UserRepository


class GetVolunteerAvailability:
    def __init__(
        self,
        users: UserRepository | None = None,
        availability: AvailabilityRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.availability = availability or AvailabilityRepository()

    def execute(self, user_id: int) -> dict:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if "VOLUNTEER" not in user.roles():
            raise ForbiddenError("Volunteer role is required")

        return {"availability": self.availability.list_for_volunteer(user.id)}
