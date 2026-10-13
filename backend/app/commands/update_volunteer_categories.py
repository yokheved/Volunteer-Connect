import json

from marshmallow import Schema, ValidationError as MarshmallowValidationError, fields

from app.commands.register_user import format_schema_errors
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.domain_event import DomainEvent
from app.persistence.category_repository import CategoryRepository
from app.persistence.event_repository import EventRepository
from app.persistence.session import commit, flush, rollback
from app.persistence.user_repository import UserRepository

ALLOWED_CATEGORIES = (
    "Elderly Assistance",
    "Transportation",
    "Shopping",
    "Tutoring",
    "Technical Help",
    "Childcare Support",
    "Cooking",
    "Cleaning",
)


class UpdateVolunteerCategoriesSchema(Schema):
    categories = fields.List(fields.Str(), required=True)


class UpdateVolunteerCategories:
    def __init__(
        self,
        users: UserRepository | None = None,
        categories: CategoryRepository | None = None,
        events: EventRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.categories = categories or CategoryRepository()
        self.events = events or EventRepository()

    def execute(self, user_id: int, data: dict) -> dict:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if "VOLUNTEER" not in user.roles():
            raise ForbiddenError("Volunteer role is required")

        selected = self._validate(data)
        try:
            self.categories.replace_for_volunteer(user.id, selected)
            flush()
            self.events.add(
                DomainEvent(
                    aggregate_type="User",
                    aggregate_id=user.id,
                    event_type="VolunteerCategoriesUpdated",
                    event_data=json.dumps(
                        {
                            "volunteer_id": user.id,
                            "categories": selected,
                        }
                    ),
                )
            )
            commit()
        except Exception:
            rollback()
            raise

        return {"categories": self.categories.list_for_volunteer(user.id)}

    def _validate(self, data: dict) -> list[str]:
        try:
            payload = UpdateVolunteerCategoriesSchema().load(data or {})
        except MarshmallowValidationError as error:
            raise ValidationError(format_schema_errors(error.messages)) from error

        selected = []
        for value in payload["categories"]:
            category = value.strip() if isinstance(value, str) else ""
            if not category:
                raise ValidationError("categories cannot include a blank value")
            if category not in ALLOWED_CATEGORIES:
                raise ValidationError(f"Unknown category: {category}")
            if category in selected:
                raise ValidationError("categories cannot include duplicates")
            selected.append(category)
        return selected
