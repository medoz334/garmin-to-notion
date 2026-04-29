def main():
    load_dotenv()

    # Initialize Notion client and target database
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_STEPS_DB_ID")

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

    daily_steps = get_all_daily_steps(garmin)
    for steps in daily_steps:
        steps_date = steps.get('calendarDate')
        existing_steps = daily_steps_exist(client, database_id, steps_date)
        if existing_steps:
            if steps_need_update(existing_steps, steps):
                update_daily_steps(client, existing_steps, steps)
        else:
            create_daily_steps(client, database_id, steps)

if __name__ == '__main__':
    main()
