from datetime import datetime, timedelta

from app.models.volunteer_request import VolunteerRequest


def now() -> datetime:
    """Server local time. Request date and start time are stored as naive local values."""
    return datetime.now()


def activity_start(request: VolunteerRequest) -> datetime:
    return datetime.combine(request.date, request.start_time)


def activity_end(request: VolunteerRequest) -> datetime:
    return activity_start(request) + timedelta(hours=request.duration)


def overlaps(first: VolunteerRequest, second: VolunteerRequest) -> bool:
    return activity_start(first) < activity_end(second) and activity_start(
        second
    ) < activity_end(first)
