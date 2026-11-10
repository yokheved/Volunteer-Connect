import json

from app.models.domain_event import DomainEvent
from app.models.volunteer_request import (
    APPROVED,
    COMPLETED,
    PENDING,
    REJECTED,
    VolunteerRequest,
)
from app.persistence.event_repository import EventRepository
from app.persistence.request_repository import RequestRepository
from app.persistence.session import commit, rollback
from app.services import request_time

STATUS_EVENTS = {
    APPROVED: "VolunteerRequestApproved",
    REJECTED: "VolunteerRequestRejected",
    COMPLETED: "VolunteerRequestCompleted",
}

SYSTEM = "SYSTEM"
EXPIRED = "EXPIRED"


def status_event(
    request: VolunteerRequest,
    previous_status: str,
    status: str,
    acted_by,
    reason: str | None = None,
) -> DomainEvent:
    data = {
        "request_id": request.id,
        "client_id": request.client_id,
        "volunteer_id": request.volunteer_id,
        "previous_status": previous_status,
        "status": status,
        "acted_by": acted_by,
    }
    if reason is not None:
        data["reason"] = reason
    return DomainEvent(
        aggregate_type="VolunteerRequest",
        aggregate_id=request.id,
        event_type=STATUS_EVENTS[status],
        event_data=json.dumps(data),
    )


class CloseEndedRequests:
    """Closes the user's requests whose time has passed.

    APPROVED and ended  -> COMPLETED
    PENDING and started -> REJECTED (expired, the volunteer never answered)
    """

    def __init__(
        self,
        requests: RequestRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.requests = requests or RequestRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int) -> int:
        current = request_time.now()
        changes = []
        for request in self.requests.list_for_user(user_id):
            if request.status == APPROVED and request_time.activity_end(request) <= current:
                changes.append((request, APPROVED, COMPLETED, None))
            elif request.status == PENDING and request_time.activity_start(request) <= current:
                changes.append((request, PENDING, REJECTED, EXPIRED))

        if not changes:
            return 0

        closed = 0
        try:
            for request, from_status, to_status, reason in changes:
                # Skip a request that another call already changed.
                if self.requests.transition_status(request.id, from_status, to_status):
                    self.events.add(
                        status_event(request, from_status, to_status, SYSTEM, reason)
                    )
                    closed += 1
            commit()
        except Exception:
            rollback()
            raise
        return closed
