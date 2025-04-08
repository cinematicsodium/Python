from pathlib import Path

import fitz

from ind_processor import IndProcessor


def main():
    folder = Path("")

    for file in folder.iterdir():
        if file.is_file() and file.suffix == ".pdf":
            processor = IndProcessor(file)
            processor.process()


def testing():
    try:
        file: Path = Path("")
        processor = IndProcessor()
        processor.process(file)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    testing()
