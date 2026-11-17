"""Group parcel parts, check parcel decisions, and persist complete state."""

import csv
from pathlib import Path
import sqlite3


def read_parts(path):
    grouped = {}
    with Path(path).open(newline="") as source:
        for row in csv.DictReader(source):
            grouped.setdefault(row["parcel"], []).append((row["part"], int(row["weight"])))
    return {parcel: grouped[parcel] for parcel in sorted(grouped)}


def read_checks(path):
    with Path(path).open(newline="") as source:
        values = [row["accepted"] for row in csv.DictReader(source)]
    if any(value not in ("yes", "no") for value in values):
        raise ValueError("checks must contain yes or no")
    return [value == "yes" for value in values]


def check_parcels(parcels, checks=None):
    result = {"parcel_count": len(parcels)}
    if checks is not None:
        if len(checks) != len(parcels):
            raise ValueError("one check is required per parcel")
        result["accepted_count"] = sum(checks)
    return result


def save_checkpoint(parcels, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [(parcel, part, weight) for parcel, parts in parcels.items()
            for part, weight in parts]
    with sqlite3.connect(path) as database:
        database.execute("DROP TABLE IF EXISTS counts")
        database.execute("CREATE TABLE IF NOT EXISTS parts (parcel TEXT, part TEXT, weight INTEGER)")
        database.execute("DELETE FROM parts")
        database.executemany("INSERT INTO parts VALUES (?, ?, ?)", rows)
    return path


def restore_checkpoint(path):
    path = Path(path).resolve()
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        rows = database.execute("SELECT parcel, part, weight FROM parts ORDER BY parcel, rowid")
        grouped = {}
        for parcel, part, weight in rows:
            grouped.setdefault(parcel, []).append((part, weight))
    return grouped


def write_totals(parcels, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as database:
        database.execute("DROP TABLE IF EXISTS parts")
        database.execute("CREATE TABLE IF NOT EXISTS counts (parcel TEXT, part_count INTEGER)")
        database.execute("DELETE FROM counts")
        database.executemany("INSERT INTO counts VALUES (?, ?)",
                             [(parcel, len(parts)) for parcel, parts in sorted(parcels.items())])
    return path


def read_totals(path):
    path = Path(path).resolve()
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as database:
        return dict(database.execute("SELECT parcel, part_count FROM counts ORDER BY parcel"))
