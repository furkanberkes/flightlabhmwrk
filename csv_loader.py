import csv
import os

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    records = []
    errors = []
    seen = set()

    for path in paths:
        file_name = os.path.basename(path)

        with open(path, encoding="utf-8-sig") as f:
            for line_number, line in enumerate(f, start=1):
                text = line.rstrip("\r\n")

                if line_number == 1:
                    continue
                stripped = text.strip()
                if stripped == "" or stripped.startswith("#"):
                    continue

                try:
                    fields = next(csv.reader([text]))
                except csv.Error:
                    errors.append(f"{file_name}:{line_number}: WRONG_FIELD_COUNT | {text}")
                    continue

                code = validate_row(fields, airports)
                if code is None:
                    record = to_record(fields)
                    key = (record["flight_id"], record["departure_datetime"])
                    if key in seen:
                        code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(record)

                if code is not None:
                    errors.append(f"{file_name}:{line_number}: {code} | {text}")

    return records, errors
