"""Smoke-test Google Drive credentials end to end.

Uploads a tiny Markdown file to a folder, reads it back, and reports the result.
Run after configuring APP_GDRIVE_CREDENTIALS_PATH or APP_GDRIVE_CREDENTIALS_JSON.

Usage:
    python -m scripts.verify_gdrive <gdrive_folder_id>

Exits 0 on success, 1 on failure. Surfaces the two common setup mistakes:
folder not shared with the service account, or the Drive API not enabled.
"""

import sys

from app.services.gdrive import GDriveClient, GDriveError


def main() -> int:
    """Upload and read back a probe file in the given Drive folder."""
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    folder_id = sys.argv[1]

    client = GDriveClient()
    try:
        meta = client.upload_markdown(folder_id, "orchestrator-probe.md", "# probe\nok\n")
        print(f"✓ upload ok: file_id={meta['gdrive_file_id']}")
        content = client.fetch_markdown(meta["gdrive_file_id"])
        assert "probe" in content, "round-trip content mismatch"
        print(f"✓ read-back ok: {len(content)} bytes")
        print(f"  web view: {meta.get('web_view_link') or '(none)'}")
        print("\nDrive credentials are working.")
        return 0
    except GDriveError as exc:
        print(f"✗ Drive misconfigured: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 - surface the raw Google error verbatim
        print(f"✗ Drive call failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "\nCommon causes:\n"
            "  - The folder is not shared with the service account's client_email (Editor)\n"
            "  - The Drive API is not enabled in the GCP project\n"
            "  - The folder ID is wrong",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
