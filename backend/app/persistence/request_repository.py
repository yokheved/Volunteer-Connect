from datetime import date

from app.extensions import db
from app.models.volunteer_request import APPROVED, VolunteerRequest


class RequestRepository:
    def add(self, request: VolunteerRequest) -> None:
        db.session.add(request)

    def get_by_id(self, request_id: int) -> VolunteerRequest | None:
        return db.session.get(VolunteerRequest, request_id)

    def list_for_user(
        self, user_id: int, status: str | None = None
    ) -> list[VolunteerRequest]:
        query = db.select(VolunteerRequest).where(
            db.or_(
                VolunteerRequest.client_id == user_id,
                VolunteerRequest.volunteer_id == user_id,
            )
        )
        if status is not None:
            query = query.where(VolunteerRequest.status == status)
        query = query.order_by(
            VolunteerRequest.date, VolunteerRequest.start_time, VolunteerRequest.id
        )
        return list(db.session.execute(query).scalars())

    def list_approved_for_volunteer_on(
        self, volunteer_id: int, day: date
    ) -> list[VolunteerRequest]:
        return list(
            db.session.execute(
                db.select(VolunteerRequest).where(
                    VolunteerRequest.volunteer_id == volunteer_id,
                    VolunteerRequest.date == day,
                    VolunteerRequest.status == APPROVED,
                )
            ).scalars()
        )

    def transition_status(
        self, request_id: int, from_status: str, to_status: str
    ) -> bool:
        """Change the status only if it is still from_status. Does not commit."""
        result = db.session.execute(
            db.update(VolunteerRequest)
            .where(
                VolunteerRequest.id == request_id,
                VolunteerRequest.status == from_status,
            )
            .values(status=to_status)
            .execution_options(synchronize_session=False)
        )
        return result.rowcount == 1
