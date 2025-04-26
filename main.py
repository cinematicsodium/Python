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

        for pdf_path in folder.iterdir():
            if pdf_path.is_file() and pdf_path.suffix == ".pdf":
                if "GRP" in pdf_path.name in pdf_path.name:
                    continue
                try:
                    processor = IndProcessor(pdf_path)
                    processor.process_pdf_data()
                    processed_list.append(pdf_path.name)

                except Exception as e:
                    logger.error(e)
                    failed_list.append({"file": pdf_path.name, "error": {str(e)[:100]}})

        logger.info(f"\n\nProcessed Files Count: {len(processed_list)}")
        if processed_list:
            [logger.info(f"- {processed}") for processed in processed_list]

        logger.info(f"\n\nProcess Failure Count: {len(failed_list)}")
        for failed in failed_list:
            for k, v in failed.items():
                logger.info(f"- {k}: {str(v)[:100]}...")
            print()

    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
