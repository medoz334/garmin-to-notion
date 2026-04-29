def main():
    load_dotenv()

    # Initialize Notion client and target database
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_SLEEP_DB_ID")

    # --- Garmin login using saved tokens (DI OAuth format, garminconnect>=0.3.2) ---
    # CI: ~/.garminconnect/garmin_tokens.json is restored from the GARMIN_TOKENS_JSON
    #     GitHub Secret before this script runs (see workflow yml).
    # Local: run generate_token.py once with widget+cffi to populate the same path.
    # If login fails here, regenerate tokens locally and update the Secret —
    # do NOT attempt a fresh SSO login from CI (will be rate-limited as 429).
    token_dir = os.path.expanduser(os.getenv("GARMIN_TOKEN_DIR", "~/.garminconnect"))
    garmin = Garmin()
    garmin.login(token_dir)
    print(f"Logged in with saved tokens from {token_dir}")
    # -------------------------------------------------------------------------------

    client = Client(auth=notion_token)

    data = get_sleep_data(garmin)
    if data:
        sleep_date = data.get('dailySleepDTO', {}).get('calendarDate')
        if sleep_date and not sleep_data_exists(client, database_id, sleep_date):
            create_sleep_data(client, database_id, data, skip_zero_sleep=True)

if __name__ == '__main__':
    main()
