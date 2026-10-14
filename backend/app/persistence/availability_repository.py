from datetime import time as dt_time

from app.extensions import db
from app.models.availability import Availability

DAY_ORDER = {
    "SUNDAY": 0,
    "MONDAY": 1,
    "TUESDAY": 2,
    "WEDNESDAY": 3,
    "THURSDAY": 4,
    "FRIDAY": 5,
    "SATURDAY": 6,
}


def format_hhmm(value: dt_time) -> str:
    return value.strftime("%H:%M")


class AvailabilityRepository:
    def list_for_volunteer(self, volunteer_id: int) -> list[dict]:
        rows = list(
            db.session.execute(
                db.select(Availability).where(
                    Availability.volunteer_id == volunteer_id
                )
            ).scalars()
        )
        rows.sort(
            key=lambda row: (
                DAY_ORDER.get(row.day_of_week, 99),
                row.start_time,
            )
        )
        return [
            {
                "day_of_week": row.day_of_week,
                "start_time": format_hhmm(row.start_time),
                "end_time": format_hhmm(row.end_time),
            }
            for row in rows
        ]

    def replace_for_volunteer(self, volunteer_id: int, windows: list[dict]) -> None:
        db.session.execute(
            db.delete(Availability).where(Availability.volunteer_id == volunteer_id)
        )
        for window in windows:
            db.session.add(
                Availability(
                    volunteer_id=volunteer_id,
                    day_of_week=window["day_of_week"],
                    start_time=window["start_time"],
                    end_time=window["end_time"],
                )
            )
