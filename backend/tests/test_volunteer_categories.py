import json

from app.extensions import db
from app.models.user import User
from app.models.volunteer_category import VolunteerCategory
from app.persistence.event_repository import EventRepository
from tests.place_data import FIXTURE_PLACE

CLIENT = {
    "name": "Client User",
    "email": "client-categories@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000001",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}

VOLUNTEER = {
    "name": "Volunteer User",
    "email": "volunteer-categories@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000002",
    "roles": ["VOLUNTEER"],
    **FIXTURE_PLACE,
}

FIRST_SELECTION = ["Elderly Assistance", "Shopping", "Transportation"]
REPLACEMENT = ["Cooking", "Cleaning"]


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
        return db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one().id


def _stored_categories(app, volunteer_id):
    with app.app_context():
        return list(
            db.session.execute(
                db.select(VolunteerCategory.category)
                .where(VolunteerCategory.volunteer_id == volunteer_id)
                .order_by(VolunteerCategory.category)
            ).scalars()
        )


def _category_events(app, volunteer_id):
    with app.app_context():
        return [
            event
            for event in EventRepository().list_by_aggregate("User", volunteer_id)
            if event.event_type == "VolunteerCategoriesUpdated"
        ]


def test_volunteer_gets_empty_list_then_saves_and_reads_categories(client, app):
    headers = _auth_header(client, VOLUNTEER)

    empty = client.get("/api/volunteers/me/categories", headers=headers)
    assert empty.status_code == 200
    assert empty.get_json() == {"categories": []}

    saved = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": FIRST_SELECTION},
    )
    assert saved.status_code == 200
    assert saved.get_json()["categories"] == sorted(FIRST_SELECTION)

    loaded = client.get("/api/volunteers/me/categories", headers=headers)
    assert loaded.status_code == 200
    assert loaded.get_json()["categories"] == sorted(FIRST_SELECTION)

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_categories(app, volunteer_id) == sorted(FIRST_SELECTION)
    events = _category_events(app, volunteer_id)
    assert len(events) == 1
    payload = json.loads(events[0].event_data)
    assert payload["volunteer_id"] == volunteer_id
    assert payload["categories"] == FIRST_SELECTION


def test_second_save_replaces_selection_and_records_new_list(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": FIRST_SELECTION},
    )

    response = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": REPLACEMENT},
    )
    assert response.status_code == 200
    assert response.get_json()["categories"] == sorted(REPLACEMENT)

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_categories(app, volunteer_id) == sorted(REPLACEMENT)
    events = _category_events(app, volunteer_id)
    assert len(events) == 2
    payload = json.loads(events[-1].event_data)
    assert payload["volunteer_id"] == volunteer_id
    assert payload["categories"] == REPLACEMENT


def test_empty_array_clears_rows_and_records_event(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": FIRST_SELECTION},
    )

    response = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": []},
    )
    assert response.status_code == 200
    assert response.get_json() == {"categories": []}

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_categories(app, volunteer_id) == []
    events = _category_events(app, volunteer_id)
    assert len(events) == 2
    assert json.loads(events[-1].event_data)["categories"] == []


def test_unknown_category_returns_400_and_leaves_state_unchanged(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": FIRST_SELECTION},
    )

    response = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": ["Shopping", "Skydiving"]},
    )
    assert response.status_code == 400
    assert "unknown category" in response.get_json()["error"].lower()

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_categories(app, volunteer_id) == sorted(FIRST_SELECTION)
    assert len(_category_events(app, volunteer_id)) == 1


def test_duplicate_category_returns_400_and_leaves_state_unchanged(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": FIRST_SELECTION},
    )

    response = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": ["Shopping", "Shopping"]},
    )
    assert response.status_code == 400
    assert "duplicate" in response.get_json()["error"].lower()

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_categories(app, volunteer_id) == sorted(FIRST_SELECTION)
    assert len(_category_events(app, volunteer_id)) == 1


def test_blank_category_returns_400(client):
    headers = _auth_header(client, VOLUNTEER)
    response = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": ["Shopping", "  "]},
    )
    assert response.status_code == 400
    assert "blank" in response.get_json()["error"].lower()


def test_client_only_user_receives_403_on_get_and_put(client, app):
    headers = _auth_header(client, CLIENT)

    get_response = client.get("/api/volunteers/me/categories", headers=headers)
    put_response = client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": ["Shopping"]},
    )

    assert get_response.status_code == 403
    assert "volunteer" in get_response.get_json()["error"].lower()
    assert put_response.status_code == 403
    assert "volunteer" in put_response.get_json()["error"].lower()

    user_id = _user_id(app, CLIENT["email"])
    assert _stored_categories(app, user_id) == []
    assert _category_events(app, user_id) == []


def test_missing_token_returns_401(client):
    get_response = client.get("/api/volunteers/me/categories")
    put_response = client.put(
        "/api/volunteers/me/categories",
        json={"categories": ["Shopping"]},
    )

    assert get_response.status_code == 401
    assert put_response.status_code == 401
