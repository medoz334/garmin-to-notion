import os
import sys
from pathlib import Path

from garminconnect import Garmin

GARMIN_AUTH_ERROR_EXIT_CODE = 85
GARMIN_RATE_LIMIT_EXIT_CODE = 86

def _is_rate_limit_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "429" in message
        or "too many requests" in message
        or "rate limit" in message
        or "rate limited" in message
    )

def _is_auth_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "401" in message
        or "unauthorized" in message
        or "authentication" in message
        or "failed to retrieve social profile" in message
        or "invalid token" in message
        or "token expired" in message
        or "expired token" in message
        or "oauth" in message and "invalid" in message
        or "refresh" in message and "failed" in message
    )

def login_garmin() -> Garmin:
    """
    Stable Garmin login for GitHub Actions.

    Design:
    - Use saved token directory only.
    - Do NOT do fresh email/password login in GitHub Actions.
    - If token is invalid, stop the workflow.
    - If Garmin returns 429, stop immediately to avoid worsening account-level throttling.
    """

    token_dir = Path(os.path.expanduser(os.getenv("GARMIN_TOKEN_DIR", "~/.garminconnect")))
    token_file = token_dir / "garmin_tokens.json"

    if not token_file.exists() or token_file.stat().st_size == 0:
        print(f"::error::Garmin token file not found or empty: {token_file}")
        print("Regenerate Garmin tokens locally and update GARMIN_TOKENS_JSON secret.")
        sys.exit(GARMIN_AUTH_ERROR_EXIT_CODE)

    garmin = Garmin()

    try:
        garmin.login(str(token_dir))
        print(f"Logged in with saved Garmin tokens from {token_dir}")
        return garmin

    except Exception as error:
        if _is_rate_limit_error(error):
            print("::error::Garmin returned 429 / Too Many Requests.")
            print("Stopping immediately. Do not retry from GitHub Actions today.")
            print("Recommended action: wait 24-72 hours, then regenerate tokens locally.")
            print(f"Original error: {error}")
            sys.exit(GARMIN_RATE_LIMIT_EXIT_CODE)

        if _is_auth_error(error):
            print("::error::Garmin authentication failed with saved token.")
            print("Do not attempt fresh login from GitHub Actions.")
            print("Regenerate token locally, update GARMIN_TOKENS_JSON, then run workflow once manually.")
            print(f"Original error: {error}")
            sys.exit(GARMIN_AUTH_ERROR_EXIT_CODE)

        print("::error::Unexpected Garmin login error.")
        print(f"Original error: {error}")
        raise
