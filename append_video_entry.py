#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA_PATH = Path("list.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append a YouTube interview entry to list.json.",
    )
    parser.add_argument("--link", required=True, help="YouTube ссылка")
    parser.add_argument("--title", required=True, help="Название видео")
    parser.add_argument("--channel", required=True, help="Название канала")
    return parser.parse_args()


def ensure_youtube(link: str) -> None:
    lower = link.lower()
    if "youtube.com" not in lower and "youtu.be" not in lower:
        sys.exit("Ожидалась YouTube ссылка.")


def extract_video_id(link: str) -> str:
    parsed = urlparse(link)
    if parsed.hostname and "youtu.be" in parsed.hostname:
        return parsed.path.strip("/")
    if parsed.hostname and "youtube.com" in parsed.hostname:
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        segments = [part for part in parsed.path.split("/") if part]
        if len(segments) >= 2 and segments[0] == "shorts":
            return segments[1]
    return link


def load_entries() -> list[dict]:
    if DATA_PATH.exists():
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            sys.exit(f"Не удалось распарсить {DATA_PATH}: {exc}")
        return data.get("results", [])
    return []


def save_entries(entries: list[dict]) -> None:
    payload = {"results": entries}
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    link = args.link.strip()
    title = args.title.strip()
    channel = args.channel.strip()

    if not link or not title or not channel:
        sys.exit("Все поля (link, title, channel) обязательны.")

    ensure_youtube(link)
    new_id = extract_video_id(link)

    entries = load_entries()
    for item in entries:
        if extract_video_id(item.get("link", "")) == new_id:
            sys.exit(f"Видео с ID {new_id} уже есть в list.json.")

    entries.append({"title": title, "channel_name": channel, "link": link})
    save_entries(entries)
    print(f"Добавлено: {channel} — {title} ({new_id})")


if __name__ == "__main__":
    main()
