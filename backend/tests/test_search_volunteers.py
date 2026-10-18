from app.extensions import db
from app.models.domain_event import DomainEvent
from tests.place_data import FIXTURE_PLACE, OTHER_PLACE

CLIENT = {
    "name": "Search Client",
    "email": "search-client@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000101",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}

VOLUNTEER_ONLY = {
    "name": "Volunteer Only",
    "email": "search-volunteer-only@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000102",
    "roles": ["VOLUNTEER"],
    **FIXTURE_PLACE,
}

MORNING = {
    "name": "Ada Morning",
    "email": "ada-morning@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000103",
    "roles": ["VOLUNTEER"],
    **FIXTURE_PLACE,
}
MORNING_ABOUT = "I enjoy assisting elderly people."

AFTERNOON = {
    "name": "Zoe Afternoon",
    "email": "zoe-afternoon@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000104",
    "roles": ["VOLUNTEER"],
    **OTHER_PLACE,
}

BOTH_ROLES = {
    "name": "Maya Both",
    "email": "maya-both@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000105",
    "roles": ["CLIENT", "VOLUNTEER"],
    **FIXTURE_PLACE,
}

MONDAY = "2026-10-12"
SUNDAY = "2026-10-11"
PRIVATE_FIELDS = (
    "email",
    "phone",
    "password",
    "password_hash",
    "google_place_id",
    "latitude",
    "longitude",
)


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


def _setup_volunteer(client, payload, categories, availability, about_me=None):
    headers = _auth_header(client, payload)
    if about_me is not None:
        client.put(
            "/api/users/me",
            headers=headers,
            json={
                "current_password": payload["password"],
                "name": payload["name"],
                "phone": payload["phone"],
                "roles": payload["roles"],
                "address": payload["address"],
                "google_place_id": payload["google_place_id"],
                "latitude": payload["latitude"],
                "longitude": payload["longitude"],
                "about_me": about_me,
            },
        )
    client.put(
        "/api/volunteers/me/categories",
        headers=headers,
        json={"categories": categories},
    )
    client.put(
        "/api/volunteers/me/availability",
        headers=headers,
        json={"availability": availability},
    )
    return headers


def _search(client, headers, **params):
    return client.get("/api/volunteers", headers=headers, query_string=params)


def _event_count(app):
    with app.app_context():
        return db.session.execute(
            db.select(db.func.count()).select_from(DomainEvent)
        ).scalar()


def _seed_volunteers(client):
    _setup_volunteer(
        client,
        MORNING,
        ["Shopping"],
        [
            {
                "day_of_week": "MONDAY",
                "start_time": "09:00",
                "end_time": "13:00",
            }
        ],
        about_me=MORNING_ABOUT,
    )
    _setup_volunteer(
        client,
        AFTERNOON,
        ["Shopping"],
        [
            {
                "day_of_week": "MONDAY",
                "start_time": "14:00",
                "end_time": "18:00",
            }
        ],
    )


def test_time_filter_keeps_morning_volunteer_and_omits_afternoon(client):
    _seed_volunteers(client)
    headers = _auth_header(client, CLIENT)

    response = _search(
        client,
        headers,
        category="Shopping",
        date=MONDAY,
        start_time="10:00",
    )
    assert response.status_code == 200
    names = [item["name"] for item in response.get_json()["volunteers"]]
    assert names == ["Ada Morning"]


def test_category_location_and_combined_filters(client):
    _seed_volunteers(client)
    headers = _auth_header(client, CLIENT)

    by_category = _search(client, headers, category="Shopping")
    assert by_category.status_code == 200
    assert [item["name"] for item in by_category.get_json()["volunteers"]] == [
        "Ada Morning",
        "Zoe Afternoon",
    ]

    by_location = _search(client, headers, location="jerusalem")
    assert by_location.status_code == 200
    assert [item["name"] for item in by_location.get_json()["volunteers"]] == [
        "Ada Morning"
    ]

    combined = _search(
        client,
        headers,
        category="Shopping",
        date=MONDAY,
        start_time="10:00",
        location="jerusalem",
    )
    assert combined.status_code == 200
    volunteers = combined.get_json()["volunteers"]
    assert [item["name"] for item in volunteers] == ["Ada Morning"]
    assert volunteers[0]["address"] == FIXTURE_PLACE["address"]
    assert volunteers[0]["categories"] == ["Shopping"]
    assert volunteers[0]["about_me"] == MORNING_ABOUT
    assert volunteers[0]["availability"] == [
        {"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"}
    ]


def test_no_match_returns_empty_list(client):
    _seed_volunteers(client)
    headers = _auth_header(client, CLIENT)

    response = _search(client, headers, category="Tutoring")
    assert response.status_code == 200
    assert response.get_json() == {"volunteers": []}


def test_invalid_filters_return_400(client):
    headers = _auth_header(client, CLIENT)
    cases = [
        {"category": "Skydiving"},
        {"date": "14-10-2026", "start_time": "10:00"},
        {"date": MONDAY, "start_time": "9:00"},
        {"date": MONDAY},
        {"start_time": "10:00"},
    ]
    for params in cases:
        response = _search(client, headers, **params)
        assert response.status_code == 400, params
        assert response.get_json()["error"]


def test_search_response_omits_private_fields(client):
    _seed_volunteers(client)
    headers = _auth_header(client, CLIENT)

    response = _search(client, headers, category="Shopping")
    assert response.status_code == 200
    for volunteer in response.get_json()["volunteers"]:
        for field in PRIVATE_FIELDS:
            assert field not in volunteer
        assert "id" in volunteer
        assert "name" in volunteer
        assert "address" in volunteer


def test_volunteer_only_user_receives_403(client):
    headers = _auth_header(client, VOLUNTEER_ONLY)
    response = _search(client, headers, category="Shopping")
    assert response.status_code == 403
    assert "client" in response.get_json()["error"].lower()


def test_missing_token_returns_401(client):
    response = client.get("/api/volunteers")
    assert response.status_code == 401


def test_empty_search_returns_every_volunteer_and_omits_client_only(client):
    _seed_volunteers(client)
    headers = _auth_header(client, CLIENT)

    response = _search(client, headers)
    assert response.status_code == 200
    names = [item["name"] for item in response.get_json()["volunteers"]]
    assert names == ["Ada Morning", "Zoe Afternoon"]
    assert "Search Client" not in names


def test_monday_1300_matches_window_start_not_window_end(client):
    _setup_volunteer(
        client,
        MORNING,
        ["Shopping"],
        [{"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"}],
    )
    _setup_volunteer(
        client,
        AFTERNOON,
        ["Shopping"],
        [{"day_of_week": "MONDAY", "start_time": "13:00", "end_time": "16:00"}],
    )
    headers = _auth_header(client, CLIENT)

    response = _search(
        client,
        headers,
        category="Shopping",
        date=MONDAY,
        start_time="13:00",
    )
    assert response.status_code == 200
    assert [item["name"] for item in response.get_json()["volunteers"]] == [
        "Zoe Afternoon"
    ]


def test_sunday_date_matches_sunday_window(client):
    _setup_volunteer(
        client,
        MORNING,
        ["Tutoring"],
        [{"day_of_week": "SUNDAY", "start_time": "09:00", "end_time": "12:00"}],
    )
    headers = _auth_header(client, CLIENT)

    response = _search(
        client,
        headers,
        category="Tutoring",
        date=SUNDAY,
        start_time="10:00",
    )
    assert response.status_code == 200
    assert [item["name"] for item in response.get_json()["volunteers"]] == [
        "Ada Morning"
    ]


def test_user_with_both_roles_can_search_and_appear_in_results(client):
    both_auth = _setup_volunteer(
        client,
        BOTH_ROLES,
        ["Cooking"],
        [{"day_of_week": "MONDAY", "start_time": "09:00", "end_time": "13:00"}],
    )

    as_searcher = _search(client, both_auth, category="Cooking")
    assert as_searcher.status_code == 200
    assert [item["name"] for item in as_searcher.get_json()["volunteers"]] == [
        "Maya Both"
    ]

    client_headers = _auth_header(client, CLIENT)
    from_client = _search(client, client_headers, category="Cooking")
    assert from_client.status_code == 200
    assert [item["name"] for item in from_client.get_json()["volunteers"]] == [
        "Maya Both"
    ]


def test_impossible_calendar_date_returns_400(client):
    headers = _auth_header(client, CLIENT)
    response = _search(
        client,
        headers,
        date="2026-02-31",
        start_time="10:00",
    )
    assert response.status_code == 400
    assert "date" in response.get_json()["error"].lower()


def test_repeating_search_does_not_add_a_domain_event(client, app):
    _seed_volunteers(client)
    headers = _auth_header(client, CLIENT)
    before = _event_count(app)

    first = _search(client, headers, category="Shopping")
    second = _search(client, headers, category="Shopping")

    assert first.status_code == 200
    assert second.status_code == 200
    assert _event_count(app) == before
