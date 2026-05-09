import os
from datetime import datetime, UTC, timedelta

from dotenv import load_dotenv
from notion_client import Client as NotionClient
from garmin_auth import login_garmin

ACTIVITY_ICONS = {
    "Barre": "https://img.icons8.com/?size=100&id=66924&format=png&color=000000",
    "Breathwork": "https://img.icons8.com/?size=100&id=9798&format=png&color=000000",
    "Cardio": "https://img.icons8.com/?size=100&id=71221&format=png&color=000000",
    "Cycling": "https://img.icons8.com/?size=100&id=47443&format=png&color=000000",
    "Hiking": "https://img.icons8.com/?size=100&id=9844&format=png&color=000000",
    "Indoor Cardio": "https://img.icons8.com/?size=100&id=62779&format=png&color=000000",
    "Indoor Cycling": "https://img.icons8.com/?size=100&id=47443&format=png&color=000000",
    "Indoor Rowing": "https://img.icons8.com/?size=100&id=71098&format=png&color=000000",
    "Pilates": "https://img.icons8.com/?size=100&id=9774&format=png&color=000000",
    "Meditation": "https://img.icons8.com/?size=100&id=9798&format=png&color=000000",
    "Rowing": "https://img.icons8.com/?size=100&id=71491&format=png&color=000000",
    "Running": "https://img.icons8.com/?size=100&id=k1l1XFkME39t&format=png&color=000000",
    "Strength Training": "https://img.icons8.com/?size=100&id=107640&format=png&color=000000",
    "Stretching": "https://img.icons8.com/?size=100&id=djfOcRn1m_kh&format=png&color=000000",
    "Swimming": "https://img.icons8.com/?size=100&id=9777&format=png&color=000000",
    "Treadmill Running": "https://img.icons8.com/?size=100&id=9794&format=png&color=000000",
    "Walking": "https://img.icons8.com/?size=100&id=9807&format=png&color=000000",
    "Yoga": "https://img.icons8.com/?size=100&id=9783&format=png&color=000000",
}


def get_all_activities(garmin_client, limit: int = 1000) -> list[dict]:
    return garmin_client.get_activities(0, limit)


def format_activity_type(activity_type: str, activity_name: str = "") -> tuple[str, str]:
    formatted_type = activity_type.replace("_", " ").title() if activity_type else "Unknown"
    activity_subtype = formatted_type
    activity_type = formatted_type

    activity_mapping = {
        "Barre": "Strength",
        "Indoor Cardio": "Cardio",
        "Indoor Cycling": "Cycling",
        "Indoor Rowing": "Rowing",
        "Speed Walking": "Walking",
        "Strength Training": "Strength",
        "Treadmill Running": "Running",
    }

    if formatted_type == "Rowing V2":
        activity_type = "Rowing"
    elif formatted_type in ["Yoga", "Pilates"]:
        activity_type = "Yoga/Pilates"
        activity_subtype = formatted_type

    if formatted_type in activity_mapping:
        activity_type = activity_mapping[formatted_type]
        activity_subtype = formatted_type

    if activity_name and "meditation" in activity_name.lower():
        return "Meditation", "Meditation"
    if activity_name and "barre" in activity_name.lower():
        return "Strength", "Barre"
    if activity_name and "stretch" in activity_name.lower():
        return "Stretching", "Stretching"

    return activity_type, activity_subtype


def format_entertainment(activity_name: str) -> str:
    return activity_name.replace("ENTERTAINMENT", "Netflix")


def format_training_message(message: str) -> str:
    messages = {
        "NO_": "No Benefit",
        "MINOR_": "Some Benefit",
        "RECOVERY_": "Recovery",
        "MAINTAINING_": "Maintaining",
        "IMPROVING_": "Impacting",
        "IMPACTING_": "Impacting",
        "HIGHLY_": "Highly Impacting",
        "OVERREACHING_": "Overreaching",
    }

    for key, value in messages.items():
        if message.startswith(key):
            return value

    return message


def format_training_effect(training_effect_label: str) -> str:
    return training_effect_label.replace("_", " ").title()


def format_pace(average_speed: float) -> str:
    if average_speed > 0:
        pace_min_km = 1000 / (average_speed * 60)
        minutes = int(pace_min_km)
        seconds = int((pace_min_km - minutes) * 60)
        return f"{minutes}:{seconds:02d} min/km"

    return ""


def activity_exists(notion_client, database_id, activity_date, activity_type, activity_name):
    lookup_type = "Stretching" if "stretch" in activity_name.lower() else activity_type
    lookup_min_date = activity_date - timedelta(minutes=5)
    lookup_max_date = activity_date + timedelta(minutes=5)

    query = notion_client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Date", "date": {"on_or_after": lookup_min_date.isoformat()}},
                {"property": "Date", "date": {"on_or_before": lookup_max_date.isoformat()}},
                {"property": "Activity Type", "select": {"equals": lookup_type}},
                {"property": "Activity Name", "title": {"equals": activity_name}},
            ]
        },
    )

    results = query["results"]
    return results[0] if results else None


def _get_rich_text_plain_text(properties, property_name):
    rich_text_items = properties.get(property_name, {}).get("rich_text", [])
    if not rich_text_items:
        return ""
    return rich_text_items[0].get("plain_text") or rich_text_items[0].get("text", {}).get("content", "")


def _get_select_name(properties, property_name):
    select_value = properties.get(property_name, {}).get("select")
    if not select_value:
        return ""
    return select_value.get("name", "")


def activity_needs_update(existing_activity, new_activity):
    existing_props = existing_activity["properties"]

    activity_name = new_activity.get("activityName", "")
    activity_type, activity_subtype = format_activity_type(
        new_activity.get("activityType", {}).get("typeKey", "Unknown"),
        activity_name,
    )

    existing_distance = existing_props.get("Distance (km)", {}).get("number")
    existing_duration = existing_props.get("Duration (min)", {}).get("number")
    existing_calories = existing_props.get("Calories", {}).get("number")
    existing_avg_pace = _get_rich_text_plain_text(existing_props, "Avg Pace")
    existing_avg_power = existing_props.get("Avg Power", {}).get("number")
    existing_max_power = existing_props.get("Max Power", {}).get("number")
    existing_training_effect = _get_select_name(existing_props, "Training Effect")
    existing_aerobic = existing_props.get("Aerobic", {}).get("number")
    existing_aerobic_effect = _get_select_name(existing_props, "Aerobic Effect")
    existing_anaerobic = existing_props.get("Anaerobic", {}).get("number")
    existing_anaerobic_effect = _get_select_name(existing_props, "Anaerobic Effect")
    existing_pr = existing_props.get("PR", {}).get("checkbox")
    existing_fav = existing_props.get("Fav", {}).get("checkbox")
    existing_activity_type = _get_select_name(existing_props, "Activity Type")
    existing_subactivity_type = _get_select_name(existing_props, "Subactivity Type")

    return (
        existing_distance != round(new_activity.get("distance", 0) / 1000, 2)
        or existing_duration != round(new_activity.get("duration", 0) / 60, 2)
        or existing_calories != round(new_activity.get("calories", 0))
        or existing_avg_pace != format_pace(new_activity.get("averageSpeed", 0))
        or existing_avg_power != round(new_activity.get("avgPower", 0), 1)
        or existing_max_power != round(new_activity.get("maxPower", 0), 1)
        or existing_training_effect != format_training_effect(new_activity.get("trainingEffectLabel", "Unknown"))
        or existing_aerobic != round(new_activity.get("aerobicTrainingEffect", 0), 1)
        or existing_aerobic_effect != format_training_message(new_activity.get("aerobicTrainingEffectMessage", "Unknown"))
        or existing_anaerobic != round(new_activity.get("anaerobicTrainingEffect", 0), 1)
        or existing_anaerobic_effect != format_training_message(new_activity.get("anaerobicTrainingEffectMessage", "Unknown"))
        or existing_pr != new_activity.get("pr", False)
        or existing_fav != new_activity.get("favorite", False)
        or existing_activity_type != activity_type
        or existing_subactivity_type != activity_subtype
    )


def create_activity(notion_client, database_id, activity):
    activity_date_raw = activity.get("startTimeGMT")
    activity_date = (
        datetime
        .strptime(activity_date_raw, "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=UTC)
        .isoformat()
    )

    activity_name = format_entertainment(activity.get("activityName", "Unnamed Activity"))
    activity_type, activity_subtype = format_activity_type(
        activity.get("activityType", {}).get("typeKey", "Unknown"),
        activity_name,
    )

    icon_url = ACTIVITY_ICONS.get(activity_subtype if activity_subtype != activity_type else activity_type)

    properties = {
        "Date": {"date": {"start": activity_date}},
        "Activity Type": {"select": {"name": activity_type}},
        "Subactivity Type": {"select": {"name": activity_subtype}},
        "Activity Name": {"title": [{"text": {"content": activity_name}}]},
        "Distance (km)": {"number": round(activity.get("distance", 0) / 1000, 2)},
        "Duration (min)": {"number": round(activity.get("duration", 0) / 60, 2)},
        "Calories": {"number": round(activity.get("calories", 0))},
        "Avg Pace": {"rich_text": [{"text": {"content": format_pace(activity.get("averageSpeed", 0))}}]},
        "Avg Power": {"number": round(activity.get("avgPower", 0), 1)},
        "Max Power": {"number": round(activity.get("maxPower", 0), 1)},
        "Training Effect": {"select": {"name": format_training_effect(activity.get("trainingEffectLabel", "Unknown"))}},
        "Aerobic": {"number": round(activity.get("aerobicTrainingEffect", 0), 1)},
        "Aerobic Effect": {"select": {"name": format_training_message(activity.get("aerobicTrainingEffectMessage", "Unknown"))}},
        "Anaerobic": {"number": round(activity.get("anaerobicTrainingEffect", 0), 1)},
        "Anaerobic Effect": {"select": {"name": format_training_message(activity.get("anaerobicTrainingEffectMessage", "Unknown"))}},
        "PR": {"checkbox": activity.get("pr", False)},
        "Fav": {"checkbox": activity.get("favorite", False)},
    }

    page = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    if icon_url:
        page["icon"] = {"type": "external", "external": {"url": icon_url}}

    notion_client.pages.create(**page)


def update_activity(notion_client, existing_activity, new_activity):
    activity_name = format_entertainment(new_activity.get("activityName", "Unnamed Activity"))
    activity_type, activity_subtype = format_activity_type(
        new_activity.get("activityType", {}).get("typeKey", "Unknown"),
        activity_name,
    )

    icon_url = ACTIVITY_ICONS.get(activity_subtype if activity_subtype != activity_type else activity_type)

    properties = {
        "Activity Type": {"select": {"name": activity_type}},
        "Subactivity Type": {"select": {"name": activity_subtype}},
        "Distance (km)": {"number": round(new_activity.get("distance", 0) / 1000, 2)},
        "Duration (min)": {"number": round(new_activity.get("duration", 0) / 60, 2)},
        "Calories": {"number": round(new_activity.get("calories", 0))},
        "Avg Pace": {"rich_text": [{"text": {"content": format_pace(new_activity.get("averageSpeed", 0))}}]},
        "Avg Power": {"number": round(new_activity.get("avgPower", 0), 1)},
        "Max Power": {"number": round(new_activity.get("maxPower", 0), 1)},
        "Training Effect": {"select": {"name": format_training_effect(new_activity.get("trainingEffectLabel", "Unknown"))}},
        "Aerobic": {"number": round(new_activity.get("aerobicTrainingEffect", 0), 1)},
        "Aerobic Effect": {"select": {"name": format_training_message(new_activity.get("aerobicTrainingEffectMessage", "Unknown"))}},
        "Anaerobic": {"number": round(new_activity.get("anaerobicTrainingEffect", 0), 1)},
        "Anaerobic Effect": {"select": {"name": format_training_message(new_activity.get("anaerobicTrainingEffectMessage", "Unknown"))}},
        "PR": {"checkbox": new_activity.get("pr", False)},
        "Fav": {"checkbox": new_activity.get("favorite", False)},
    }

    update = {
        "page_id": existing_activity["id"],
        "properties": properties,
    }

    if icon_url:
        update["icon"] = {"type": "external", "external": {"url": icon_url}}

    notion_client.pages.update(**update)


def main():
    load_dotenv()

    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")
    garmin_fetch_limit = int(os.getenv("GARMIN_ACTIVITIES_FETCH_LIMIT") or "1000")

    garmin_client = login_garmin()
    notion_client = NotionClient(auth=notion_token)

    activities = get_all_activities(garmin_client, garmin_fetch_limit)

    for activity in activities:
        activity_date_raw = activity.get("startTimeGMT")

        if not activity_date_raw:
            print("Skipping activity because startTimeGMT is missing")
            continue

        activity_date = (
            datetime
            .strptime(activity_date_raw, "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=UTC)
        )

        activity_name = format_entertainment(activity.get("activityName", "Unnamed Activity"))
        activity_type, activity_subtype = format_activity_type(
            activity.get("activityType", {}).get("typeKey", "Unknown"),
            activity_name,
        )

        existing_activity = activity_exists(
            notion_client,
            database_id,
            activity_date,
            activity_type,
            activity_name,
        )

        if existing_activity:
            if activity_needs_update(existing_activity, activity):
                update_activity(notion_client, existing_activity, activity)
                print(f"Updated activity: {activity_name}")
            else:
                print(f"No update needed: {activity_name}")
        else:
            create_activity(notion_client, database_id, activity)
            print(f"Created activity: {activity_name}")


if __name__ == "__main__":
    main()
