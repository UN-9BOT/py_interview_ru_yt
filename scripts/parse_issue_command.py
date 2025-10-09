#!/usr/bin/env python3
import json
import os
import shlex
import sys
from typing import Dict, Optional

DEFAULT_SUBMITTER = "UN-9BOT"


def main() -> None:
    raw = os.environ.get("PAYLOAD", "")
    if not raw.strip():
        print("PAYLOAD env variable is empty", file=sys.stderr)
        sys.exit(1)

    issue_number: Optional[int] = None
    payload = raw
    author = ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pass
    else:
        payload = data.get("payload", "")
        issue_number = data.get("number")
        author = (data.get("author") or "").strip() or ""

    payload = payload.strip()
    if payload.startswith("/add-video"):
        payload = payload[len("/add-video"):].strip()

    parsed: Dict[str, str] = {}
    for token in shlex.split(payload):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        parsed[key] = value

    required = ["link", "title", "channel"]
    missing = [k for k in required if not parsed.get(k)]
    if missing:
        print(
            "Missing fields: " + ", ".join(missing)
            + '. Expected /add-video link="..." title="..." channel="..."',
            file=sys.stderr,
        )
        sys.exit(1)

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        for key in required:
            fh.write(f"{key.upper()}={parsed[key].strip()}\n")
        if issue_number is not None:
            fh.write(f"ISSUE_NUMBER={issue_number}\n")
        else:
            fh.write("ISSUE_NUMBER=\n")
        raw_submitter = author or DEFAULT_SUBMITTER
        submitter = raw_submitter.rstrip("/").split("/")[-1].lstrip("@") or DEFAULT_SUBMITTER
        fh.write(f"SUBMITTER={submitter}\n")


if __name__ == "__main__":
    main()
