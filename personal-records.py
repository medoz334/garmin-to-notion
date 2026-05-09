from datetime import date, datetime
from notion_client import Client
from garmin_auth import login_garmin
import os


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def format_activity_type(activity_type: str) -> str:
    mapping = {
        "running": "Running",
        "cycling": "Cycling",
        "indoor_cycling": "Indoor Cycling",
        "swimming": "Swimming",
        "walking": "Walking",
        "hiking": "Hiking",
    }
    return mapping.get((activity_type or "").lower(), activity_type or "Unknown")


def replace_activity_name_by_typeId(typeId: int) -> str:
    typeId_name_map = {
        1: "1K",
        2: "1mi",
        3: "5K",
        4: "10K",
        7: "Longest Run",
        8: "Longest Ride",
        9: "Total Ascent",
        10: "Max Avg Power (20 min)",
        12: "Most Steps in a Day",
        13: "Most Steps in a Week",
        14: "Most Steps in a Month",
        15: "Longest Goal Streak",
    }
    return typeId_name_map.get(typeId, "Unnamed Activity")


def format_garmin_value(value, activity_type: str, type_id: int):
    """Return (value_str, pace_str). Both are strings for rich_text fields."""
    if value is None:
        return "", ""

    if type_id == 1:  # 1K
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"
        pace = f"{minutes}:{seconds:02d} /km"
        return formatted_value, pace

    if type_id == 2:  # 1mi
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"

        total_pseconds = total_seconds / 1.60934
        pminutes = int(total_pseconds // 60)
        pseconds = int(total_pseconds % 60)
        formatted_pace = f"{pminutes}:{pseconds:02d} /km"

        return formatted_value, formatted_pace

    if type_id == 3:  # 5K
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"

        total_pseconds = total_seconds // 5
        pminutes = total_pseconds // 60
        pseconds = total_pseconds % 60
        formatted_pace = f"{pminutes}:{pseconds:02d} /km"

        return formatted_value, formatted_pace

    if type_id == 4:  # 10K
        total_seconds = round(value)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            formatted_value = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            formatted_value = f"{minutes}:{seconds:02d}"

        total_pseconds = total_seconds // 10
        pminutes = total_pseconds // 60
        pseconds = total_pseconds % 60
        formatted_pace = f"{pminutes}:{pseconds:02d} /km"

        return formatted_value, formatted_pace

    if type_id in [7, 8]:  # Longest Run, Longest Ride
        value_km = value / 1000
        formatted_value = f"{value_km:.2f} km"
        return formatted_value, ""

    if type_id == 9:  # Total Ascent
        value_m = int(value)
        formatted_value = f"{value_m:,} m"
        return formatted_value, ""

    if type_id == 10:  # Max Avg Power
        value_w = round(value)
        formatted_value = f"{value_w} W"
        return formatted_value, ""

    if type_id in [12, 13, 14]:  # Step counts
        value_steps = round(value)
        formatted_value = f"{value_steps:,}"
        return formatted_value, ""

    if type_id == 15:  # Longest Goal Streak
        value_days = round(value)
        formatted_value = f"{value_days} days"
        return formatted_value, ""

    return str(value), ""


# ---------------------------------------------------------------------------
# Notion helpers
# ---------------------------------------------------------------------------

def get_existing_record(client, database_id: str, activity_name: str):
    """Get the current PR record (PR=True) for this activity name."""
    response = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {
                    "property": "Record",
                    "title": {"equals": activity_name}
                },
                {
                    "property": "PR",
                    "checkbox": {"equals": True}
                }
            ]
        }
    )
    results = response.get("results", [])
    return results[0] if results else None


def get_record_by_date_and_name(client, database_id: str, activity_date: str, activity_name: str):
    """Get a record matching both date and activity name."""
    response = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {
                    "property": "Date",
                    "date": {"equals": activity_date}
                },
                {
                    "property": "Record",
                    "title": {"equals": activity_name}
                }
            ]
        }
    )
    results = response.get("results", [])
    return results[0] if results else None


def write_new_record(client, database_id, activity_date, activity_type, activity_name, type_id, value_str, pace_str):
    properties = {
        "Record": {
            "title": [{"text": {"content": activity_name}}]
        },
        "Activity Type": {
            "select": {"name": activity_type}
        },
        "Date": {
            "date": {"start": activity_date}
        },
        "PR": {
            "checkbox": True
        },
        "typeId": {
            "number": type_id
        },
    }

    if value_str:
        properties["Value"] = {
            "rich_text": [{"text": {"content": value_str}}]
        }

    if pace_str:
        properties["Pace"] = {
            "rich_text": [{"text": {"content": pace_str}}]
        }

    client.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )


def update_record(client, page_id, activity_date, value_str, pace_str, activity_name, is_pr: bool):
    properties = {
        "PR": {"checkbox": is_pr}
    }

    if activity_date:
        properties["Date"] = {"date": {"start": activity_date}}

    if value_str is not None:
        properties["Value"] = {
            "rich_text": [{"text": {"content": value_str}}]
        }

    if pace_str:
        properties["Pace"] = {
            "rich_text": [{"text": {"content": pace_str}}]
        }

    client.pages.update(page_id=page_id, properties=properties)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_PR_DB_ID")

    garmin = login_garmin()
    client = Client(auth=notion_token)

    records = garmin.get_personal_record()
    filtered_records = [record for record in records if record.get('typeId') != 16]

    for record in filtered_records:
        activity_date = record.get('prStartTimeGmtFormatted')
        activity_type = format_activity_type(record.get('activityType'))
        typeId = record.get('typeId', 0)
        activity_name = replace_activity_name_by_typeId(typeId)
        value_str, pace_str = format_garmin_value(record.get('value', 0), activity_type, typeId)

        existing_pr_record = get_existing_record(client, database_id, activity_name)
        existing_date_record = get_record_by_date_and_name(client, database_id, activity_date, activity_name)

        if existing_date_record:
            update_record(client, existing_date_record['id'], activity_date, value_str, pace_str, activity_name, True)
            print(f"Updated existing record: {activity_type} - {activity_name}")

        elif existing_pr_record:
            try:
                date_prop = existing_pr_record['properties']['Date']
                if date_prop and date_prop.get('date') and date_prop['date'].get('start'):
                    existing_date = date_prop['date']['start']

                    if activity_date > existing_date:
                        update_record(client, existing_pr_record['id'], existing_date, None, None, activity_name, False)
                        print(f"Archived old record: {activity_type} - {activity_name}")

                        write_new_record(
                            client,
                            database_id,
                            activity_date,
                            activity_type,
                            activity_name,
                            typeId,
                            value_str,
                            pace_str
                        )
                        print(f"Created new PR record: {activity_type} - {activity_name}")
                    else:
                        print(f"No update needed: {activity_type} - {activity_name}")
                else:
                    print(f"Warning: Record {activity_name} has invalid date format - updating anyway")
                    update_record(client, existing_pr_record['id'], activity_date, value_str, pace_str, activity_name, True)

            except (KeyError, TypeError) as e:
                print(f"Error processing record {activity_name}: {e}")
                print(f"Record data: {existing_pr_record['properties']}")
                write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value_str, pace_str)

        else:
            write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value_str, pace_str)
            print(f"Successfully written new record: {activity_type} - {activity_name}")


if __name__ == "__main__":
    main()
