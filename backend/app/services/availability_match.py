from datetime import date

PYTHON_WEEKDAY_NAMES = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)


def weekday_name(value: date) -> str:
    return PYTHON_WEEKDAY_NAMES[value.weekday()]


def matches_availability(windows: list[dict], weekday: str, minutes: int) -> bool:
    for window in windows:
        if window["day_of_week"] != weekday:
            continue
        start = _hhmm_to_minutes(window["start_time"])
        end = _hhmm_to_minutes(window["end_time"])
        if start <= minutes < end:
            return True
    return False


def _hhmm_to_minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)
