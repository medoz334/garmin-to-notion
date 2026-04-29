def main():
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_PR_DB_ID")

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
    records = garmin.get_personal_record()
    filtered_records = [record for record in records if record.get('typeId') != 16]

    for record in filtered_records:
        activity_date = record.get('prStartTimeGmtFormatted')
        activity_type = format_activity_type(record.get('activityType'))
        activity_name = replace_activity_name_by_typeId(record.get('typeId'))
        typeId = record.get('typeId', 0)
        value, pace = format_garmin_value(record.get('value', 0), activity_type, typeId)

        existing_pr_record = get_existing_record(client, database_id, activity_name)
        existing_date_record = get_record_by_date_and_name(client, database_id, activity_date, activity_name)

        if existing_date_record:
            update_record(client, existing_date_record['id'], activity_date, value, pace, activity_name, True)
            print(f"Updated existing record: {activity_type} - {activity_name}")
        elif existing_pr_record:
            # Add error handling here
            try:
                date_prop = existing_pr_record['properties']['Date']
                if date_prop and date_prop.get('date') and date_prop['date'].get('start'):
                    existing_date = date_prop['date']['start']

                    if activity_date > existing_date:
                        update_record(client, existing_pr_record['id'], existing_date, None, None, activity_name, False)
                        print(f"Archived old record: {activity_type} - {activity_name}")

                        write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace)
                        print(f"Created new PR record: {activity_type} - {activity_name}")
                    else:
                        print(f"No update needed: {activity_type} - {activity_name}")
                else:
                    # Handle case where date is missing or improperly formatted
                    print(f"Warning: Record {activity_name} has invalid date format - updating anyway")
                    update_record(client, existing_pr_record['id'], activity_date, value, pace, activity_name, True)
            except (KeyError, TypeError) as e:
                print(f"Error processing record {activity_name}: {e}")
                print(f"Record data: {existing_pr_record['properties']}")
                # Fallback - create new record if we can't process the existing one properly
                write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace)
        else:
            write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace)
            print(f"Successfully written new record: {activity_type} - {activity_name}")

if __name__ == '__main__':
    main()
