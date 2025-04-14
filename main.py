from pathlib import Path

from ind_processor import IndProcessor
from modules import Logger

logger = Logger()


def main():
    try:
        processed_list: list[str] = []
        failed_list: list[dict[str, str]] = []
        
        folder: Path

        for file in folder.iterdir():
            if file.is_file() and file.suffix == ".pdf":
                try:
                    logger.info(file.name)
                    processor = IndProcessor()
                    processor.process(file)
                    processed_list.append(file.name)

                except Exception as e:
                    logger.error(f"\n{file.name}\n{e}")
                    failed_list.append({"file": file.name, "error": {str(e)[:100]}})

        print(f"\n\nProcessed Files Count: {len(processed_list)}")
        if processed_list:
            [print(f"- {processed}") for processed in processed_list]

        print(f"\n\nProcess Failure Count: {len(failed_list)}")
        if failed_list:
            [
                print(f"- {k}: {str(v)[:100]}...")
                for failed in failed_list
                for k, v in failed.items()
            ]
        print("\n\n")
    except Exception as e:
        print(e)
