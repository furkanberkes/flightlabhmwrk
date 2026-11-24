import math

from validator import parse_datetime

RECORD_KEYS = ["flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price"]
STRING_KEYS = ["flight_id", "origin", "destination"]
DATETIME_KEYS = ["departure_datetime", "arrival_datetime"]
NUMBER_KEYS = ["price", "min_price"]
ALLOWED_KEYS = STRING_KEYS + DATETIME_KEYS + NUMBER_KEYS + ["sort_by", "order", "limit"]


def is_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def is_valid_query(query):
    if not isinstance(query, dict):
        return False

    for key, value in query.items():
        if key not in ALLOWED_KEYS:
            return False
        if key in STRING_KEYS and not isinstance(value, str):
            return False
        if key in DATETIME_KEYS and parse_datetime(value) is None:
            return False
        if key in NUMBER_KEYS and not is_number(value):
            return False
        if key == "sort_by" and (not isinstance(value, str) or value not in RECORD_KEYS):
            return False
        if key == "order" and (not isinstance(value, str) or value not in ("asc", "desc")):
            return False
        if key == "limit" and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            return False

    if "order" in query and "sort_by" not in query:
        return False
    return True


def flight_matches(flight, query):
    for key in STRING_KEYS:
        if key in query and flight[key] != query[key]:
            return False
    if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
        return False
    if "price" in query and flight["price"] > query["price"]:
        return False
    if "min_price" in query and flight["price"] < query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    if not is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [flight for flight in db if flight_matches(flight, query)]

    if "sort_by" in query:
        descending = query.get("order", "asc") == "desc"
        matches = sorted(matches, key=lambda flight: flight[query["sort_by"]], reverse=descending)

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    if isinstance(queries, list):
        return [run_query(db, q) for q in queries]
    return [run_query(db, queries)]
