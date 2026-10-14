import json

from app.extensions import db
from app.models.availability import Availability
from app.models.user import User
from app.persistence.availability_repository import DAY_ORDER, format_hhmm
from app.persistence.event_repository import EventRepository
from tests.place_data import FIXTURE_PLACE

CLIENT = {
    "name": "Client User",
    "email": "client-availability@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000001",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}

VOLUNTEER = {
    "name": "Volunteer User",
    "email": "volunteer-availability@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000002",
    "roles": ["VOLUNTEER"],
    **FIXTURE_PLACE,
}

BOTH_ROLES = {
    "name": "Both Roles User",
    "email": "both-availability@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000003",
    "roles": ["CLIENT", "VOLUNTEER"],
    **FIXTURE_PLACE,
}

FIRST_WINDOWS = [
    {"day_of_week": "SUNDAY", "start_time": "09:00", "end_time": "12:00"},
    {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"},
]
REPLACEMENT = [
    {"day_of_week": "WEDNESDAY", "start_time": "16:00", "end_time": "20:00"},
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
        return db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar_one().id


def _stored_windows(app, volunteer_id):
    with app.app_context():
        rows = list(
            db.session.execute(
                db.select(Availability).where(
                    Availability.volunteer_id == volunteer_id
                )
            ).scalars()
        )
        rows.sort(
            key=lambda row: (DAY_ORDER.get(row.day_of_week, 99), row.start_time)
        )
        return [
            {
                "day_of_week": row.day_of_week,
                "start_time": format_hhmm(row.start_time),
                "end_time": format_hhmm(row.end_time),
            }
            for row in rows
        ]


def _availability_events(app, volunteer_id):
    with app.app_context():
        return [
            event
            for event in EventRepository().list_by_aggregate("User", volunteer_id)
            if event.event_type == "VolunteerAvailabilityUpdated"
        ]


def test_volunteer_gets_empty_list_then_saves_and_reads_sunday_first(client, app):
    headers = _auth_header(client, VOLUNTEER)

    empty = client.get("/api/volunteers/me/availability", headers=headers)
    assert empty.status_code == 200
    assert empty.get_json() == {"availability": []}

    saved = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={
            "availability": [
                FIRST_WINDOWS[1],
                FIRST_WINDOWS[0],
            ]
        },
    )
    assert saved.status_code == 200
    assert saved.get_json()["availability"] == FIRST_WINDOWS

    loaded = client.get("/api/volunteers/me/availability", headers=headers)
    assert loaded.status_code == 200
    assert loaded.get_json()["availability"] == FIRST_WINDOWS

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    stored = _stored_windows(app, volunteer_id)
    assert {"day_of_week": "SUNDAY", "start_time": "09:00", "end_time": "12:00"} in stored
    assert {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"} in stored
    events = _availability_events(app, volunteer_id)
    assert len(events) == 1
    payload = json.loads(events[0].event_data)
    assert payload["volunteer_id"] == volunteer_id
    assert payload["availability"] == [FIRST_WINDOWS[1], FIRST_WINDOWS[0]]


def test_second_save_replaces_windows_and_records_new_list(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": FIRST_WINDOWS},
    )

    response = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": REPLACEMENT},
    )
    assert response.status_code == 200
    assert response.get_json()["availability"] == REPLACEMENT

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_windows(app, volunteer_id) == REPLACEMENT
    events = _availability_events(app, volunteer_id)
    assert len(events) == 2
    payload = json.loads(events[-1].event_data)
    assert payload["volunteer_id"] == volunteer_id
    assert payload["availability"] == REPLACEMENT


def test_empty_array_clears_rows_and_records_event(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": FIRST_WINDOWS},
    )

    response = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": []},
    )
    assert response.status_code == 200
    assert response.get_json() == {"availability": []}

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_windows(app, volunteer_id) == []
    events = _availability_events(app, volunteer_id)
    assert len(events) == 2
    assert json.loads(events[-1].event_data)["availability"] == []


def test_invalid_windows_return_400_and_leave_state_unchanged(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": FIRST_WINDOWS},
    )
    volunteer_id = _user_id(app, VOLUNTEER["email"])

    cases = [
        (
            [{"day_of_week": "FUNDAY", "start_time": "09:00", "end_time": "12:00"}],
            "day_of_week",
        ),
        (
            [{"day_of_week": "MONDAY", "start_time": "9:00", "end_time": "12:00"}],
            "start_time",
        ),
        (
            [{"day_of_week": "MONDAY", "start_time": "13:00", "end_time": "09:00"}],
            "later",
        ),
        (
            [
                {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"},
                {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"},
            ],
            "overlap",
        ),
        (
            [
                {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"},
                {"day_of_week": "MONDAY", "start_time": "12:00", "end_time": "15:00"},
            ],
            "overlap",
        ),
    ]
    for payload, expected in cases:
        response = client.put(
            "/api/volunteers/me/availability",
            headers=headers,
            json={"availability": payload},
        )
        assert response.status_code == 400, payload
        error = response.get_json()["error"].lower()
        if expected == "later":
            assert "later" in error
        elif expected == "overlap":
            assert "overlap" in error
        else:
            assert expected in error
        assert _stored_windows(app, volunteer_id) == FIRST_WINDOWS
        assert len(_availability_events(app, volunteer_id)) == 1


def test_touching_windows_on_the_same_day_are_saved(client, app):
    headers = _auth_header(client, VOLUNTEER)
    windows = [
        {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"},
        {"day_of_week": "MONDAY", "start_time": "13:00", "end_time": "16:00"},
    ]

    response = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": windows},
    )
    assert response.status_code == 200
    assert response.get_json()["availability"] == windows

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_windows(app, volunteer_id) == windows


def test_user_with_both_roles_can_get_and_put_availability(client, app):
    headers = _auth_header(client, BOTH_ROLES)

    empty = client.get("/api/volunteers/me/availability", headers=headers)
    assert empty.status_code == 200
    assert empty.get_json() == {"availability": []}

    saved = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": FIRST_WINDOWS},
    )
    assert saved.status_code == 200
    assert saved.get_json()["availability"] == FIRST_WINDOWS

    volunteer_id = _user_id(app, BOTH_ROLES["email"])
    assert _stored_windows(app, volunteer_id) == FIRST_WINDOWS
    events = _availability_events(app, volunteer_id)
    assert len(events) == 1
    assert json.loads(events[0].event_data)["volunteer_id"] == volunteer_id


def test_same_clock_times_on_different_days_are_saved(client, app):
    headers = _auth_header(client, VOLUNTEER)
    windows = [
        {"day_of_week": "SUNDAY", "start_time": "09:00", "end_time": "12:00"},
        {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "12:00"},
    ]

    response = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": windows},
    )
    assert response.status_code == 200
    assert response.get_json()["availability"] == windows

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_windows(app, volunteer_id) == windows


def test_equal_start_and_end_returns_400_and_leaves_state_unchanged(client, app):
    headers = _auth_header(client, VOLUNTEER)
    client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": FIRST_WINDOWS},
    )

    response = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={
            "availability": [
                {"day_of_week": "TUESDAY", "start_time": "09:00", "end_time": "09:00"}
            ]
        },
    )
    assert response.status_code == 400
    assert "later" in response.get_json()["error"].lower()

    volunteer_id = _user_id(app, VOLUNTEER["email"])
    assert _stored_windows(app, volunteer_id) == FIRST_WINDOWS
    assert len(_availability_events(app, volunteer_id)) == 1


def test_client_only_user_receives_403_on_get_and_put(client, app):
    headers = _auth_header(client, CLIENT)

    get_response = client.get("/api/volunteers/me/availability", headers=headers)
    put_response = client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": FIRST_WINDOWS},
    )

    assert get_response.status_code == 403
    assert "volunteer" in get_response.get_json()["error"].lower()
    assert put_response.status_code == 403
    assert "volunteer" in put_response.get_json()["error"].lower()

    user_id = _user_id(app, CLIENT["email"])
    assert _stored_windows(app, user_id) == []
    assert _availability_events(app, user_id) == []


def test_missing_token_returns_401(client):
    get_response = client.get("/api/volunteers/me/availability")
    put_response = client.put(
        "/api/volunteers/me/availability",
        json={"availability": FIRST_WINDOWS},
    )

    assert get_response.status_code == 401
    assert put_response.status_code == 401
