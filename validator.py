import math
import re
from datetime import datetime

ID_PATTERN = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_PATTERN = re.compile(r"[A-Z]{3}")
DATETIME_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def load_airports(path: str) -> set[str]:
    airports = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if code == "" or code.startswith("#"):
                continue
            airports.add(code)
    return airports


def parse_datetime(text):
    if not isinstance(text, str) or not DATETIME_PATTERN.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, departure, arrival, price = [x.strip() for x in fields]

    if "" in (flight_id, origin, destination, departure, arrival, price):
        return "MISSING_FIELD"

    if not ID_PATTERN.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    if not AIRPORT_PATTERN.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not AIRPORT_PATTERN.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"

    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    dep_time = parse_datetime(departure)
    if dep_time is None:
        return "INVALID_DEPARTURE"
    arr_time = parse_datetime(arrival)
    if arr_time is None:
        return "INVALID_ARRIVAL"

    if arr_time <= dep_time:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    try:
        price_number = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(price_number):
        return "INVALID_PRICE"

    if price_number <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    flight_id, origin, destination, departure, arrival, price = [x.strip() for x in fields]
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }
