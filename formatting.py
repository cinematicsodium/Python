import re
from typing import Optional

from rich.traceback import install

install(show_locals=True)

TITLES: list[str] = [
    "dr.",
    "mr.",
    "mrs.",
    "miss.",
    "ms.",
    "prof.",
    "ph.d",
]
for title in TITLES:
    TITLES.append(title.replace(".", "")) if "." in title else None

NAME_PARTICLES = [
    "mc",
    "st",
    "st.",
    "de",
    "da",
    "di",
    "du",
    "la",
    "le",
    "el",
    "lo",
    "am",
    "op",
    "te",
    "zu",
    "zu",
    "im",
    "af",
    "av",
    "al",
    "ov",
    "ev",
]


class NameFormatter:
    """
    Class to format names as "Last, First".
    """

    @staticmethod
    def _is_valid(part: str) -> bool:
        def is_title(part: str) -> bool:
            pattern = r"\b[a-zA-Z]{2,4}\.(?:[a-zA-Z])?\.?(?:\s|$)"
            return re.match(pattern, part) is not None

        def is_enclosed(part: str) -> bool:
            pattern = re.compile(r"(['\"])([a-zA-Z]{1,12})\1|(\()([a-zA-Z]{1,32})(\))")
            return pattern.match(part) is not None

        return any(
            [
                part.lower() in NAME_PARTICLES,
                not is_title(part),
                not is_enclosed(part),
                not len(part) == 1,
            ]
        )

    @staticmethod
    def name_parts(name_string: str) -> Optional[list[str]]:
        """
        Splits the full name into parts and removes titles and extraneous elements.
        """
        parts = name_string.split(" ")
        filtered_parts = []
        for part in parts:
            if NameFormatter._is_valid(part):
                filtered_parts.append(part)
        return filtered_parts if filtered_parts else None

    @staticmethod
    def format_last_first(name_string: str) -> Optional[str]:
        """
        Formats the full name as "Last, First".
        """
        if any(
            [
                not name_string,
                " " not in name_string,
                (filtered_parts := NameFormatter.name_parts(name_string)) is None,
                len(filtered_parts) not in range(2, 6),
            ]
        ):
            return name_string

        elif len(filtered_parts) == 5:
            first_name, last_name, preposition = filtered_parts[:3]
            if preposition != "for":
                return name_string

        elif len(filtered_parts) == 4:
            first_name, preposition, article, noun = filtered_parts
            if (
                preposition.lower() in NAME_PARTICLES
                and article.lower() in NAME_PARTICLES
            ):
                last_name = f"{preposition} {article} {noun}"
            else:
                return name_string

        elif len(filtered_parts) == 3:
            first_name, preposition, article = filtered_parts
            if preposition.lower() in NAME_PARTICLES:
                last_name = f"{preposition} {article}"
            else:
                return name_string

        elif len(filtered_parts) == 2:
            if "," in filtered_parts[0]:
                last_name, first_name = filtered_parts[0], filtered_parts[1]
            else:
                first_name, last_name = filtered_parts

        last_name = last_name if last_name.endswith(",") else f"{last_name},"

        full_name: str = f"{last_name} {first_name}"

        capitalized_count: int = len(re.findall(r"[A-Z]", full_name))
        if 2 <= capitalized_count <= 5:
            return full_name
        return full_name.title()


class Formatter:
    def __init__(self, text: Optional[str]):
        self.text = text
        if isinstance(text, str):
            self.text = self._clean(text)

    @staticmethod
    def _clean(text: str) -> Optional[str]:
        """
        Normalizes the text, removes extra spaces, and applies a consistent newline prefix.
        """
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

    def __str__(self):
        return str(self.text)

    def key(self) -> Optional[str]:
        if not self.text:
            return
        return self.text.lower().replace(" ", "_")

    def value(self) -> Optional[str]:
        return self.text if self.text else None

    def name(self) -> Optional[str]:
        """
        Class to format names as "Last, First".
        """
        if not self.text or not isinstance(self.text, str):
            return
        return NameFormatter(self.text)

    def justification(self) -> Optional[str]:
        """
        Formats the 'justification' content to allow line breaks within a single Excel cell.
        """
        if not self.text:
            return
        text = self.text.replace('"', "'")
        lines: list[str] = [line.strip() for line in text.split("\n") if line.strip()]
        for idx, line in enumerate(lines):
            is_list_item: bool = re.match(r"^[a-zA-Z0-9]{1,3}\.", line) is not None
            if line[0].isalnum() and not is_list_item:
                lines[idx] = f"> {line}"
            else:
                lines[idx] = f"    {line}"
        text = "\n".join(lines)
        return f'"{text}"'

    def numerical(self) -> Optional[int]:
        """
        Formats the text as a numerical value.
        """
        if not self.text:
            return
        pattern = r"\s*([\d,]*\d(?:\.\d+)?)"
        match = re.search(pattern, self.text)
        if match is None:
            raise ValueError(f"Unable to extract numerical value from '{self.text}'")
        number = float(match.group(1).replace(",", ""))
        return number

    def standardized_org_div(self) -> Optional[str]:
        """
        Normalizes the text, removes hyphens, and applies a consistent lowercase.
        """
        if not self.text:
            return
        self.text = self.text.replace("-", "").replace(" ", "")
        return self.text.lower().strip()

    def pay_plan(self) -> Optional[str]:
        if not self.text:
            return

        def fmtpart(part: str) -> str:
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

        parts = [part.strip() for part in self.text.split()]
        formatted_parts = []
        for part in parts:
            part = fmtpart(part)
            if part:
                formatted_parts.append(part)
        return "_".join(formatted_parts)