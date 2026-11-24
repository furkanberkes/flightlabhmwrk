import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "241RDB000"
FIRST_NAME = "Sefer"
LAST_NAME = "Seferoglu"


class RunError(Exception):
    pass


def build_parser():
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight schedule CSV files, store them as JSON and run queries.",
        allow_abbrev=False)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in the folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output path of the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries to run")
    parser.add_argument("-r", metavar="FOLDER", help="folder for the response file (default: current directory)")
    return parser


def get_arguments(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.i or args.d) and not args.a:
        parser.error("-a is required together with -i or -d")
    if args.j and args.o:
        parser.error("-o cannot be used together with -j")
    return args


def read_json(path):
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except ValueError:
            raise RunError(f"{path} is not valid JSON")


def load_database(path):
    db = read_json(path)
    if not isinstance(db, list) or not all(isinstance(item, dict) for item in db):
        raise RunError(f"{path} must contain a JSON array of objects")
    return db


def load_queries(path):
    queries = read_json(path)
    if not isinstance(queries, (dict, list)):
        raise RunError(f"{path} must contain a query object or an array of query objects")
    return queries


def find_csv_files(folder):
    if not os.path.isdir(folder):
        raise RunError(f"folder {folder} does not exist")
    names = sorted(os.listdir(folder))
    paths = [os.path.join(folder, n) for n in names
             if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n))]
    if not paths:
        raise RunError(f"no .csv files found in {folder}")
    return paths


def write_database_and_log(records, errors, db_path):
    log_path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "errors.log")

    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        logger.info("%d valid rows, %d invalid rows", len(records), len(errors))
        for message in errors:
            logger.warning("%s", message)
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    finally:
        logger.removeHandler(handler)
        handler.close()


def write_response(responses, folder):
    now = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{now}.json"
    with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2)


def run(args):
    queries = load_queries(args.q) if args.q else None

    if args.j:
        db = load_database(args.j)
    else:
        airports = load_airports(args.a)
        paths = [args.i] if args.i else find_csv_files(args.d)
        db, errors = parse_files(paths, airports)
        write_database_and_log(db, errors, args.o or "db.json")
        print(f"Parsed {len(paths)} file(s): {len(db)} valid rows, {len(errors)} invalid rows")

    if queries is not None:
        responses = run_queries(db, queries)
        write_response(responses, args.r or ".")
        print(f"Ran {len(responses)} queries")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        args = get_arguments(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0

    try:
        return run(args)
    except RunError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError, RecursionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
