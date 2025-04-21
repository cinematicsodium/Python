from datetime import datetime

from constants import path_manager, testing_mode
from rich.console import Console

console = Console()


class Logger:
    def _log(
        self,
        message: str,
        level: str = "INFO",
        color: str = "spring_green3",
        linebreak=True,
    ):
        padding = "\n" if linebreak is True else ""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]

        console.print(
            f"[{color}]{padding}{now} - {level}: {message}{padding}[/{color}]"
        )
        with open(path_manager.logger_path, "a", encoding="utf-8") as f:
            f.write(f"\n{padding}{now} - {level}: {message}{padding}")

    def info(self, message):
        self._log(message, linebreak=False)

    def warning(self, message):
        self._log(message, "WARNING", "orange1")

    def error(self, message):
        self._log(message, "ERROR", "red1")

    def path(self, message):
        self._log(message)

    def final(self, message):
        self._log(f"\n{message}")
