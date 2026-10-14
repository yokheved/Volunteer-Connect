import json
import re
from datetime import time as dt_time

from marshmallow import Schema, ValidationError as MarshmallowValidationError, fields

from app.commands.register_user import format_schema_errors
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.domain_event import DomainEvent
from app.persistence.availability_repository import AvailabilityRepository
from app.persistence.event_repository import EventRepository
from app.persistence.session import commit, flush, rollback
from app.persistence.user_repository import UserRepository

ALLOWED_DAYS = (
    "SUNDAY",
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
)
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class AvailabilityWindowSchema(Schema):
    day_of_week = fields.Str(required=True)
    start_time = fields.Str(required=True)
    end_time = fields.Str(required=True)


class UpdateVolunteerAvailabilitySchema(Schema):
    availability = fields.List(fields.Nested(AvailabilityWindowSchema), required=True)


class UpdateVolunteerAvailability:
    def __init__(
        self,
        users: UserRepository | None = None,
        availability: AvailabilityRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.availability = availability or AvailabilityRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int, data: dict) -> dict:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if "VOLUNTEER" not in user.roles():
            raise ForbiddenError("Volunteer role is required")

        windows, stored = self._validate(data)
        try:
            self.availability.replace_for_volunteer(user.id, stored)
            flush()
            self.events.add(
                DomainEvent(
                    aggregate_type="User",
                    aggregate_id=user.id,
                    event_type="VolunteerAvailabilityUpdated",
                    event_data=json.dumps(
                        {
                            "volunteer_id": user.id,
                            "availability": windows,
                        }
                    ),
                )
            )
            commit()
        except Exception:
            rollback()
            raise

        return {"availability": self.availability.list_for_volunteer(user.id)}

    def _validate(self, data: dict) -> tuple[list[dict], list[dict]]:
        try:
            payload = UpdateVolunteerAvailabilitySchema().load(data or {})
        except MarshmallowValidationError as error:
            raise ValidationError(format_schema_errors(error.messages)) from error

        windows = []
        stored = []
        for raw in payload["availability"]:
            day = raw["day_of_week"].strip().upper()
            start = raw["start_time"].strip()
            end = raw["end_time"].strip()
            if day not in ALLOWED_DAYS:
                raise ValidationError(f"Unknown day_of_week: {raw['day_of_week']}")
            if not TIME_PATTERN.fullmatch(start):
                raise ValidationError("start_time must be HH:MM on a 24-hour clock")
            if not TIME_PATTERN.fullmatch(end):
                raise ValidationError("end_time must be HH:MM on a 24-hour clock")
            start_minutes = _to_minutes(start)
            end_minutes = _to_minutes(end)
            if end_minutes <= start_minutes:
                raise ValidationError("end_time must be later than start_time")
            windows.append(
                {
                    "day_of_week": day,
                    "start_time": start,
                    "end_time": end,
                }
            )
            stored.append(
                {
                    "day_of_week": day,
                    "start_time": _to_time(start),
                    "end_time": _to_time(end),
                }
            )

        _reject_overlaps(windows)
        return windows, stored


def _to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _to_time(value: str) -> dt_time:
    hour, minute = value.split(":")
    return dt_time(int(hour), int(minute))


def _reject_overlaps(windows: list[dict]) -> None:
    by_day: dict[str, list[tuple[int, int]]] = {}
    for window in windows:
        start = _to_minutes(window["start_time"])
        end = _to_minutes(window["end_time"])
        existing = by_day.setdefault(window["day_of_week"], [])
        for other_start, other_end in existing:
            if start < other_end and other_start < end:
                raise ValidationError("availability windows cannot overlap")
        existing.append((start, end))
