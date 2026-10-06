from app.extensions import db
from app.models.domain_event import DomainEvent


class EventRepository:
    def add(self, event: DomainEvent) -> None:
        db.session.add(event)

    def list_by_aggregate(self, aggregate_type: str, aggregate_id: int) -> list[DomainEvent]:
        return list(
            db.session.execute(
                db.select(DomainEvent)
                .where(
                    DomainEvent.aggregate_type == aggregate_type,
                    DomainEvent.aggregate_id == aggregate_id,
                )
                .order_by(DomainEvent.id)
            ).scalars()
        )
