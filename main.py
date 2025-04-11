from pathlib import Path

import fitz

from ind_processor import IndProcessor
from utils import log


def main():
    folder: Path

    for file in folder.iterdir():
        if file.is_file() and file.suffix == ".pdf":
            log(file.name)
            processor = IndProcessor()
            data = processor.process(file)


def testing():
    try:
        file: Path
        log(file.name)
        processor = IndProcessor()
        data = processor.process(file)
        log(f'\n{data}')
    except Exception as e:
        log(f"[bright_red]Error: {e}[/bright_red]")


if __name__ == "__main__":
    testing()

