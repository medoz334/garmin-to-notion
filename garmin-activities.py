def main():
    load_dotenv()

    # Initialize Notion client and fetch settings
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DB_ID")
    garmin_fetch_limit = int(os.getenv("GARMIN_ACTIVITIES_FETCH_LIMIT") or "1000")

    # --- Garmin login using saved tokens (DI OAuth format, garminconnect>=0.3.2) ---
    # CI: ~/.garminconnect/garmin_tokens.json is restored from the GARMIN_TOKENS_JSON
    #     GitHub Secret before this script runs (see workflow yml).
    # Local: run generate_token.py once with widget+cffi to populate the same path.
    # Tokens auto-refresh via DI OAuth, so the Secret typically needs updating only
    # ~yearly. If login fails here, regenerate tokens locally and update the Secret
    # — do NOT attempt a fresh SSO login from CI (will be rate-limited as 429).
    token_dir = os.path.expanduser(os.getenv("GARMIN_TOKEN_DIR", "~/.garminconnect"))
    garmin_client = GarminClient()
    garmin_client.login(token_dir)
    print(f"Logged in with saved tokens from {token_dir}")
    # -------------------------------------------------------------------------------

    notion_client = NotionClient(auth=notion_token)

    # Get all activities
    activities = get_all_activities(garmin_client, garmin_fetch_limit)

    # Process all activities
    for activity in activities:
        activity_date_raw: str = activity.get('startTimeGMT')
        activity_date: datetime = (
            datetime
            .strptime(activity_date_raw, '%Y-%m-%d %H:%M:%S')
            .replace(tzinfo=UTC)
        )

        activity_name = format_entertainment(activity.get('activityName', 'Unnamed Activity'))
        activity_type, activity_subtype = format_activity_type(
            activity.get('activityType', {}).get('typeKey', 'Unknown'),
            activity_name
        )

        existing_activity = activity_exists(notion_client, database_id, activity_date, activity_type, activity_name)

        if existing_activity:
            if activity_needs_update(existing_activity, activity):
                update_activity(notion_client, existing_activity, activity)
        else:
            create_activity(notion_client, database_id, activity)

if __name__ == '__main__':
    main()
