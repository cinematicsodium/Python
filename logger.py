from datetime import datetime

from constants import logger_path
from rich.console import Console

console = Console()


class Logger:

    def _log(self, level: str, color: str, message: str):
        console.status("").stop()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]

        console.print(f"[{color}]{now} - {level}: {message}[/{color}]")

        with open(logger_path, "a", encoding="utf-8") as f:
            f.write(f"\n{now} - {level}: {message}")

    def info(self, message):
        self._log("INFO", "spring_green3", message)

    def warning(self, message):
        self._log("WARNING", "orange1", message)

    def error(self, message):
        self._log("ERROR", "red1", message)
