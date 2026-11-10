from app.commands.close_ended_requests import CloseEndedRequests
from app.commands.create_volunteer_request import public_request
from app.errors import NotFoundError, ValidationError
from app.models.volunteer_request import STATUSES
from app.persistence.event_repository import EventRepository
from app.persistence.request_repository import RequestRepository
from app.persistence.user_repository import UserRepository


class ListMyRequests:
    def __init__(
        self,
        users: UserRepository | None = None,
        requests: RequestRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.requests = requests or RequestRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int, status: str | None = None) -> list[dict]:
        if status is not None:
            status = status.strip().upper() or None
        if status is not None and status not in STATUSES:
            raise ValidationError(f"status must be one of: {', '.join(STATUSES)}")

        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        # Statuses whose time has passed are updated before they are returned.
        CloseEndedRequests(self.requests, self.events).execute(user_id)

        names: dict[int, str] = {}

        def name_of(other_id: int) -> str:
            if other_id not in names:
                other = self.users.get_by_id(other_id)
                names[other_id] = other.name if other else ""
            return names[other_id]

        items = []
        for request in self.requests.list_for_user(user_id, status):
            item = public_request(request)
            item["my_role"] = "CLIENT" if request.client_id == user_id else "VOLUNTEER"
            item["client_name"] = name_of(request.client_id)
            item["volunteer_name"] = name_of(request.volunteer_id)
            items.append(item)
        return items
