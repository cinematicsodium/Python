from datetime import datetime

from constants import PathManager
from rich.console import Console

console = Console()


class Logger:
    def _log(self, level: str, color: str, message: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]

        console.print(f"[{color}]{now} - {level}: {message}[/{color}]")

        with open(PathManager.logger_path, "a", encoding="utf-8") as f:
            f.write(f"\n{now} - {level}: {message}")

    def info(self, message):
        self._log("INFO", "spring_green3", message)

    def warning(self, message):
        self._log("WARNING", "orange1", f"\n{message}\n")

    def error(self, message):
        self._log("ERROR", "red1", f"\n{message}\n")

    def path(self, message):
        self._log("INFO", "spring_green3", f"\n{message}")

    def final(self, message):
        self._log("INFO", "spring_green3", f"\n\n{message}\n")
