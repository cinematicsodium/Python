from pathlib import Path
from ind_processor import IndProcessor


def main():
    folder = Path("")

    for file in folder.iterdir():
        if file.is_file() and file.suffix == ".pdf":
            processor = IndProcessor(file)
            processor.process()