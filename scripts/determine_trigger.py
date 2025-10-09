#!/usr/bin/env python3
import json
import os
from typing import Any


def write_output(should_run: bool, issue_mode: bool, raw_command: str = "") -> None:
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write(f"should_run={'true' if should_run else 'false'}\n")
        fh.write(f"issue_mode={'true' if issue_mode else 'false'}\n")
        if raw_command:
            fh.write("raw_command<<EOF\n")
            fh.write(raw_command)
            if not raw_command.endswith("\n"):
                fh.write("\n")
            fh.write("EOF\n")


def normalize_first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def main() -> None:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.exists(event_path):
        write_output(False, False)
        return

    with open(event_path, encoding="utf-8") as fh:
        event: dict[str, Any] = json.load(fh)

    if event_name == "issues":
        issue = event.get("issue", {}) or {}
        body = issue.get("body") or ""
        if normalize_first_line(body) == "/add-video":
            issue_number = issue.get("number")
            command_json = json.dumps(
                {"number": issue_number, "payload": body},
                ensure_ascii=False,
            )
            write_output(True, True, command_json)
            return
        write_output(False, False)
        return

    if event_name == "issue_comment":
        issue = event.get("issue", {})
        if issue.get("pull_request"):
            write_output(False, False)
            return

        body = (event.get("comment") or {}).get("body") or ""
        if normalize_first_line(body) != "/add-video":
            write_output(False, False)
            return

        author = (event.get("comment") or {}).get("user", {}).get("login")
        issue_author = (issue.get("user") or {}).get("login")
        if author and issue_author and author != issue_author:
            write_output(False, False)
            return

        issue_number = issue.get("number")
        command_json = json.dumps(
            {"number": issue_number, "payload": body},
            ensure_ascii=False,
        )
        write_output(True, True, command_json)
        return

    write_output(False, False)


if __name__ == "__main__":
    main()
