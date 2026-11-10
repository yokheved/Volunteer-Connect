from app.commands.close_ended_requests import CloseEndedRequests, status_event
from app.commands.create_volunteer_request import public_request
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.volunteer_request import APPROVED, PENDING, REJECTED, VolunteerRequest
from app.persistence.event_repository import EventRepository
from app.persistence.request_repository import RequestRepository
from app.persistence.session import commit, rollback
from app.persistence.user_repository import UserRepository
from app.services.request_time import overlaps


class _VolunteerDecision:
    """Shared flow for a volunteer's answer to a PENDING request."""

    to_status: str = ""

    def __init__(
        self,
        users: UserRepository | None = None,
        requests: RequestRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.requests = requests or RequestRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int, request_id: int) -> dict:
        volunteer = self.users.get_by_id(user_id)
        if volunteer is None:
            raise NotFoundError("User not found")
        if "VOLUNTEER" not in volunteer.roles():
            raise ForbiddenError("Volunteer role is required")

        # A request whose time has passed is closed first, so it cannot be approved.
        CloseEndedRequests(self.requests, self.events).execute(user_id)

        request = self.requests.get_by_id(request_id)
        if request is None or request.volunteer_id != volunteer.id:
            raise NotFoundError("Request not found")
        if request.status != PENDING:
            raise ConflictError(f"Request is already {request.status}")

        self.check(request)

        try:
            if not self.requests.transition_status(request.id, PENDING, self.to_status):
                raise ConflictError("Request was changed by another action")
            self.events.add(status_event(request, PENDING, self.to_status, volunteer.id))
            commit()
        except Exception:
            rollback()
            raise

        # commit() expires the object, so this reads the saved status.
        return public_request(request)

    def check(self, request: VolunteerRequest) -> None:
        pass


class ApproveVolunteerRequest(_VolunteerDecision):
    to_status = APPROVED

    def check(self, request: VolunteerRequest) -> None:
        approved = self.requests.list_approved_for_volunteer_on(
            request.volunteer_id, request.date
        )
        if any(other.id != request.id and overlaps(request, other) for other in approved):
            raise ConflictError(
                "You already have an approved activity that overlaps this time"
            )


class RejectVolunteerRequest(_VolunteerDecision):
    to_status = REJECTED
