import json
from datetime import datetime, timedelta

from app.extensions import db
from app.models.domain_event import DomainEvent
from app.models.user import User
from app.models.volunteer_request import (
    APPROVED,
    COMPLETED,
    PENDING,
    REJECTED,
    VolunteerRequest,
)
from tests.place_data import FIXTURE_PLACE, OTHER_PLACE

CLIENT = {
    "name": "Status Client",
    "email": "status-client@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000301",
    "roles": ["CLIENT"],
    **FIXTURE_PLACE,
}

VOLUNTEER = {
    "name": "Status Volunteer",
    "email": "status-volunteer@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000302",
    "roles": ["VOLUNTEER"],
    **OTHER_PLACE,
}

OTHER_VOLUNTEER = {
    "name": "Other Status Volunteer",
    "email": "other-status-volunteer@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000303",
    "roles": ["VOLUNTEER"],
    **OTHER_PLACE,
}

BOTH_ROLES = {
    "name": "Both Roles Status",
    "email": "both-status@example.com",
    "password": "password",
    "confirm_password": "password",
    "phone": "0500000304",
    "roles": ["CLIENT", "VOLUNTEER"],
    **FIXTURE_PLACE,
}

PRIVATE_FIELDS = ("email", "phone", "password", "password_hash")


def _auth_header(client, payload):
    client.post("/api/auth/register", json=payload)
    token = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    ).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user_id(app, email):
    with app.app_context():
        return (
            db.session.execute(db.select(User).where(User.email == email))
            .scalar_one()
            .id
        )


def _at(days=0, hours=0, minute_of_hour=0):
    """A whole-minute time relative to now."""
    moment = datetime.now() + timedelta(days=days, hours=hours)
    return moment.replace(minute=minute_of_hour, second=0, microsecond=0)


def _seed(app, client_id, volunteer_id, start, duration=2, status=PENDING):
    with app.app_context():
        request = VolunteerRequest(
            client_id=client_id,
            volunteer_id=volunteer_id,
            category="Shopping",
            date=start.date(),
            start_time=start.time(),
            duration=duration,
            location=FIXTURE_PLACE["address"],
            google_place_id=FIXTURE_PLACE["google_place_id"],
            latitude=FIXTURE_PLACE["latitude"],
            longitude=FIXTURE_PLACE["longitude"],
            location_cached_at=datetime(2026, 1, 1),
            description="Help with groceries.",
            status=status,
        )
        db.session.add(request)
        db.session.commit()
        return request.id


def _status(app, request_id):
    with app.app_context():
        return db.session.get(VolunteerRequest, request_id).status


def _events(app, request_id):
    with app.app_context():
        return list(
            db.session.execute(
                db.select(DomainEvent)
                .where(
                    DomainEvent.aggregate_type == "VolunteerRequest",
                    DomainEvent.aggregate_id == request_id,
                )
                .order_by(DomainEvent.id)
            ).scalars()
        )


def _setup(client, app):
    client_headers = _auth_header(client, CLIENT)
    volunteer_headers = _auth_header(client, VOLUNTEER)
    return (
        client_headers,
        volunteer_headers,
        _user_id(app, CLIENT["email"]),
        _user_id(app, VOLUNTEER["email"]),
    )


def _future():
    return _at(days=3).replace(hour=10)


# --- approve / reject -------------------------------------------------------


def test_volunteer_approves_pending_request(client, app):
    _, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _future())

    response = client.post(f"/api/requests/{request_id}/approve", headers=volunteer_headers)

    assert response.status_code == 200
    assert response.get_json()["status"] == APPROVED
    assert _status(app, request_id) == APPROVED
    events = _events(app, request_id)
    assert [event.event_type for event in events] == ["VolunteerRequestApproved"]
    data = json.loads(events[0].event_data)
    assert data["previous_status"] == PENDING
    assert data["status"] == APPROVED
    assert data["acted_by"] == volunteer_id


def test_volunteer_rejects_pending_request(client, app):
    _, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _future())

    response = client.post(f"/api/requests/{request_id}/reject", headers=volunteer_headers)

    assert response.status_code == 200
    assert response.get_json()["status"] == REJECTED
    assert _status(app, request_id) == REJECTED
    assert [e.event_type for e in _events(app, request_id)] == ["VolunteerRequestRejected"]


def test_client_only_user_cannot_approve(client, app):
    client_headers, _, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _future())

    response = client.post(f"/api/requests/{request_id}/approve", headers=client_headers)

    assert response.status_code == 403
    assert _status(app, request_id) == PENDING
    assert _events(app, request_id) == []


def test_other_volunteer_gets_not_found(client, app):
    _, _, client_id, volunteer_id = _setup(client, app)
    other_headers = _auth_header(client, OTHER_VOLUNTEER)
    request_id = _seed(app, client_id, volunteer_id, _future())

    for action in ("approve", "reject"):
        response = client.post(f"/api/requests/{request_id}/{action}", headers=other_headers)
        assert response.status_code == 404
    assert _status(app, request_id) == PENDING
    assert _events(app, request_id) == []


def test_unknown_request_and_missing_token(client, app):
    _, volunteer_headers, _, _ = _setup(client, app)

    assert client.post("/api/requests/9999/approve", headers=volunteer_headers).status_code == 404
    assert client.post("/api/requests/1/approve").status_code == 401
    assert client.get("/api/requests").status_code == 401


def test_invalid_transitions_return_conflict(client, app):
    _, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    cases = [
        (APPROVED, "approve"),
        (APPROVED, "reject"),
        (REJECTED, "approve"),
        (REJECTED, "reject"),
        (COMPLETED, "approve"),
    ]
    for index, (status, action) in enumerate(cases):
        request_id = _seed(
            app, client_id, volunteer_id, _future() + timedelta(days=index), status=status
        )
        response = client.post(f"/api/requests/{request_id}/{action}", headers=volunteer_headers)
        assert response.status_code == 409, (status, action)
        assert _status(app, request_id) == status
        assert _events(app, request_id) == []


def test_approve_overlapping_request_is_rejected(client, app):
    _, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    start = _future()
    _seed(app, client_id, volunteer_id, start, duration=2, status=APPROVED)
    overlapping = _seed(app, client_id, volunteer_id, start + timedelta(hours=1))
    after = _seed(app, client_id, volunteer_id, start + timedelta(hours=2))

    response = client.post(f"/api/requests/{overlapping}/approve", headers=volunteer_headers)
    assert response.status_code == 409
    assert _status(app, overlapping) == PENDING

    # Starting exactly when the other one ends is not an overlap.
    response = client.post(f"/api/requests/{after}/approve", headers=volunteer_headers)
    assert response.status_code == 200


# --- automatic close ----------------------------------------------------------


def test_list_completes_ended_approved_request(client, app):
    client_headers, _, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _at(days=-2), status=APPROVED)

    response = client.get("/api/requests", headers=client_headers)

    assert response.status_code == 200
    assert response.get_json()[0]["status"] == COMPLETED
    assert _status(app, request_id) == COMPLETED
    events = _events(app, request_id)
    assert [e.event_type for e in events] == ["VolunteerRequestCompleted"]
    data = json.loads(events[0].event_data)
    assert data["acted_by"] == "SYSTEM"
    assert data["previous_status"] == APPROVED


def test_list_rejects_expired_pending_request(client, app):
    _, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _at(hours=-1))

    response = client.get("/api/requests", headers=volunteer_headers)

    assert response.get_json()[0]["status"] == REJECTED
    events = _events(app, request_id)
    assert [e.event_type for e in events] == ["VolunteerRequestRejected"]
    data = json.loads(events[0].event_data)
    assert data["acted_by"] == "SYSTEM"
    assert data["reason"] == "EXPIRED"


def test_in_progress_approved_request_stays_approved(client, app):
    client_headers, _, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(
        app, client_id, volunteer_id, _at(hours=-1), duration=3, status=APPROVED
    )

    client.get("/api/requests", headers=client_headers)

    assert _status(app, request_id) == APPROVED
    assert _events(app, request_id) == []


def test_future_requests_are_not_closed(client, app):
    client_headers, _, client_id, volunteer_id = _setup(client, app)
    pending = _seed(app, client_id, volunteer_id, _future())
    approved = _seed(app, client_id, volunteer_id, _future() + timedelta(days=1), status=APPROVED)

    client.get("/api/requests", headers=client_headers)

    assert _status(app, pending) == PENDING
    assert _status(app, approved) == APPROVED


def test_approving_expired_request_returns_conflict(client, app):
    _, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _at(days=-1))

    response = client.post(f"/api/requests/{request_id}/approve", headers=volunteer_headers)

    assert response.status_code == 409
    assert _status(app, request_id) == REJECTED
    assert [e.event_type for e in _events(app, request_id)] == ["VolunteerRequestRejected"]


def test_closing_twice_writes_one_event(client, app):
    client_headers, volunteer_headers, client_id, volunteer_id = _setup(client, app)
    request_id = _seed(app, client_id, volunteer_id, _at(days=-2), status=APPROVED)

    client.get("/api/requests", headers=client_headers)
    client.get("/api/requests", headers=volunteer_headers)
    client.get("/api/requests", headers=client_headers)

    assert len(_events(app, request_id)) == 1


# --- list ---------------------------------------------------------------------


def test_list_shows_both_sides_with_my_role(client, app):
    both_headers = _auth_header(client, BOTH_ROLES)
    _, _, client_id, volunteer_id = _setup(client, app)
    both_id = _user_id(app, BOTH_ROLES["email"])
    sent = _seed(app, both_id, volunteer_id, _future())
    received = _seed(app, client_id, both_id, _future() + timedelta(days=1))
    _seed(app, client_id, volunteer_id, _future())  # not related to BOTH_ROLES

    response = client.get("/api/requests", headers=both_headers)

    assert response.status_code == 200
    items = {item["id"]: item for item in response.get_json()}
    assert set(items) == {sent, received}
    assert items[sent]["my_role"] == "CLIENT"
    assert items[sent]["volunteer_name"] == VOLUNTEER["name"]
    assert items[received]["my_role"] == "VOLUNTEER"
    assert items[received]["client_name"] == CLIENT["name"]
    for item in items.values():
        for field in PRIVATE_FIELDS:
            assert field not in item


def test_list_filters_by_status(client, app):
    client_headers, _, client_id, volunteer_id = _setup(client, app)
    pending = _seed(app, client_id, volunteer_id, _future())
    _seed(app, client_id, volunteer_id, _future() + timedelta(days=1), status=APPROVED)

    response = client.get("/api/requests?status=pending", headers=client_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.get_json()] == [pending]


def test_list_rejects_unknown_status(client, app):
    client_headers, _, _, _ = _setup(client, app)

    response = client.get("/api/requests?status=DONE", headers=client_headers)

    assert response.status_code == 400
