import json
import re
from datetime import datetime, time as dt_time

from marshmallow import (
    RAISE,
    Schema,
    ValidationError as MarshmallowValidationError,
    fields,
    pre_load,
    validate,
)

from app.commands.register_user import format_schema_errors
from app.commands.update_volunteer_availability import TIME_PATTERN
from app.commands.update_volunteer_categories import ALLOWED_CATEGORIES
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.domain_event import DomainEvent
from app.models.volunteer_request import PENDING, VolunteerRequest
from app.persistence.availability_repository import AvailabilityRepository
from app.persistence.category_repository import CategoryRepository
from app.persistence.event_repository import EventRepository
from app.persistence.request_repository import RequestRepository
from app.persistence.session import commit, flush, rollback
from app.persistence.user_repository import UserRepository
from app.services.availability_match import matches_availability, weekday_name

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOCATION_BODY_FIELDS = ("location", "google_place_id", "latitude", "longitude")


class CreateVolunteerRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    volunteer_id = fields.Integer(required=True)
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    date = fields.Str(required=True)
    start_time = fields.Str(required=True)
    duration = fields.Integer(required=True, validate=validate.Range(min=1))
    description = fields.Str(required=True, validate=validate.Length(min=1, max=2000))

    @pre_load
    def strip_text_fields(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        stripped = dict(data)
        for key in ("category", "date", "start_time", "description"):
            value = stripped.get(key)
            if isinstance(value, str):
                stripped[key] = value.strip()
        return stripped


class CreateVolunteerRequest:
    def __init__(
        self,
        users: UserRepository | None = None,
        categories: CategoryRepository | None = None,
        availability: AvailabilityRepository | None = None,
        requests: RequestRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.categories = categories or CategoryRepository()
        self.availability = availability or AvailabilityRepository()
        self.requests = requests or RequestRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int, data: dict) -> dict:
        client = self.users.get_by_id(user_id)
        if client is None:
            raise NotFoundError("User not found")
        if "CLIENT" not in client.roles():
            raise ForbiddenError("Client role is required")

        payload = self._validate(data)
        if payload["volunteer_id"] == client.id:
            raise ValidationError("You cannot create a request for yourself")

        volunteer = self.users.get_by_id(payload["volunteer_id"])
        if volunteer is None or "VOLUNTEER" not in volunteer.roles():
            raise NotFoundError("Volunteer not found")

        saved_categories = self.categories.list_for_volunteer(volunteer.id)
        if payload["category"] not in saved_categories:
            raise ValidationError("The volunteer does not offer that category")

        windows = self.availability.list_for_volunteer(volunteer.id)
        minutes = payload["start_time"].hour * 60 + payload["start_time"].minute
        if not matches_availability(windows, weekday_name(payload["date"]), minutes):
            raise ValidationError(
                "The volunteer is not available at that date and start time"
            )

        if (
            not client.google_place_id
            or client.latitude is None
            or client.longitude is None
            or client.location_cached_at is None
        ):
            raise ValidationError("Set your profile address before creating a request")

        request = VolunteerRequest(
            client_id=client.id,
            volunteer_id=volunteer.id,
            category=payload["category"],
            date=payload["date"],
            start_time=payload["start_time"],
            duration=payload["duration"],
            location=client.address,
            google_place_id=client.google_place_id,
            latitude=client.latitude,
            longitude=client.longitude,
            location_cached_at=client.location_cached_at,
            description=payload["description"],
            status=PENDING,
        )

        try:
            self.requests.add(request)
            flush()
            self.events.add(
                DomainEvent(
                    aggregate_type="VolunteerRequest",
                    aggregate_id=request.id,
                    event_type="VolunteerRequestCreated",
                    event_data=json.dumps(
                        {
                            "request_id": request.id,
                            "client_id": request.client_id,
                            "volunteer_id": request.volunteer_id,
                            "category": request.category,
                            "date": request.date.isoformat(),
                            "start_time": _hhmm(request.start_time),
                            "duration": request.duration,
                            "location": request.location,
                            "google_place_id": request.google_place_id,
                            "status": request.status,
                        }
                    ),
                )
            )
            body = public_request(request)
            commit()
        except Exception:
            rollback()
            raise

        return body

    def _validate(self, data: dict) -> dict:
        raw = data if isinstance(data, dict) else {}
        if "client_id" in raw or "status" in raw:
            raise ValidationError("client_id and status cannot be sent in the request body")
        for field in LOCATION_BODY_FIELDS:
            if field in raw:
                raise ValidationError(
                    "location is copied from your saved profile and cannot be sent"
                )

        try:
            payload = CreateVolunteerRequestSchema().load(raw)
        except MarshmallowValidationError as error:
            raise ValidationError(format_schema_errors(error.messages)) from error

        category = payload["category"]
        if category not in ALLOWED_CATEGORIES:
            raise ValidationError(f"Unknown category: {category}")

        date_value = payload["date"]
        if not DATE_PATTERN.fullmatch(date_value):
            raise ValidationError("date must be YYYY-MM-DD")
        try:
            parsed_date = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError as error:
            raise ValidationError("date must be YYYY-MM-DD") from error

        start_time = payload["start_time"]
        if not TIME_PATTERN.fullmatch(start_time):
            raise ValidationError("start_time must be HH:MM on a 24-hour clock")
        hour, minute = start_time.split(":")

        return {
            "volunteer_id": payload["volunteer_id"],
            "category": category,
            "date": parsed_date,
            "start_time": dt_time(int(hour), int(minute)),
            "duration": payload["duration"],
            "description": payload["description"],
        }


def public_request(request: VolunteerRequest) -> dict:
    return {
        "id": request.id,
        "client_id": request.client_id,
        "volunteer_id": request.volunteer_id,
        "category": request.category,
        "date": request.date.isoformat(),
        "start_time": _hhmm(request.start_time),
        "duration": request.duration,
        "location": request.location,
        "google_place_id": request.google_place_id,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "location_cached_at": request.location_cached_at.isoformat(),
        "description": request.description,
        "status": request.status,
        "created_at": request.created_at.isoformat(),
    }


def _hhmm(value: dt_time) -> str:
    return value.strftime("%H:%M")
