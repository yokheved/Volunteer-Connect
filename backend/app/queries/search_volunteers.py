import re
from datetime import datetime

from app.commands.update_volunteer_availability import TIME_PATTERN
from app.commands.update_volunteer_categories import ALLOWED_CATEGORIES
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.persistence.availability_repository import AvailabilityRepository
from app.persistence.category_repository import CategoryRepository
from app.persistence.user_repository import UserRepository
from app.services.availability_match import matches_availability, weekday_name

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SearchVolunteers:
    def __init__(
        self,
        users: UserRepository | None = None,
        categories: CategoryRepository | None = None,
        availability: AvailabilityRepository | None = None,
    ):
        self.users = users or UserRepository()
        self.categories = categories or CategoryRepository()
        self.availability = availability or AvailabilityRepository()

    def execute(self, user_id: int, filters: dict) -> dict:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if "CLIENT" not in user.roles():
            raise ForbiddenError("Client role is required")

        parsed = self._validate(filters or {})
        volunteers = []
        for candidate in self.users.list_volunteers():
            categories = self.categories.list_for_volunteer(candidate.id)
            windows = self.availability.list_for_volunteer(candidate.id)
            if not self._matches(candidate, categories, windows, parsed):
                continue
            volunteers.append(
                {
                    "id": candidate.id,
                    "name": candidate.name,
                    "address": public_address(candidate.address),
                    "categories": categories,
                    "about_me": candidate.about_me,
                    "availability": windows,
                }
            )
        return {"volunteers": volunteers}

    def _validate(self, filters: dict) -> dict:
        category = _optional_text(filters.get("category"))
        date_value = _optional_text(filters.get("date"))
        start_time = _optional_text(filters.get("start_time"))
        location = _optional_text(filters.get("location"))

        if category is not None and category not in ALLOWED_CATEGORIES:
            raise ValidationError(f"Unknown category: {category}")

        if (date_value is None) != (start_time is None):
            raise ValidationError("date and start_time must be sent together")

        weekday = None
        minutes = None
        if date_value is not None:
            weekday = _weekday_from_date(date_value)
            minutes = _minutes_from_time(start_time)

        return {
            "category": category,
            "weekday": weekday,
            "minutes": minutes,
            "location": location,
        }

    def _matches(self, candidate, categories, windows, parsed) -> bool:
        if parsed["category"] is not None and parsed["category"] not in categories:
            return False
        if parsed["location"] is not None:
            if parsed["location"].lower() not in public_address(candidate.address).lower():
                return False
        if parsed["weekday"] is not None:
            if not matches_availability(
                windows, parsed["weekday"], parsed["minutes"]
            ):
                return False
        return True


def public_address(address: str | None) -> str:
    parts = [part.strip() for part in (address or "").split(",") if part.strip()]
    if len(parts) >= 2:
        return ", ".join(parts[-2:])
    return parts[0] if parts else ""


def _optional_text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _weekday_from_date(value: str) -> str:
    if not DATE_PATTERN.fullmatch(value):
        raise ValidationError("date must be YYYY-MM-DD")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise ValidationError("date must be YYYY-MM-DD") from error
    return weekday_name(parsed.date())


def _minutes_from_time(value: str) -> int:
    if not TIME_PATTERN.fullmatch(value):
        raise ValidationError("start_time must be HH:MM on a 24-hour clock")
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


