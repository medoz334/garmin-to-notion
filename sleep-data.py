from datetime import datetime, date, timedelta
from garminconnect import Garmin
from notion_client import Client
from dotenv import load_dotenv
import pytz
import os

# Constants
local_tz = pytz.timezone("Asia/Tokyo")


def get_sleep_data_range(garmin, days_back: int):
    """
    Fetch sleep data for the last N days, ending with yesterday.
    Today is excluded because Garmin may not have synced it yet when the workflow runs in the morning.
    """
    end_date = date.today() - timedelta(days=1)  # yesterday
    start_date = end_date - timedelta(days=days_back - 1)
    daterange = [start_date + timedelta(days=x) for x in range(days_back)]

    sleep_records = []
    for d in daterange:
        try:
            data = garmin.get_sleep_data(d.isoformat())
            if data:
                sleep_records.append(data)
        except Exception as e:
            print(f"Error fetching sleep for {d.isoformat()}: {e}")
    return sleep_records


def format_duration(seconds):
    minutes = (seconds or 0) // 60
    return f"{minutes // 60}h {minutes % 60}m"


def format_time(timestamp):
    return (
        datetime.utcfromtimestamp(timestamp / 1000).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if timestamp else None
    )


def format_time_readable(timestamp):
    return (
        datetime.fromtimestamp(timestamp / 1000, local_tz).strftime("%H:%M")
        if timestamp else "Unknown"
    )


def format_date_for_name(sleep_date):
    return datetime.strptime(sleep_date, "%Y-%m-%d").strftime("%d.%m.%Y") if sleep_date else "Unknown"


def sleep_data_exists(client, database_id, sleep_date):
    query = client.databases.query(
        database_id=database_id,
        filter={"property": "Long Date", "date": {"equals": sleep_date}}
    )
    results = query.get('results', [])
    return results[0] if results else None


def create_sleep_data(client, database_id, sleep_data, skip_zero_sleep=True):
    daily_sleep = sleep_data.get('dailySleepDTO', {})
    if not daily_sleep:
        return False

    sleep_date = daily_sleep.get('calendarDate', "Unknown Date")
    total_sleep = sum(
        (daily_sleep.get(k, 0) or 0) for k in ['deepSleepSeconds', 'lightSleepSeconds', 'remSleepSeconds']
    )

    if skip_zero_sleep and total_sleep == 0:
        print(f"Skipping sleep data for {sleep_date} as total sleep is 0")
        return False

    properties = {
        "Date": {"title": [{"text": {"content": format_date_for_name(sleep_date)}}]},
        "Times": {"rich_text": [{"text": {"content": f"{format_time_readable(daily_sleep.get('sleepStartTimestampGMT'))} → {format_time_readable(daily_sleep.get('sleepEndTimestampGMT'))}"}}]},
        "Long Date": {"date": {"start": sleep_date}},
        "Full Date/Time": {"date": {"start": format_time(daily_sleep.get('sleepStartTimestampGMT')), "end": format_time(daily_sleep.get('sleepEndTimestampGMT'))}},
        "Total Sleep (h)": {"number": round(total_sleep / 3600, 1)},
        "Light Sleep (h)": {"number": round(daily_sleep.get('lightSleepSeconds', 0) / 3600, 1)},
        "Deep Sleep (h)": {"number": round(daily_sleep.get('deepSleepSeconds', 0) / 3600, 1)},
        "REM Sleep (h)": {"number": round(daily_sleep.get('remSleepSeconds', 0) / 3600, 1)},
        "Awake Time (h)": {"number": round(daily_sleep.get('awakeSleepSeconds', 0) / 3600, 1)},
        "Total Sleep": {"rich_text": [{"text": {"content": format_duration(total_sleep)}}]},
        "Light Sleep": {"rich_text": [{"text": {"content": format_duration(daily_sleep.get('lightSleepSeconds', 0))}}]},
        "Deep Sleep": {"rich_text": [{"text": {"content": format_duration(daily_sleep.get('deepSleepSeconds', 0))}}]},
        "REM Sleep": {"rich_text": [{"text": {"content": format_duration(daily_sleep.get('remSleepSeconds', 0))}}]},
        "Awake Time": {"rich_text": [{"text": {"content": format_duration(daily_sleep.get('awakeSleepSeconds', 0))}}]},
        "Resting HR": {"number": sleep_data.get('restingHeartRate', 0)}
    }

    client.pages.create(parent={"database_id": database_id}, properties=properties, icon={"emoji": "😴"})
    print(f"Created sleep entry for: {sleep_date}")
    return True


def main():
    load_dotenv()

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_SLEEP_DB_ID")
    backfill_days = int(os.getenv("GARMIN_SLEEP_BACKFILL_DAYS") or "1")

    # --- Garmin login using token string from env var ---
    garmin = Garmin()
    garmin.login(os.getenv("GARMIN_TOKENS_JSON"))
    print("Logged in with saved tokens (from env var)")
    # ------------------------------------------------------

    client = Client(auth=notion_token)

    print(f"Fetching last {backfill_days} day(s) of sleep data (ending yesterday)...")
    sleep_records = get_sleep_data_range(garmin, backfill_days)
    print(f"Retrieved {len(sleep_records)} sleep record(s) from Garmin")

    created_count = 0
    skipped_existing = 0
    skipped_zero = 0
    for data in sleep_records:
        sleep_date = data.get('dailySleepDTO', {}).get('calendarDate')
        if not sleep_date:
            continue
        if sleep_data_exists(client, database_id, sleep_date):
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


if __name__ == '__main__':
    main()
