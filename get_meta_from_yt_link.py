#!/usr/bin/env python3
import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


DATA_PATH = Path("list.json")
WAIT_TIMEOUT = 20


@dataclass
class VideoInfo:
    title: str
    channel: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Получить метаданные YouTube-видео и сохранить в list.json",
    )
    parser.add_argument("link", help="Ссылка на YouTube-видео")
    return parser.parse_args()


def is_youtube_link(link: str) -> bool:
    lowered = link.lower()
    return "youtube.com" in lowered or "youtu.be" in lowered


def load_results() -> list[dict]:
    if not DATA_PATH.exists():
        logger.info("%s не найден. Создаю новый список.", DATA_PATH)
        return []
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Не удалось распарсить %s: %s", DATA_PATH, exc)
        sys.exit(1)
    return data.get("results", [])


def save_results(results: list[dict]) -> None:
    payload = {"results": results}
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_driver() -> webdriver.Chrome:
    logger.info("Инициализируем ChromeDriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    logger.info("ChromeDriver поднят")
    return driver


def _locate_channel(wait: WebDriverWait) -> str:
    selectors = ("#owner-name a", "#channel-name a")
    for selector in selectors:
        try:
            elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            text = elem.get_attribute("textContent") or elem.text
            text = (text or "").strip()
            if text:
                return text
        except TimeoutException:
            logger.debug("Selector %s не найден", selector)
            continue
    return "неизвестный канал"


def fetch_video_info(driver: webdriver.Chrome, url: str) -> VideoInfo:
    logger.info("Открываем страницу %s", url)
    driver.get(url)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    title = driver.title.removesuffix(" - YouTube").strip()
    if not title:
        elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ytd-watch-metadata"))
        )
        title = elem.text.strip() or "неизвестное видео"
    channel = _locate_channel(wait)
    if not title:
        title = "неизвестное видео"
    return VideoInfo(title=title, channel=channel)


def update_readme() -> None:
    logger.info("Перегенерирую README.md")
    subprocess.run([sys.executable, "generate_readme.py"], check=True)


def main() -> None:
    args = parse_args()
    link = args.link.strip()

    if not is_youtube_link(link):
        logger.error("Нужна ссылка на YouTube. Получено: %s", link)
        sys.exit(1)

    results = load_results()
    if any(item.get("link") == link for item in results):
        logger.info("Эта ссылка уже есть в списке. Повторений не требуется.")
        sys.exit(0)

    try:
        driver = _build_driver()
    except WebDriverException as exc:
        logger.error("Не удалось запустить ChromeDriver: %s", exc)
        sys.exit(1)

    try:
        info = fetch_video_info(driver, link)
    except (WebDriverException, TimeoutException) as exc:
        logger.error("Ошибка во время работы Selenium: %s", exc)
        sys.exit(1)
    finally:
        driver.quit()

    entry = {"title": info.title, "channel_name": info.channel, "link": link}
    results.append(entry)
    save_results(results)
    logger.info("Добавлено: %s — %s", info.channel, info.title)

    try:
        update_readme()
    except subprocess.CalledProcessError as exc:
        logger.error("Не удалось обновить README: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
