import getpass
import os
from pathlib import Path

from garminconnect import Garmin

def main():
    token_dir = Path(os.path.expanduser("~/.garminconnect"))
    token_dir.mkdir(parents=True, exist_ok=True)

    token_file = token_dir / "garmin_tokens.json"

    if token_file.exists():
        print(f"Existing token file found: {token_file}")
        answer = input("Delete existing token and regenerate? [y/N]: ").strip().lower()
        if answer == "y":
            token_file.unlink()
            print("Existing token deleted.")
        else:
            print("Canceled.")
            return

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")

    def prompt_mfa():
        return input("MFA code, if requested: ").strip()

    garmin = Garmin(
        email=email,
        password=password,
        prompt_mfa=prompt_mfa,
    )

    print("Logging in to Garmin locally...")
    garmin.login(str(token_dir))

    if not token_file.exists() or token_file.stat().st_size == 0:
        raise FileNotFoundError(f"Token file was not created or is empty: {token_file}")

    print()
    print("Garmin token generated successfully.")
    print(f"Token file: {token_file}")
    print()
    print("=== Copy everything below into GitHub Secret: GARMIN_TOKENS_JSON ===")
    print(token_file.read_text())
    print("=== End ===")

if __name__ == "__main__":
    main()
