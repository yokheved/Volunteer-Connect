import json

from app.extensions import db
from app.models.user import User
from app.persistence.event_repository import EventRepository
from tests.place_data import FIXTURE_PLACE, OTHER_PLACE


CLIENT = {
    "name": "Client User",
    "email": "client@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000001",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}

VOLUNTEER = {
    "name": "Volunteer User",
    "email": "volunteer@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000002",
    "roles": ["VOLUNTEER"],
    **FIXTURE_PLACE,
}


def _register(client, payload):
    return client.post("/api/auth/register", json=payload)


def _login(client, payload, password=None):
    return client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": password or payload["password"]},
    )


def _auth_header(client, payload):
    _register(client, payload)
    token = _login(client, payload).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _profile_body(payload, **overrides):
    body = {
        "current_password": payload["password"],
        "name": payload["name"],
        "phone": payload["phone"],
        "roles": list(payload["roles"]),
        "address": payload["address"],
        "google_place_id": payload["google_place_id"],
        "latitude": payload["latitude"],
        "longitude": payload["longitude"],
    }
    body.update(overrides)
    return body


def test_update_profile_fields_and_event(client, app):
    headers = _auth_header(client, CLIENT)
    original_hash = None
    with app.app_context():
        original_hash = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one().password_hash

    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            CLIENT,
            name="New Name",
            phone="0501111111",
            roles=["CLIENT", "VOLUNTEER"],
            **OTHER_PLACE,
        ),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "New Name"
    assert body["phone"] == "0501111111"
    assert body["address"] == OTHER_PLACE["address"]
    assert body["google_place_id"] == OTHER_PLACE["google_place_id"]
    assert body["roles"] == ["CLIENT", "VOLUNTEER"]
    assert "password" not in body

    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        assert stored.name == "New Name"
        assert stored.password_hash == original_hash
        events = [
            event
            for event in EventRepository().list_by_aggregate("User", stored.id)
            if event.event_type == "UserProfileUpdated"
        ]
        assert len(events) == 1
        payload = json.loads(events[0].event_data)
        assert payload["user_id"] == stored.id
        assert payload["name"] == "New Name"
        assert payload["password_changed"] is False
        assert payload["google_place_id"] == OTHER_PLACE["google_place_id"]
        assert "password" not in payload
        assert "password_hash" not in payload


def test_wrong_current_password_returns_401(client, app):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, current_password="wrong-password", name="Hijacked"),
    )

    assert response.status_code == 401
    assert "current password" in response.get_json()["error"].lower()
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        assert stored.name == CLIENT["name"]
        events = [
            event
            for event in EventRepository().list_by_aggregate("User", stored.id)
            if event.event_type == "UserProfileUpdated"
        ]
        assert events == []


def test_missing_current_password_returns_400(client):
    headers = _auth_header(client, CLIENT)
    body = _profile_body(CLIENT)
    del body["current_password"]
    response = client.put("/api/users/me", headers=headers, json=body)

    assert response.status_code == 400


def test_mismatched_new_password_returns_400(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            CLIENT,
            new_password="newpassword",
            confirm_password="different1",
        ),
    )

    assert response.status_code == 400


def test_matching_new_password_updates_hash(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            CLIENT,
            new_password="newpassword",
            confirm_password="newpassword",
        ),
    )

    assert response.status_code == 200
    old_login = _login(client, CLIENT)
    assert old_login.status_code == 401
    new_login = _login(client, CLIENT, password="newpassword")
    assert new_login.status_code == 200
    assert new_login.get_json()["access_token"]


def test_address_without_place_returns_400(client):
    headers = _auth_header(client, CLIENT)
    body = _profile_body(CLIENT, address="Jerusalem")
    del body["google_place_id"]
    del body["latitude"]
    del body["longitude"]
    response = client.put("/api/users/me", headers=headers, json=body)

    assert response.status_code == 400


def test_client_cannot_set_volunteer_fields(client, app):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            CLIENT,
            about_me="Should not save",
            monthly_hours_goal=10,
        ),
    )

    assert response.status_code == 403
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        assert stored.about_me is None
        assert stored.monthly_hours_goal is None


def test_volunteer_can_set_about_me_and_goal(client):
    headers = _auth_header(client, VOLUNTEER)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            VOLUNTEER,
            about_me="I enjoy helping elderly people.",
            monthly_hours_goal=20,
        ),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["about_me"] == "I enjoy helping elderly people."
    assert body["monthly_hours_goal"] == 20


def test_update_profile_requires_auth(client):
    response = client.put("/api/users/me", json=_profile_body(CLIENT))

    assert response.status_code == 401


def test_name_only_update_keeps_location_cached_at(client, app):
    from datetime import datetime

    headers = _auth_header(client, CLIENT)
    original = datetime(2026, 1, 1, 12, 0, 0)
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        stored.location_cached_at = original
        db.session.commit()

    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, name="Name Only"),
    )

    assert response.status_code == 200
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        assert stored.name == "Name Only"
        assert stored.google_place_id == FIXTURE_PLACE["google_place_id"]
        assert stored.location_cached_at == original


def test_new_place_updates_location_cached_at(client, app):
    from datetime import datetime

    headers = _auth_header(client, CLIENT)
    original = datetime(2026, 1, 1, 12, 0, 0)
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        stored.location_cached_at = original
        db.session.commit()

    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, **OTHER_PLACE),
    )

    assert response.status_code == 200
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        assert stored.google_place_id == OTHER_PLACE["google_place_id"]
        assert stored.location_cached_at != original
        assert stored.location_cached_at is not None


def test_client_can_set_volunteer_fields_when_adding_role(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            CLIENT,
            roles=["CLIENT", "VOLUNTEER"],
            about_me="Now a volunteer",
            monthly_hours_goal=8,
        ),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["roles"] == ["CLIENT", "VOLUNTEER"]
    assert body["about_me"] == "Now a volunteer"
    assert body["monthly_hours_goal"] == 8


def test_email_on_update_returns_400(client, app):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, email="other@example.com"),
    )

    assert response.status_code == 400
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == CLIENT["email"])
        ).scalar_one()
        assert stored.email == CLIENT["email"]
        assert stored.name == CLIENT["name"]


def test_only_new_password_returns_400(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, new_password="newpassword"),
    )

    assert response.status_code == 400


def test_only_confirm_password_returns_400(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, confirm_password="newpassword"),
    )

    assert response.status_code == 400


def test_latitude_out_of_range_returns_400(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, latitude=91),
    )

    assert response.status_code == 400


def test_longitude_out_of_range_returns_400(client):
    headers = _auth_header(client, CLIENT)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(CLIENT, longitude=181),
    )

    assert response.status_code == 400


def test_volunteer_can_clear_about_me_and_goal(client, app):
    headers = _auth_header(client, VOLUNTEER)
    first = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(
            VOLUNTEER,
            about_me="I enjoy helping elderly people.",
            monthly_hours_goal=20,
        ),
    )
    assert first.status_code == 200

    response = client.put(
        "/api/users/me",
        headers=headers,
        json=_profile_body(VOLUNTEER, about_me="", monthly_hours_goal=None),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["about_me"] is None
    assert body["monthly_hours_goal"] is None
    with app.app_context():
        stored = db.session.execute(
            db.select(User).where(User.email == VOLUNTEER["email"])
        ).scalar_one()
        assert stored.about_me is None
        assert stored.monthly_hours_goal is None
