#!/usr/bin/env python3
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DATA_PATH = Path("list.json")
OUTPUT_PATH = Path("README.md")
DEFAULT_SUBMITTER = "https://github.com/UN-9BOT/"


@dataclass
class Entry:
    title: str
    channel: str
    link: str
    submitted_by: str


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
        submitted_by = item.get("submitted_by", "").strip() or DEFAULT_SUBMITTER
        if not (title and channel and link):
            continue
        if link in seen_links:
            continue
        entries.append(Entry(title=title, channel=channel, link=link, submitted_by=submitted_by))
        seen_links.add(link)
    return entries


def group_by_channel(entries: Iterable[Entry]) -> dict[str, list[Entry]]:
    grouped: defaultdict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.channel].append(entry)
    for bucket in grouped.values():
        bucket.sort(key=lambda item: item.title.lower())
    return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))


def anchor_id(name: str) -> str:
    slug = []
    for char in name.strip().lower():
        if char.isspace() or char in {"-", "_"}:
            slug.append("-")
        elif char.isalnum():
            slug.append(char)
    result = "".join(slug).strip("-")
    while "--" in result:
        result = result.replace("--", "-")
    return result or "section"


def render_markdown(entries: list[Entry]) -> str:
    total = len(entries)
    header = [
        "# Подборка Python-собеседований",
        "",
        f"- Всего интервью: **{total}**",
        f"- Последнее обновление: **{date.today().isoformat()}**",
        "",
    ]
    if total == 0:
        header.append("Данные отсутствуют. Добавьте интервью через issue с командой /add-video.")
        header.append("")
        return "\n".join(header)

    grouped = group_by_channel(entries)
    submitters = dict(
        sorted(
            ((entry.link, entry.submitted_by) for entry in entries),
            key=lambda item: item[0],
        )
    )
    submitters_json = json.dumps({"submitted_by": submitters}, ensure_ascii=False, indent=2)

    toc_block: list[str] = [
        "## Добавившие",
        "",
        "```json",
        *submitters_json.splitlines(),
        "```",
        "",
        "## Каналы",
        "",
    ]
    for channel, items in grouped.items():
        toc_block.append(f"- [{channel} ({len(items)})](#{anchor_id(channel)})")
    toc_block.append("")

    blocks: list[str] = [
        *header,
        *toc_block,
        "## Contributing",
        "",
        "- Открыт для PR =)",
        "- Не редактируйте `list.json` и `README.md` вручную.",
        "- Видео добавляйте только через issue `/add-video`.",
        "- При создании issue выберите шаблон «Новое Видео».",
        "- В описании должно быть:",
        "  ```",
        "  /add-video",
        "  link=\"https://www.youtube.com/watch?v=...\"",
        "  title=\"Название видео\"",
        "  channel=\"Название канала\"",
        "  ```",
        "  GitHub Actions создаст PR автоматически. Других способов добавления нет.",
        "- Созданный PR будет ссылаться на issue.",
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
