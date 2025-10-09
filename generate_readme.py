#!/usr/bin/env python3
import json
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import Iterable


INPUT_PATH = Path("test2.json")
OUTPUT_PATH = Path("README.md")


@dataclass
class Entry:
    title: str
    channel: str
    link: str


def load_entries(path: Path) -> list[Entry]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = []
    for item in data.get("results", []):
        title = item.get("title", "").strip()
        channel = item.get("channel_name", "").strip()
        link = item.get("link", "").strip()
        if title and channel and link:
            entries.append(Entry(title=title, channel=channel, link=link))
    return entries


def group_by_channel(entries: Iterable[Entry]) -> dict[str, list[Entry]]:
    grouped: defaultdict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.channel].append(entry)
    for bucket in grouped.values():
        bucket.sort(key=lambda item: item.title.lower())
    return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))


def render_markdown(entries: list[Entry]) -> str:
    total = len(entries)
    header = [
        "# Подборка Python-собеседований",
        "",
        "_Файл README.md генерируется автоматически скриптом `generate_readme.py` на основе `test2.json`._",
        "",
        f"- Всего интервью: **{total}**",
        "",
    ]
    if total == 0:
        header.append("Данные отсутствуют. Запустите скрипт `get_name.py` для сбора информации.")
        header.append("")
        return "\n".join(header)

    grouped = group_by_channel(entries)
    blocks: list[str] = header
    for channel, items in grouped.items():
        blocks.append(f"## {channel}")
        blocks.append("")
        blocks.append("| # | Видео | Ссылка |")
        blocks.append("| - | ----- | ------ |")
        for idx, item in enumerate(items, start=1):
            blocks.append(f"| {idx} | {item.title} | [Смотреть]({item.link}) |")
        blocks.append("")
    return "\n".join(blocks)


def main() -> None:
    entries = load_entries(INPUT_PATH)
    markdown = render_markdown(entries)
    OUTPUT_PATH.write_text(markdown + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
