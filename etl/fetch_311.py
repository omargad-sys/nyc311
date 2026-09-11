"""
NYC311 Pulse - ETL script
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
import psycopg2
from psycopg2.extras import execute_values

SOCRATA_ENDPOINT = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
PAGE_SIZE = int(os.environ.get("PAGE_SIZE", 5000))
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", 365))
DATE_FIELDS = ("created_date", "closed_date")


def get_since_date() -> str:
    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    return since.strftime("%Y-%m-%dT%H:%M:%S.000")


def fetch_page(offset: int, since: str, app_token: str) -> list:
    params = {
        "$select": "unique_key, created_date, closed_date, agency, agency_name, "
                   "complaint_type, descriptor, borough, status, latitude, longitude",
        "$where": f"created_date >= '{since}'",
        "$order": "created_date",
        "$limit": PAGE_SIZE,
        "$offset": offset,
    }
    headers = {"X-App-Token": app_token} if app_token else {}
    resp = requests.get(SOCRATA_ENDPOINT, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_row(row: dict) -> dict:
    created = parse_dt(row.get("created_date"))
    closed = parse_dt(row.get("closed_date"))
    resolution_hours = None
    if created and closed:
        resolution_hours = round((closed - created).total_seconds() / 3600.0, 2)

    return {
        "unique_key": int(row["unique_key"]) if row.get("unique_key") else None,
        "created_date": created,
        "closed_date": closed,
        "agency_code": row.get("agency"),
        "agency_name": row.get("agency_name") or row.get("agency"),
        "complaint_type": row.get("complaint_type"),
        "descriptor": row.get("descriptor"),
        "borough": row.get("borough"),
        "status": row.get("status"),
        "resolution_hours": resolution_hours,
        "latitude": float(row["latitude"]) if row.get("latitude") else None,
        "longitude": float(row["longitude"]) if row.get("longitude") else None,
    }


def upsert_dimensions(conn, rows: list):
    agencies = {(r["agency_code"], r["agency_name"]) for r in rows if r["agency_code"]}
    complaint_types = {(r["complaint_type"], r["descriptor"]) for r in rows if r["complaint_type"]}
    boroughs = {(r["borough"],) for r in rows if r["borough"]}
    dates = {r["created_date"].date() for r in rows if r["created_date"]}

    with conn.cursor() as cur:
        if agencies:
            execute_values(
                cur,
                "INSERT INTO dim_agency (agency_code, agency_name) VALUES %s "
                "ON CONFLICT (agency_code) DO NOTHING",
                list(agencies),
            )
        if complaint_types:
            execute_values(
                cur,
                "INSERT INTO dim_complaint_type (complaint_type, descriptor) VALUES %s "
                "ON CONFLICT (complaint_type) DO NOTHING",
                list(complaint_types),
            )
        if boroughs:
            execute_values(
                cur,
                "INSERT INTO dim_borough (borough) VALUES %s ON CONFLICT (borough) DO NOTHING",
                list(boroughs),
            )
        if dates:
            date_rows = [
                (d, d.year, d.month, d.day, d.strftime("%A"), d.weekday() >= 5)
                for d in dates
            ]
            execute_values(
                cur,
                "INSERT INTO dim_date (date_key, year, month, day, day_of_week, is_weekend) "
                "VALUES %s ON CONFLICT (date_key) DO NOTHING",
                date_rows,
            )
    conn.commit()


def upsert_facts(conn, rows: list):
    fact_rows = [
        (
            r["unique_key"],
            r["created_date"],
            r["created_date"].date(),
            r["closed_date"],
            r["agency_code"],
            r["complaint_type"],
            r["borough"],
            r["status"],
            r["resolution_hours"],
            r["latitude"],
            r["longitude"],
        )
        for r in rows
        if r["unique_key"] and r["created_date"]
    ]
    if not fact_rows:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO fact_311_requests (
                unique_key, created_date, created_date_key, closed_date,
                agency_code, complaint_type, borough, status,
                resolution_hours, latitude, longitude
            ) VALUES %s
            ON CONFLICT (unique_key) DO UPDATE SET
                closed_date = EXCLUDED.closed_date,
                status = EXCLUDED.status,
                resolution_hours = EXCLUDED.resolution_hours
            """,
            fact_rows,
        )
    conn.commit()


def main():
    app_token = os.environ.get("SOCRATA_APP_TOKEN", "")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("DATABASE_URL environment variable is required")

    since = get_since_date()
    conn = psycopg2.connect(database_url)

    offset = 0
    total_loaded = 0
    print(f"Pulling 311 requests created since {since}")

    while True:
        batch = fetch_page(offset, since, app_token)
        if not batch:
            break

        parsed = [parse_row(r) for r in batch]
        parsed = [r for r in parsed if r["unique_key"] and r["created_date"]]

        upsert_dimensions(conn, parsed)
        upsert_facts(conn, parsed)

        total_loaded += len(parsed)
        print(f"  loaded {total_loaded} rows so far (offset {offset})")

        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.2)  # be polite to the API

    conn.close()
    print(f"Done. {total_loaded} rows upserted.")


if __name__ == "__main__":
    main()
