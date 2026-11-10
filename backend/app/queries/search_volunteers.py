import math
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
EARTH_RADIUS_KM = 6371.0
DEFAULT_RADIUS_KM = 10.0
MIN_RADIUS_KM = 1.0
MAX_RADIUS_KM = 100.0


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
            if candidate.id == user.id:
                continue
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
        latitude_text = _optional_text(filters.get("latitude"))
        longitude_text = _optional_text(filters.get("longitude"))
        radius_text = _optional_text(filters.get("radius_km"))

        if category is not None and category not in ALLOWED_CATEGORIES:
            raise ValidationError(f"Unknown category: {category}")

        if (date_value is None) != (start_time is None):
            raise ValidationError("date and start_time must be sent together")

        weekday = None
        minutes = None
        if date_value is not None:
            weekday = _weekday_from_date(date_value)
            minutes = _minutes_from_time(start_time)

        if (latitude_text is None) != (longitude_text is None):
            raise ValidationError("latitude and longitude must be sent together")
        if radius_text is not None and latitude_text is None:
            raise ValidationError("radius_km requires latitude and longitude")

        origin = None
        radius_km = None
        if latitude_text is not None:
            latitude = _number(latitude_text, "latitude", -90, 90)
            longitude = _number(longitude_text, "longitude", -180, 180)
            origin = (latitude, longitude)
            radius_km = (
                _number(radius_text, "radius_km", MIN_RADIUS_KM, MAX_RADIUS_KM)
                if radius_text is not None
                else DEFAULT_RADIUS_KM
            )

        return {
            "category": category,
            "weekday": weekday,
            "minutes": minutes,
            "origin": origin,
            "radius_km": radius_km,
        }

    def _matches(self, candidate, categories, windows, parsed) -> bool:
        if parsed["category"] is not None and parsed["category"] not in categories:
            return False
        if parsed["origin"] is not None:
            if candidate.latitude is None or candidate.longitude is None:
                return False
            distance = distance_km(
                parsed["origin"], (candidate.latitude, candidate.longitude)
            )
            if distance > parsed["radius_km"]:
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


def distance_km(origin: tuple[float, float], target: tuple[float, float]) -> float:
    """Great-circle (haversine) distance between two lat/lng points."""
    lat1, lng1 = map(math.radians, origin)
    lat2, lng2 = map(math.radians, target)
    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _number(value: str, name: str, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise ValidationError(f"{name} must be a number") from error
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValidationError(f"{name} must be between {minimum:g} and {maximum:g}")
    return number


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


