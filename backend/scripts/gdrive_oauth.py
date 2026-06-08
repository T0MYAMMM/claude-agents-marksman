"""One-time OAuth consent flow to authorize Drive uploads as the user.

Runs the installed-app (Desktop) flow: opens a browser for consent, then writes a
reusable token (with refresh token) to disk. The backend then uploads to the user's
Drive as the user — sidestepping the service-account storage-quota limitation.

Usage:
    python -m scripts.gdrive_oauth \
        --client-secret /secrets/oauth-client.json \
        --token /secrets/oauth-token.json \
        [--port 8765]

The token path must match APP_GDRIVE_OAUTH_TOKEN_PATH in the backend env.
"""

import argparse
from pathlib import Path

from app.services.gdrive import OAUTH_SCOPES


def main() -> int:
    """Run the consent flow and persist the authorized-user token."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-secret", required=True, help="Path to client_secret JSON")
    parser.add_argument("--token", required=True, help="Output path for the authorized token")
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Loopback port for the OAuth redirect (must be free)",
    )
    args = parser.parse_args()

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, OAUTH_SCOPES)
    # Desktop clients use a loopback redirect; this prints a URL and waits for the code.
    creds = flow.run_local_server(port=args.port, open_browser=False, prompt="consent")

    out = Path(args.token)
    out.write_text(creds.to_json())
    print(f"\n✓ Token written to {out}")
    print("  Set APP_GDRIVE_OAUTH_TOKEN_PATH to this path and restart the backend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
