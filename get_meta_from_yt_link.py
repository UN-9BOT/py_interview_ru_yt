import json
import logging
import random
import sys
import time
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


TEST1_PATH = Path("test1.json")
LIST_PATH = Path("list.json")
WAIT_TIMEOUT = 20
SLEEP_RANGE = (5, 15)


@dataclass
class VideoInfo:
    title: str
    channel: str


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
        logger.info("Пробуем найти канал через selector=%s", selector)
        try:
            elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            text = elem.get_attribute("textContent") or elem.text
            text = (text or "").strip()
            if text:
                logger.info("Канал найден: %s", text)
                return text
        except TimeoutException:
            logger.warning("Не найден канал по selector=%s", selector)
            continue
    logger.error("Не удалось получить название канала")
    return "неизвестный канал"


def fetch_video_info(driver: webdriver.Chrome, url: str) -> VideoInfo:
    logger.info("Открываем страницу %s", url)
    driver.get(url)
    logger.info("Получили текущий URL: %s", driver.current_url)
    logger.info("Document.readyState: %s", driver.execute_script("return document.readyState"))
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    title = driver.title.removesuffix(" - YouTube").strip()
    logger.info("Заголовок из driver.title: %s", title)
    if not title:
        logger.info("driver.title пустой, ищем <h1>")
        elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ytd-watch-metadata"))
        )
        title = elem.text.strip() or "неизвестное видео"
    channel = _locate_channel(wait)
    if not title:
        logger.error("Не удалось извлечь название видео")
        title = "неизвестное видео"
    return VideoInfo(title=title, channel=channel)


def _load_links(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    interviews = raw.get("interviews", {})
    links = []
    for level, entries in interviews.items():
        logger.info("Скачиваем раздел %s (%d записей)", level, len(entries))
        for entry in entries:
            link = entry.get("link")
            if link:
                links.append(link)
    return links


def _load_existing_results(path: Path) -> list[dict]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("results", [])
        except json.JSONDecodeError:
            logger.warning("Не удалось распарсить %s, начинаем заново", path)
    return []


def _store_results(path: Path, results: list[dict]) -> None:
    payload = {"results": results}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if not TEST1_PATH.exists():
        logger.error("Не найден входной файл %s", TEST1_PATH)
        sys.exit(1)

    links = _load_links(TEST1_PATH)
    if not links:
        logger.error("Не найдено ссылок в %s", TEST1_PATH)
        sys.exit(1)

    results = _load_existing_results(LIST_PATH)
    processed = {item["link"] for item in results if "link" in item}
    logger.info("Уже обработано: %d ссылок", len(processed))

    try:
        driver = _build_driver()
    except WebDriverException as exc:
        logger.error("Не удалось инициализировать WebDriver: %s", exc)
        sys.exit(1)

    try:
        for idx, url in enumerate(links, start=1):
            if url in processed:
                logger.info("Пропускаем уже обработанную ссылку: %s", url)
                continue

            logger.info("Обработка %d/%d: %s", idx, len(links), url)
            info = fetch_video_info(driver, url)
            entry = {"title": info.title, "channel_name": info.channel, "link": url}
            results.append(entry)
            _store_results(LIST_PATH, results)
            logger.info("Запись сохранена. Текущий размер: %d", len(results))

            if idx != len(links):
                delay = random.uniform(*SLEEP_RANGE)
                logger.info("Пауза %.2f секунд", delay)
                time.sleep(delay)
    except (WebDriverException, TimeoutException) as exc:
        logger.error("Ошибка Selenium: %s", exc)
        sys.exit(1)
    finally:
        logger.info("Закрываем браузер")
        driver.quit()


if __name__ == "__main__":
    main()
