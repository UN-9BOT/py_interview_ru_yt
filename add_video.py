#!/usr/bin/env python3
import json
import sys
from pathlib import Path

TEST2_PATH = Path("test2.json")

BORDER = "=" * 60


def load_results(path: Path) -> list[dict]:
    if not path.exists():
        print("Файл test2.json не найден, создаю новый каркас.")
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Ошибка чтения JSON: {exc}")
        sys.exit(1)
    return data.get("results", [])


def save_results(path: Path, results: list[dict]) -> None:
    payload = {"results": results}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prompt(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Пустое значение недопустимо. Повторите ввод.")


def ask_link() -> str:
    while True:
        link = prompt("YouTube ссылка")
        lowered = link.lower()
        if ("youtube.com" in lowered) or ("youtu.be" in lowered):
            return link
        print("Нужна ссылка на YouTube. Попробуйте снова.")


def confirm(entry: dict) -> bool:
    print(BORDER)
    print("Проверьте введённые данные:")
    for key, value in entry.items():
        print(f"- {key}: {value}")
    print(BORDER)
    while True:
        answer = input("Сохранить? [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Введите 'y' или 'n'.")


def main() -> None:
    if not sys.stdin.isatty():
        print("Ошибка: для добавления записи нужен интерактивный терминал.")
        sys.exit(1)

    print(BORDER)
    print(" Добавление нового интервью ".center(60, "="))
    print("Заполняйте поля. Для выхода нажмите Ctrl+C.")
    print(BORDER)

    try:
        results = load_results(TEST2_PATH)
        link = ask_link()
        title = prompt("Название видео")
        channel = prompt("Название канала")
        entry = {"title": title, "channel_name": channel, "link": link}

        if any(item.get("link") == link for item in results):
            print("Такая ссылка уже есть в списке. Добавление отменено.")
            return

        if not confirm(entry):
            print("Отменено пользователем.")
            return

        results.append(entry)
        save_results(TEST2_PATH, results)
        print("Готово! Запись добавлена в конец test2.json.")
        print("README.md будет обновлён автоматически после завершения make.")
    except KeyboardInterrupt:
        print("\nОтмена пользователем.")
        sys.exit(1)
    except EOFError:
        print("\nВвод неожиданно завершён. Изменения не сохранены.")
        sys.exit(1)


if __name__ == "__main__":
    main()
