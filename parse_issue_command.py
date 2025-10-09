#!/usr/bin/env python3
import os
import shlex
import sys


def main() -> None:
    payload = os.environ.get("PAYLOAD", "").strip()
    if not payload:
        print("PAYLOAD env variable is empty", file=sys.stderr)
        sys.exit(1)

    if payload.startswith("/add-video"):
        payload = payload[len("/add-video"):].strip()

    parsed: dict[str, str] = {}
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


if __name__ == "__main__":
    main()
