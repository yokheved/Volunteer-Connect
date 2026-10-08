import json

import pytest

from app.commands.register_user import RegisterUser
from app.errors import ValidationError
from app.extensions import db
from app.models.domain_event import DomainEvent
from app.models.user import User
from app.persistence.event_repository import EventRepository


from tests.place_data import FIXTURE_PLACE

VALID_USER = {
    "name": "Example User",
    "email": "user@example.com",
    "password": "password",
    "phone": "0500000000",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}


def test_register_user_validates_input(app):
    with app.app_context():
        with pytest.raises(ValidationError):
            RegisterUser().execute({"email": "not-an-email"})


def test_register_user_persists_user(app):
    with app.app_context():
        user = RegisterUser().execute(VALID_USER)
        stored = db.session.get(User, user.id)

        assert stored is not None
        assert stored.email == "user@example.com"
        assert stored.password_hash != VALID_USER["password"]
        assert stored.is_client is True
        assert stored.is_volunteer is False
        assert stored.google_place_id == FIXTURE_PLACE["google_place_id"]
        assert stored.latitude == FIXTURE_PLACE["latitude"]
        assert stored.longitude == FIXTURE_PLACE["longitude"]
        assert stored.location_cached_at is not None


def test_register_user_writes_user_registered_event(app):
    with app.app_context():
        user = RegisterUser().execute(VALID_USER)
        events = EventRepository().list_by_aggregate("User", user.id)

        assert len(events) == 1
        event = events[0]
        assert isinstance(event, DomainEvent)
        assert event.event_type == "UserRegistered"
        payload = json.loads(event.event_data)
        assert payload["user_id"] == user.id
        assert payload["email"] == user.email
        assert payload["roles"] == ["CLIENT"]
        assert payload["google_place_id"] == FIXTURE_PLACE["google_place_id"]
        assert payload["latitude"] == FIXTURE_PLACE["latitude"]
        assert payload["longitude"] == FIXTURE_PLACE["longitude"]
        assert "password" not in payload
        assert "password_hash" not in payload
