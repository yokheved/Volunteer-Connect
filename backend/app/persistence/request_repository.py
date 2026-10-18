from app.extensions import db
from app.models.volunteer_request import VolunteerRequest


class RequestRepository:
    def add(self, request: VolunteerRequest) -> None:
        db.session.add(request)
