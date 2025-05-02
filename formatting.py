import re
from typing import Optional

from .nameformatter import NameFormatter
from rich.traceback import install

install(show_locals=True)


class Formatter:
    @staticmethod
    def clean(text: str) -> Optional[str]:
        if not isinstance(text, str):
            return
        text = text.encode("ascii", errors="ignore").decode("utf-8")
        regex_map: dict[str, str] = {
            r"\r": "\n",
            r"\n{2,}": "\n",
            r"\t": " ",
            r" {2,}": " ",
        }
        for pattern, replacement in regex_map.items():
            text = re.sub(pattern, replacement, text)
        return text.strip() if text else None

    @staticmethod
    def key(text: str) -> Optional[str]:
        text = Formatter.clean(text)
        if not text:
            return
        pattern = r"[a-zA-Z0-9]+"
        matches = re.findall(pattern, text)
        if not matches:
            return
        return "_".join(matches).lower()

    @staticmethod
    def name(text: str) -> Optional[str]:
        text = Formatter.clean(text)
        if not text:
            return
        return NameFormatter.format_last_first(text)

    @staticmethod
    def justification(text: str) -> Optional[str]:
        text = Formatter.clean(text)
        if not text:
            return
        text = text.replace('"', "'")
        lines: list[str] = [line.strip() for line in text.split("\n") if line.strip()]
        for idx, line in enumerate(lines):
            is_list_item: bool = re.match(r"^[a-zA-Z0-9]{1,3}\.", line) is not None
            if line[0].isalnum() and not is_list_item:
                lines[idx] = f"> {line}"
            else:
                lines[idx] = f"    {line}"
        text = "\n".join(lines)
        return f'"{text}"'

    @staticmethod
    def numerical(text: str) -> Optional[int | float]:
        text = Formatter.clean(text)
        if not text:
            return
        pattern = r"\s*([\d,]*\d(?:\.\d+)?)"
        match = re.search(pattern, text)
        if match is None:
            raise ValueError(f"Unable to extract numerical value from '{text}'")
        number = float(match.group(1).replace(",", ""))
        return int(number) if number.is_integer() else number

    @staticmethod
    def standardized_org_div(text: str) -> Optional[str]:
        text = Formatter.clean(text)
        if not text:
            return
        text = text.replace("-", "").replace(" ", "")
        return text.lower().strip()

    @staticmethod
    def _fmtpart(part: str) -> str:
        part = re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", part)
        part = re.sub(
            r"[^a-zA-Z0-9]+",
            lambda match: (
                "-" if match.start() != 0 and match.end() != len(part) else ""
            ),
            part,
        ).upper()
        part = re.sub(r"-+", "-", part)
        return part

    @staticmethod
    def pay_plan(text: str) -> Optional[str]:
        text = Formatter.clean(text)
        if not text:
            return

        parts = [part.strip() for part in text.split()]
        formatted_parts = []
        for part in parts:
            part = Formatter._fmtpart(part)
            if part:
                formatted_parts.append(part)
        return "_".join(formatted_parts)


if __name__ == "__main__":
    text = "  This is a test text with   multiple spaces, tabs\tand newlines.\n\n\n"
    formatter = Formatter()
    print(formatter.pay_plan(text))
