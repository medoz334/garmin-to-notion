from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
from notion_client import Client
from dotenv import load_dotenv
from garmin_auth import login_garmin
import os


JST = ZoneInfo("Asia/Tokyo")


# ---------------------------------------------------------------------------
# Garmin data fetch
# ---------------------------------------------------------------------------

def get_sleep_data_range(garmin, backfill_days: int) -> list:
    """Fetch sleep data for the last `backfill_days` days, ending yesterday."""
    results = []
    today = date.today()

    for i in range(1, backfill_days + 1):
        target_date = today - timedelta(days=i)
        try:
            data = garmin.get_sleep_data(target_date.isoformat())
            if data:
                results.append(data)
        except Exception as e:
            print(f"Warning: Failed to fetch sleep data for {target_date}: {e}")

    return results


# ---------------------------------------------------------------------------
# Format helpers
# ---------------------------------------------------------------------------

def seconds_to_hours(seconds: int | float | None) -> float:
    seconds = seconds or 0
    return round(seconds / 3600, 2)


def seconds_to_hm_text(seconds: int | float | None) -> str:
    seconds = seconds or 0
    total_minutes = round(seconds / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def garmin_timestamp_to_jst_iso(value):
    """
    Garmin sleep timestamps may be ISO strings or Unix timestamps.
    Keys ending in GMT are treated as UTC when timezone info is missing.
    """
    if value is None:
        return None

    try:
        if isinstance(value, (int, float)):
            # Garmin may return milliseconds in some contexts.
            timestamp = value / 1000 if value > 10_000_000_000 else value
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return dt.astimezone(JST).isoformat(timespec="seconds")

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None

            # Numeric string timestamp.
            if raw.replace(".", "", 1).isdigit():
                timestamp = float(raw)
                timestamp = timestamp / 1000 if timestamp > 10_000_000_000 else timestamp
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                return dt.astimezone(JST).isoformat(timespec="seconds")

            # ISO string.
            normalized = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)

            # sleepStartTimestampGMT / sleepEndTimestampGMT are GMT values.
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt.astimezone(JST).isoformat(timespec="seconds")

    except Exception as e:
        print(f"Warning: Failed to parse Garmin timestamp {value}: {e}")
        return None

    return None


def time_range_text(start_iso: str | None, end_iso: str | None) -> str:
    if not start_iso or not end_iso:
        return ""

    try:
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
        return f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------

def sleep_data_exists(client, database_id: str, sleep_date: str) -> bool:
    """
    Check duplicate records by Long Date.
    In this DB, Date is a title property, not a date property.
    """
    response = client.databases.query(
        database_id=database_id,
        filter={
            "property": "Long Date",
            "date": {"equals": sleep_date}
        }
    )
    return len(response.get("results", [])) > 0


def rich_text(value: str):
    return {
        "rich_text": [
            {
                "text": {
                    "content": value
                }
            }
        ]
    }


def create_sleep_data(client, database_id: str, data: dict, skip_zero_sleep: bool = True) -> bool:
    """
    Create a Notion page for a sleep record.
    Returns True if created, False if skipped.
    """
    dto = data.get("dailySleepDTO", {})
    sleep_date = dto.get("calendarDate")

    if not sleep_date:
        print("Skipped: No calendarDate found")
        return False

    total_sleep_seconds = dto.get("sleepTimeSeconds", 0) or 0
    deep_sleep_seconds = dto.get("deepSleepSeconds", 0) or 0
    light_sleep_seconds = dto.get("lightSleepSeconds", 0) or 0
    rem_sleep_seconds = dto.get("remSleepSeconds", 0) or 0
    awake_seconds = dto.get("awakeSleepSeconds", 0) or 0

    total_sleep_hours = seconds_to_hours(total_sleep_seconds)
    deep_sleep_hours = seconds_to_hours(deep_sleep_seconds)
    light_sleep_hours = seconds_to_hours(light_sleep_seconds)
    rem_sleep_hours = seconds_to_hours(rem_sleep_seconds)
    awake_hours = seconds_to_hours(awake_seconds)

    if skip_zero_sleep and total_sleep_hours == 0:
        print(f"Skipped (zero sleep): {sleep_date}")
        return False

    sleep_start_jst = garmin_timestamp_to_jst_iso(dto.get("sleepStartTimestampGMT"))
    sleep_end_jst = garmin_timestamp_to_jst_iso(dto.get("sleepEndTimestampGMT"))
    times_text = time_range_text(sleep_start_jst, sleep_end_jst)

    resting_hr = (
        dto.get("restingHeartRate")
        or dto.get("restingHR")
        or data.get("restingHeartRate")
        or data.get("restingHR")
    )

    properties = {
        "Date": {
            "title": [
                {
                    "text": {
                        "content": sleep_date
                    }
                }
            ]
        },
        "Long Date": {
            "date": {
                "start": sleep_date
            }
        },
        "Total Sleep (h)": {
            "number": total_sleep_hours
        },
        "Deep Sleep (h)": {
            "number": deep_sleep_hours
        },
        "Light Sleep (h)": {
            "number": light_sleep_hours
        },
        "REM Sleep (h)": {
            "number": rem_sleep_hours
        },
        "Awake Time (h)": {
            "number": awake_hours
        },
        "Total Sleep": rich_text(seconds_to_hm_text(total_sleep_seconds)),
        "Deep Sleep": rich_text(seconds_to_hm_text(deep_sleep_seconds)),
        "Light Sleep": rich_text(seconds_to_hm_text(light_sleep_seconds)),
        "REM Sleep": rich_text(seconds_to_hm_text(rem_sleep_seconds)),
        "Awake Time": rich_text(seconds_to_hm_text(awake_seconds)),
        "Sleep Goal": {
            "checkbox": total_sleep_hours >= 7
        },
    }

    if sleep_start_jst:
        properties["Full Date/Time"] = {
            "date": {
                "start": sleep_start_jst
            }
        }

    if times_text:
        properties["Times"] = rich_text(times_text)

    if resting_hr is not None:
        properties["Resting HR"] = {
            "number": resting_hr
        }

    client.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )

    print(f"Created: {sleep_date} - {total_sleep_hours}h sleep")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_dotenv()

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_SLEEP_DB_ID")
    backfill_days = int(os.getenv("GARMIN_SLEEP_BACKFILL_DAYS") or "1")

    if not notion_token:
        raise RuntimeError("NOTION_TOKEN is not set")

    if not database_id:
        raise RuntimeError("NOTION_SLEEP_DB_ID is not set")

    garmin = login_garmin()
    client = Client(auth=notion_token)

    print(f"Fetching last {backfill_days} day(s) of sleep data, ending yesterday...")
    sleep_records = get_sleep_data_range(garmin, backfill_days)
    print(f"Retrieved {len(sleep_records)} sleep record(s) from Garmin")

    created_count = 0
    skipped_existing = 0
    skipped_zero = 0

    for data in sleep_records:
        sleep_date = data.get("dailySleepDTO", {}).get("calendarDate")

        if not sleep_date:
            print("Skipped: No sleep date")
            continue

        if sleep_data_exists(client, database_id, sleep_date):
            print(f"Skipped (already exists): {sleep_date}")
            skipped_existing += 1
            continue

        if create_sleep_data(client, database_id, data, skip_zero_sleep=True):
            created_count += 1
        else:
            skipped_zero += 1

    print("\n=== Summary ===")
    print(f"Created:                 {created_count}")
    print(f"Skipped (already exist): {skipped_existing}")
    print(f"Skipped (zero sleep):    {skipped_zero}")


if __name__ == "__main__":
    main()
