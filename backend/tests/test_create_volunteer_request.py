import json

from app.extensions import db
from app.models.domain_event import DomainEvent
from app.models.user import User
from app.models.volunteer_request import VolunteerRequest
from app.persistence.event_repository import EventRepository
from tests.place_data import FIXTURE_PLACE, OTHER_PLACE

CLIENT = {
    "name": "Request Client",
    "email": "request-client@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000201",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}

OTHER_CLIENT = {
    "name": "Other Client",
    "email": "other-request-client@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000202",
    "roles": ["CLIENT"],
    **OTHER_PLACE,
}

VOLUNTEER = {
    "name": "Request Volunteer",
    "email": "request-volunteer@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000203",
    "roles": ["VOLUNTEER"],
    **OTHER_PLACE,
}

VOLUNTEER_ONLY = {
    "name": "Volunteer Only Requester",
    "email": "volunteer-only-request@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000204",
    "roles": ["VOLUNTEER"],
    **FIXTURE_PLACE,
}

BOTH_ROLES = {
    "name": "Both Roles Requester",
    "email": "both-request@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000205",
    "roles": ["CLIENT", "VOLUNTEER"],
    **FIXTURE_PLACE,
}

VALID_DESCRIPTION = "Help with grocery shopping."
PRIVATE_FIELDS = ("email", "phone", "password", "password_hash")
THURSDAY_MORNING = [
    {"day_of_week": "THURSDAY", "start_time": "09:00", "end_time": "13:00"}
]


def _register(client, payload):
    return client.post("/api/auth/register", json=payload)


def _login(client, payload):
    return client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )


def _auth_header(client, payload):
    _register(client, payload)
    token = _login(client, payload).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user_id(app, email):
    with app.app_context():
        return (
            db.session.execute(db.select(User).where(User.email == email))
            .scalar_one()
            .id
        )


def _setup_volunteer(client, payload, categories, availability=None):
    headers = _auth_header(client, payload)
    client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": categories},
    )
    client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": availability if availability is not None else THURSDAY_MORNING},
    )
    return headers


def _valid_body(volunteer_id, **overrides):
    body = {
        "volunteer_id": volunteer_id,
        "category": "Shopping",
        "date": "2026-10-15",
        "start_time": "10:00",
        "duration": 2,
        "description": VALID_DESCRIPTION,
    }
    body.update(overrides)
    return body


def _create(client, headers, body):
    return client.post("/api/requests", headers=headers, json=body)


def _request_count(app):
    with app.app_context():
        return db.session.execute(
            db.select(db.func.count()).select_from(VolunteerRequest)
        ).scalar()


def _created_events(app, request_id=None):
    with app.app_context():
        query = db.select(DomainEvent).where(
            DomainEvent.event_type == "VolunteerRequestCreated"
        )
        if request_id is not None:
            query = query.where(DomainEvent.aggregate_id == request_id)
        return list(db.session.execute(query).scalars())


def test_client_creates_pending_request_with_copied_location(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping", "Elderly Assistance"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, CLIENT)
    client_id = _user_id(app, CLIENT["email"])

    with app.app_context():
        stored_client = db.session.get(User, client_id)
        cached_at = stored_client.location_cached_at

    response = _create(client, headers, _valid_body(volunteer_id))
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "PENDING"
    assert body["client_id"] == client_id
    assert body["volunteer_id"] == volunteer_id
    assert body["category"] == "Shopping"
    assert body["date"] == "2026-10-15"
    assert body["start_time"] == "10:00"
    assert body["duration"] == 2
    assert body["description"] == VALID_DESCRIPTION
    assert body["location"] == FIXTURE_PLACE["address"]
    assert body["google_place_id"] == FIXTURE_PLACE["google_place_id"]
    assert body["latitude"] == FIXTURE_PLACE["latitude"]
    assert body["longitude"] == FIXTURE_PLACE["longitude"]
    assert body["location_cached_at"] == cached_at.isoformat()
    assert "id" in body
    assert "created_at" in body
    for field in PRIVATE_FIELDS:
        assert field not in body

    with app.app_context():
        stored = db.session.get(VolunteerRequest, body["id"])
        assert stored is not None
        assert stored.status == "PENDING"
        assert stored.client_id == client_id
        assert stored.location == FIXTURE_PLACE["address"]
        assert stored.google_place_id == FIXTURE_PLACE["google_place_id"]
        assert stored.location_cached_at == cached_at
        events = EventRepository().list_by_aggregate("VolunteerRequest", body["id"])
        created = [event for event in events if event.event_type == "VolunteerRequestCreated"]
        assert len(created) == 1
        payload = json.loads(created[0].event_data)
        assert payload["request_id"] == body["id"]
        assert payload["client_id"] == client_id
        assert payload["volunteer_id"] == volunteer_id
        assert payload["status"] == "PENDING"
        assert payload["location"] == FIXTURE_PLACE["address"]
        assert payload["google_place_id"] == FIXTURE_PLACE["google_place_id"]


def test_both_roles_user_can_create_request_for_another_volunteer(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, BOTH_ROLES)

    response = _create(client, headers, _valid_body(volunteer_id))
    assert response.status_code == 201
    assert response.get_json()["status"] == "PENDING"


def test_volunteer_only_user_receives_403(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, VOLUNTEER_ONLY)

    response = _create(client, headers, _valid_body(volunteer_id))
    assert response.status_code == 403
    assert _request_count(app) == 0
    assert _created_events(app) == []


def test_missing_token_receives_401(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])

    response = _create(client, {}, _valid_body(volunteer_id))
    assert response.status_code == 401
    assert _request_count(app) == 0
    assert _created_events(app) == []


def test_unknown_volunteer_id_receives_404(client, app):
    headers = _auth_header(client, CLIENT)
    before = _request_count(app)

    response = _create(client, headers, _valid_body(99999))
    assert response.status_code == 404
    assert _request_count(app) == before
    assert _created_events(app) == []


def test_non_volunteer_user_receives_404(client, app):
    headers = _auth_header(client, CLIENT)
    _auth_header(client, OTHER_CLIENT)
    other_id = _user_id(app, OTHER_CLIENT["email"])

    response = _create(client, headers, _valid_body(other_id))
    assert response.status_code == 404
    assert _request_count(app) == 0
    assert _created_events(app) == []


def test_validation_failures_return_400_and_write_nothing(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, CLIENT)
    client_id = _user_id(app, CLIENT["email"])

    invalid_bodies = [
        _valid_body(volunteer_id, category="Tutoring"),
        _valid_body(volunteer_id, category="Not A Category"),
        _valid_body(volunteer_id, duration=0),
        _valid_body(volunteer_id, description="   "),
        _valid_body(client_id),
        _valid_body(volunteer_id, client_id=client_id),
        _valid_body(volunteer_id, status="APPROVED"),
        _valid_body(volunteer_id, location="Jerusalem"),
        _valid_body(volunteer_id, start_time="14:00"),
        _valid_body(volunteer_id, start_time="13:00"),
        _valid_body(volunteer_id, date="2026-10-16"),
    ]

    for body in invalid_bodies:
        before = _request_count(app)
        before_events = len(_created_events(app))
        response = _create(client, headers, body)
        assert response.status_code == 400, body
        assert _request_count(app) == before
        assert len(_created_events(app)) == before_events


def test_request_at_window_start_is_accepted(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, CLIENT)

    response = _create(client, headers, _valid_body(volunteer_id, start_time="09:00"))
    assert response.status_code == 201
    assert response.get_json()["start_time"] == "09:00"


def test_volunteer_with_no_availability_receives_400(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"], availability=[])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, CLIENT)

    response = _create(client, headers, _valid_body(volunteer_id))
    assert response.status_code == 400
    assert _request_count(app) == 0
    assert _created_events(app) == []


def test_client_without_saved_place_receives_400(client, app):
    _setup_volunteer(client, VOLUNTEER, ["Shopping"])
    volunteer_id = _user_id(app, VOLUNTEER["email"])
    headers = _auth_header(client, CLIENT)
    client_id = _user_id(app, CLIENT["email"])

    with app.app_context():
        stored = db.session.get(User, client_id)
        stored.google_place_id = None
        stored.latitude = None
        stored.longitude = None
        stored.location_cached_at = None
        db.session.commit()

    response = _create(client, headers, _valid_body(volunteer_id))
    assert response.status_code == 400
    assert _request_count(app) == 0
    assert _created_events(app) == []
