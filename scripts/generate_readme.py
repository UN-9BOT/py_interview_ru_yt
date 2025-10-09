#!/usr/bin/env python3
import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DATA_PATH = Path("list.json")
OUTPUT_PATH = Path("README.md")


@dataclass
class Entry:
    title: str
    channel: str
    link: str
    submitted_by: str
    added_at: date


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
        raw_submitter = (item.get("submitted_by") or "").strip()
        if not raw_submitter:
            raise ValueError(f"Для ссылки {link} не указан submitted_by в list.json.")
        submitter = raw_submitter.rstrip("/").split("/")[-1].lstrip("@")
        if not submitter:
            raise ValueError(f"Для ссылки {link} указано пустое submitted_by в list.json.")
        raw_added_at = (item.get("added_at") or "").strip()
        if not raw_added_at:
            raise ValueError(f"Для ссылки {link} не указана дата added_at.")
        try:
            added_at = datetime.fromisoformat(raw_added_at).date()
        except ValueError as exc:
            raise ValueError(f"Некорректная дата added_at для {link}: {raw_added_at}") from exc
        if not (title and channel and link):
            continue
        if link in seen_links:
            continue
        entries.append(
            Entry(
                title=title,
                channel=channel,
                link=link,
                submitted_by=submitter,
                added_at=added_at,
            )
        )
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
    latest_added = max((entry.added_at for entry in entries), default=None)
    header = [
        "# Подборка Python-собеседований",
        "",
        f"- Всего интервью: **{total}**",
        f"- Последнее добавление: **{(latest_added or date.today()).isoformat()}**",
        "",
    ]
    if total == 0:
        header.append("Данные отсутствуют. Добавьте интервью через issue с командой /add-video.")
        header.append("")
        return "\n".join(header)

    grouped = group_by_channel(entries)
    toc_block: list[str] = [
        "## Каналы",
        "",
    ]
    for channel, items in grouped.items():
        toc_block.append(f"- [{channel} ({len(items)})](#{anchor_id(channel)})")
    toc_block.append("")

    latest_section: list[str] = []
    latest = sorted(
        entries,
        key=lambda item: (item.added_at, item.channel.lower(), item.title.lower(), item.link),
    )[-5:]
    if latest:
        latest_section.extend(
            [
                "## Последние добавления",
                "",
                "| # | Канал | Видео | Ссылка | Контрибьютор |",
                "| - | ------ | ----- | ------ | ------------- |",
            ]
        )
        for idx, item in enumerate(reversed(latest), start=1):
            label = link_label(item.link)
            contributor_link = f"https://github.com/{item.submitted_by}"
            latest_section.append(
                f"| {idx} | {item.channel} | {item.title} | [{label}]({item.link}) | "
                f"[{item.submitted_by}]({contributor_link}) |"
            )
        latest_section.append("")

    blocks: list[str] = [
        *header,
        "## Contributing",
        "",
        "- Открыт для PR =)",
        "- Не редактируйте `list.json` и `README.md` вручную.",
        "- Видео добавляйте только через issue `/add-video`.",
        "- При создании issue выберите шаблон «Новое Видео».",
        "- В описании должно быть:",
        "  ```",
        "  /add-video",
        "  LINK = https://www.youtube.com/watch?v=...",
        "  TITLE = Название видео",
        "  CHANNEL = Название канала",
        "  ```",
        "  GitHub Actions создаст PR автоматически. Других способов добавления нет.",
        "- Созданный PR будет ссылаться на issue.",
        "",
        *latest_section,
        *toc_block,
    ]
    for channel, items in grouped.items():
        blocks.append(f"## {channel}")
        blocks.append("")
        blocks.append("| # | Видео | Ссылка | Контрибьютор |")
        blocks.append("| - | ----- | ------ | ------------- |")
        for idx, item in enumerate(items, start=1):
            label = link_label(item.link)
            contributor_link = f"https://github.com/{item.submitted_by}"
            blocks.append(f"| {idx} | {item.title} | [{label}]({item.link}) | [{item.submitted_by}]({contributor_link}) |")
        blocks.append("")
    return "\n".join(blocks)


def main() -> None:
    entries = load_entries()
    markdown = render_markdown(entries)
    OUTPUT_PATH.write_text(markdown + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
