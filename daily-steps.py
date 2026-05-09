from datetime import date, timedelta
from notion_client import Client
from dotenv import load_dotenv
from garmin_auth import login_garmin
import os

def get_all_daily_steps(garmin):
    """
    Get last 7 days of daily step count data from Garmin Connect.
    Today is excluded because Garmin may not have synced it yet.
    """
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)

    daily_steps = []

    current_date = start_date
    while current_date <= end_date:
        try:
            daily_steps += garmin.get_daily_steps(
                current_date.isoformat(),
                current_date.isoformat()
            )
        except Exception as e:
            message = str(e).lower()

            if (
                "401" in message
                or "unauthorized" in message
                or "authentication" in message
                or "failed to retrieve social profile" in message
                or "429" in message
                or "too many requests" in message
                or "rate limit" in message
                or "rate limited" in message
            ):
                print(f"Critical Garmin error while fetching steps for {current_date.isoformat()}: {e}")
                raise

            print(f"Error fetching steps for {current_date.isoformat()}: {e}")

        current_date += timedelta(days=1)

    return daily_steps

def daily_steps_exist(client, database_id, activity_date):
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Date", "date": {"equals": activity_date}},
                {"property": "Activity Type", "title": {"equals": "Walking"}},
            ]
        },
    )

    results = query["results"]
    return results[0] if results else None

def steps_need_update(existing_steps, new_steps):
    existing_props = existing_steps["properties"]

    total_distance = new_steps.get("totalDistance")
    if total_distance is None:
        total_distance = 0

    new_total_distance_km = round(total_distance / 1000, 2)

    existing_activity_type = ""
    title_items = existing_props.get("Activity Type", {}).get("title", [])
    if title_items:
        existing_activity_type = title_items[0].get("plain_text", "")

    return (
        existing_props["Total Steps"]["number"] != new_steps.get("totalSteps")
        or existing_props["Step Goal"]["number"] != new_steps.get("stepGoal")
        or existing_props["Total Distance (km)"]["number"] != new_total_distance_km
        or existing_activity_type != "Walking"
    )

def update_daily_steps(client, existing_steps, new_steps):
    total_distance = new_steps.get("totalDistance")
    if total_distance is None:
        total_distance = 0

    properties = {
        "Activity Type": {"title": [{"text": {"content": "Walking"}}]},
        "Total Steps": {"number": new_steps.get("totalSteps")},
        "Step Goal": {"number": new_steps.get("stepGoal")},
        "Total Distance (km)": {"number": round(total_distance / 1000, 2)},
    }

    update = {
        "page_id": existing_steps["id"],
        "properties": properties,
    }

    client.pages.update(**update)

def create_daily_steps(client, database_id, steps):
    total_distance = steps.get("totalDistance")
    if total_distance is None:
        total_distance = 0

    properties = {
        "Activity Type": {"title": [{"text": {"content": "Walking"}}]},
        "Date": {"date": {"start": steps.get("calendarDate")}},
        "Total Steps": {"number": steps.get("totalSteps")},
        "Step Goal": {"number": steps.get("stepGoal")},
        "Total Distance (km)": {"number": round(total_distance / 1000, 2)},
    }

    page = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    client.pages.create(**page)

def main():
    load_dotenv()

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_STEPS_DB_ID")

    garmin = login_garmin()
    client = Client(auth=notion_token)

    daily_steps = get_all_daily_steps(garmin)

    for steps in daily_steps:
        steps_date = steps.get("calendarDate")
        existing_steps = daily_steps_exist(client, database_id, steps_date)

        if existing_steps:
            if steps_need_update(existing_steps, steps):
                update_daily_steps(client, existing_steps, steps)
        else:
            create_daily_steps(client, database_id, steps)

if __name__ == "__main__":
    main()
