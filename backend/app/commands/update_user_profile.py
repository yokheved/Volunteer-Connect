import json

from marshmallow import (
    RAISE,
    Schema,
    ValidationError as MarshmallowValidationError,
    fields,
    missing as marshmallow_missing,
    pre_load,
    validate,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.commands.location import LocationFieldsSchema
from app.commands.register_user import format_schema_errors, normalize_roles
from app.errors import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.models.domain_event import DomainEvent
from app.models.user import User, utc_now
from app.persistence.event_repository import EventRepository
from app.persistence.session import commit, flush, rollback
from app.persistence.user_repository import UserRepository
from app.queries.get_user_profile import GetUserProfile

VOLUNTEER_FIELDS = ("about_me", "monthly_hours_goal")


class UpdateUserProfileSchema(LocationFieldsSchema):
    class Meta:
        unknown = RAISE

    current_password = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    phone = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    roles = fields.List(fields.Str(), required=True)
    new_password = fields.Str(load_default=marshmallow_missing)
    confirm_password = fields.Str(load_default=marshmallow_missing)
    about_me = fields.Str(load_default=marshmallow_missing, allow_none=True)
    monthly_hours_goal = fields.Integer(
        load_default=marshmallow_missing,
        allow_none=True,
        validate=validate.Range(min=1),
    )

    @pre_load
    def strip_text_fields(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        stripped = dict(data)
        for key in (
            "name",
            "phone",
            "address",
            "google_place_id",
            "current_password",
            "new_password",
            "confirm_password",
            "about_me",
        ):
            value = stripped.get(key)
            if isinstance(value, str):
                stripped[key] = value.strip()
        return stripped


class UpdateUserProfile:
    def __init__(
        self,
        users: UserRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int, data: dict) -> dict:
        raw = data if isinstance(data, dict) else {}
        if "email" in raw:
            raise ValidationError("email cannot be updated on this endpoint")

        payload = self._validate(raw)
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        if not check_password_hash(user.password_hash, payload["current_password"]):
            raise UnauthorizedError("Current password is incorrect")

        roles = normalize_roles(payload["roles"])
        sent_volunteer_fields = [field for field in VOLUNTEER_FIELDS if field in raw]
        if sent_volunteer_fields and "VOLUNTEER" not in roles:
            raise ForbiddenError(
                "Only volunteers can update about_me and monthly_hours_goal"
            )

        password_changed = self._apply_password_change(user, raw, payload)

        place_changed = user.google_place_id != payload["google_place_id"]

        user.name = payload["name"]
        user.phone = payload["phone"]
        user.address = payload["address"]
        user.google_place_id = payload["google_place_id"]
        user.latitude = payload["latitude"]
        user.longitude = payload["longitude"]
        if place_changed:
            user.location_cached_at = utc_now()
        user.is_client = "CLIENT" in roles
        user.is_volunteer = "VOLUNTEER" in roles

        written = {
            "name": user.name,
            "phone": user.phone,
            "address": user.address,
            "google_place_id": user.google_place_id,
            "roles": user.roles(),
            "latitude": user.latitude,
            "longitude": user.longitude,
            "password_changed": password_changed,
        }

        if "about_me" in raw:
            about_me = payload.get("about_me")
            user.about_me = None if about_me in (None, "", marshmallow_missing) else about_me
            written["about_me"] = user.about_me

        if "monthly_hours_goal" in raw:
            goal = payload["monthly_hours_goal"]
            user.monthly_hours_goal = None if goal is None else goal
            written["monthly_hours_goal"] = user.monthly_hours_goal

        try:
            flush()
            self.events.add(
                DomainEvent(
                    aggregate_type="User",
                    aggregate_id=user.id,
                    event_type="UserProfileUpdated",
                    event_data=json.dumps({"user_id": user.id, **written}),
                )
            )
            commit()
        except Exception:
            rollback()
            raise

        return GetUserProfile(users=self.users).execute(user.id)

    def _validate(self, data: dict) -> dict:
        has_new = "new_password" in data
        has_confirm = "confirm_password" in data
        if has_new != has_confirm:
            raise ValidationError("new_password and confirm_password are both required")
        try:
            payload = UpdateUserProfileSchema().load(data)
        except MarshmallowValidationError as error:
            raise ValidationError(format_schema_errors(error.messages)) from error
        return payload

    def _apply_password_change(self, user: User, raw: dict, payload: dict) -> bool:
        if "new_password" not in raw and "confirm_password" not in raw:
            return False

        new_password = payload.get("new_password")
        confirm_password = payload.get("confirm_password")
        if not new_password or not confirm_password:
            raise ValidationError("new_password and confirm_password are both required")
        if len(new_password) < 8:
            raise ValidationError("new_password must be at least 8 characters")
        if new_password != confirm_password:
            raise ValidationError("new_password and confirm_password must match")

        user.password_hash = generate_password_hash(new_password)
        return True
