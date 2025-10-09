#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

def main() -> None:
    raw = os.environ.get("PAYLOAD", "")
    if not raw.strip():
        print("PAYLOAD env variable is empty", file=sys.stderr)
        sys.exit(1)

    issue_number: Optional[int] = None
    payload = raw
    author = ""
    created_at_raw = ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        pass
    else:
        payload = data.get("payload", "")
        issue_number = data.get("number")
        author = (data.get("author") or "").strip()
        created_at_raw = (data.get("created_at") or "").strip()

    payload = payload.strip()
    if payload.startswith("/add-video"):
        payload = payload[len("/add-video"):].strip()

    parsed: Dict[str, str] = {}
    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key_part, value_part = line.split("=", 1)
        key = key_part.strip().lower()
        value = value_part.strip()
        if value.startswith(("\"", "'")) and value.endswith(("\"", "'")) and len(value) >= 2:
            value = value[1:-1].strip()
        parsed[key] = value

    required = ["link", "title", "channel"]
    missing = [k for k in required if not parsed.get(k)]
    if missing:
        print(
            "Missing fields: " + ", ".join(missing)
            + '. Expected format:\\n/add-video\\nLINK = ...\\nTITLE = ...\\nCHANNEL = ...',
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
        if not author:
            print("Не удалось определить автора issue/comment для заполнения submitted_by.", file=sys.stderr)
            sys.exit(1)
        submitter = author.rstrip("/").split("/")[-1].lstrip("@")
        if not submitter:
            print("Переданный логин автора пустой после нормализации.", file=sys.stderr)
            sys.exit(1)
        fh.write(f"SUBMITTER={submitter}\n")

        if not created_at_raw:
            print("Не удалось определить дату создания issue.", file=sys.stderr)
            sys.exit(1)
        try:
            created_dt = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
        except ValueError:
            print(f"Некорректная дата создания issue: {created_at_raw}", file=sys.stderr)
            sys.exit(1)
        fh.write(f"ADDED_AT={created_dt.date().isoformat()}\n")


if __name__ == "__main__":
    main()
