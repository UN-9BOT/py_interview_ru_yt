#!/usr/bin/env python3
import sys


def main() -> None:
    sys.exit(
        "Локальное добавление отключено. Создайте issue с командой /add-video, "
        "остальное сделает GitHub Actions."
    )


if __name__ == "__main__":
    main()
