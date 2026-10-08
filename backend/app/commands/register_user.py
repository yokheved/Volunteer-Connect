import json

from marshmallow import Schema, ValidationError as MarshmallowValidationError, fields, pre_load, validate
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app.commands.location import LocationFieldsSchema
from app.errors import ConflictError, ValidationError
from app.models.domain_event import DomainEvent
from app.models.user import User, utc_now
from app.persistence.event_repository import EventRepository
from app.persistence.session import commit, flush, rollback
from app.persistence.user_repository import UserRepository

ALLOWED_ROLES = {"CLIENT", "VOLUNTEER"}


class RegisterUserSchema(LocationFieldsSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8, max=255))
    phone = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    roles = fields.List(fields.Str(), required=True)

    @pre_load
    def strip_text_fields(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        stripped = dict(data)
        for key in ("name", "email", "password", "phone", "address", "google_place_id"):
            value = stripped.get(key)
            if isinstance(value, str):
                stripped[key] = value.strip()
        return stripped


class RegisterUser:
    def __init__(
        self,
        users: UserRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.events = events or EventRepository()

    def execute(self, data: dict) -> User:
        payload = self._validate(data)
        email = payload["email"].strip().lower()
        roles = normalize_roles(payload["roles"])

        if self.users.get_by_email(email) is not None:
            raise ConflictError("Email is already registered")

        user = User(
            name=payload["name"].strip(),
            email=email,
            password_hash=generate_password_hash(payload["password"]),
            phone=payload["phone"].strip(),
            address=payload["address"].strip(),
            google_place_id=payload["google_place_id"],
            latitude=payload["latitude"],
            longitude=payload["longitude"],
            location_cached_at=utc_now(),
            is_client="CLIENT" in roles,
            is_volunteer="VOLUNTEER" in roles,
        )

        try:
            self.users.add(user)
            flush()
            self.events.add(
                DomainEvent(
                    aggregate_type="User",
                    aggregate_id=user.id,
                    event_type="UserRegistered",
                    event_data=json.dumps(
                        {
                            "user_id": user.id,
                            "email": user.email,
                            "name": user.name,
                            "roles": user.roles(),
                            "address": user.address,
                            "google_place_id": user.google_place_id,
                            "latitude": user.latitude,
                            "longitude": user.longitude,
                        }
                    ),
                )
            )
            commit()
        except IntegrityError as error:
            rollback()
            raise ConflictError("Email is already registered") from error
        except Exception:
            rollback()
            raise

        return user

    def _validate(self, data: dict) -> dict:
        try:
            return RegisterUserSchema().load(data)
        except MarshmallowValidationError as error:
            raise ValidationError(format_schema_errors(error.messages)) from error


def normalize_roles(roles: list[str]) -> list[str]:
    if not roles:
        raise ValidationError("roles must include CLIENT and/or VOLUNTEER")

    unique_roles = []
    for role in roles:
        normalized = role.strip().upper()
        if normalized not in ALLOWED_ROLES:
            raise ValidationError("roles must include CLIENT and/or VOLUNTEER")
        if normalized not in unique_roles:
            unique_roles.append(normalized)

    if not unique_roles:
        raise ValidationError("roles must include CLIENT and/or VOLUNTEER")
    return unique_roles


def format_schema_errors(messages) -> str:
    if isinstance(messages, dict):
        parts = []
        for field, errors in messages.items():
            text = "; ".join(errors) if isinstance(errors, list) else str(errors)
            parts.append(f"{field}: {text}")
        return "; ".join(parts)
    return str(messages)
