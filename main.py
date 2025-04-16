from pathlib import Path

from constants import testing_mode
from ind_processor import IndProcessor
from logger import Logger
from utils import update_serial_numbers

logger = Logger()


def main():
    if not testing_mode:
        update_serial_numbers()
    try:
        processed_list: list[str] = []
        failed_list: list[dict[str, str]] = []

        folder: Path

        for file in folder.iterdir():
            if file.is_file() and file.suffix == ".pdf":
                if "GRP" in file.name or "NA-90" in file.name:
                    continue
                try:
                    processor = IndProcessor()
                    processor.run_processing(file)
                    processed_list.append(file.name)

                except Exception as e:
                    logger.error(e)
                    failed_list.append({"file": file.name, "error": {str(e)[:100]}})

        logger.info(f"\n\nProcessed Files Count: {len(processed_list)}")
        if processed_list:
            [logger.info(f"- {processed}") for processed in processed_list]

        logger.info(f"\n\nProcess Failure Count: {len(failed_list)}")
        for failed in failed_list:
            for k, v in failed.items():
                logger.info(f"- {k}: {str(v)[:100]}...")
            logger.info()
        logger.info()
    except Exception as e:
        logger.error(e)


def test_file():
    file_path: Path
    try:
        logger.info(file_path.name)
        processor = IndProcessor()
        processor.run_processing(file_path)

    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    # main()
    test_file()
