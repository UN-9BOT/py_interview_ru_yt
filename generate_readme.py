#!/usr/bin/env python3
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable
from urllib.parse import parse_qs, urlparse


DATA_PATH = Path("list.json")
OUTPUT_PATH = Path("README.md")


@dataclass
class Entry:
    title: str
    channel: str
    link: str


def sanitize_title(value: str) -> str:
    return " — ".join(part.strip() for part in value.split("|") if part.strip()) or value.replace("|", " ")


def link_label(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if qs.get("v"):
        return qs["v"][0]
    tail = parsed.path.rstrip("/").split("/")[-1]
    return tail or parsed.netloc


def load_entries() -> list[Entry]:
    entries: list[Entry] = []
    seen_links: set[str] = set()
    if not DATA_PATH.exists():
        return entries
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for item in data.get("results", []):
        raw_title = item.get("title", "")
        title = sanitize_title(raw_title.strip())
        channel = item.get("channel_name", "").strip()
        link = item.get("link", "").strip()
        if not (title and channel and link):
            continue
        if link in seen_links:
            continue
        entries.append(Entry(title=title, channel=channel, link=link))
        seen_links.add(link)
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
        f"- Всего интервью: **{total}**",
        "",
    ]
    if total == 0:
        header.append("Данные отсутствуют. Запустите скрипт `get_meta_from_yt_link.py` для сбора информации.")
        header.append("")
        return "\n".join(header)

    grouped = group_by_channel(entries)
    blocks: list[str] = [
        *header,
        "## Contributing",
        "",
        "- Открыт для PR =)",
        "- README.md руками не править!",
        "- Добавляйте новые интервью через `make meta \"https://youtu...\"` или интерактивно через `make add`.",
        "- Можно запустить GitHub Actions workflow `Add Video via Dispatch` (inputs: link/title/channel) — он создаст PR автоматически.",
        "- При ручных правках дописывайте записи в конец `list.json` (ключ `results`).",
        "- Используйте только YouTube-ссылки и интервью по Python.",
        "- После правок выполните `make readme`, чтобы обновить `README.md`.",
        "",
    ]
    for channel, items in grouped.items():
        blocks.append(f"## {channel}")
        blocks.append("")
        blocks.append("| # | Видео | Ссылка |")
        blocks.append("| - | ----- | ------ |")
        for idx, item in enumerate(items, start=1):
            label = link_label(item.link)
            blocks.append(f"| {idx} | {item.title} | [{label}]({item.link}) |")
        blocks.append("")
    return "\n".join(blocks)


def main() -> None:
    entries = load_entries()
    markdown = render_markdown(entries)
    OUTPUT_PATH.write_text(markdown + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
