import re
import unicodedata
from typing import Optional

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


def is_title(part: str) -> bool:
    pattern = r"\b[a-zA-Z]{2,4}\.(?:[a-zA-Z])?\.?(?:\s|$)"
    return re.match(pattern, part) is not None


def is_enclosed(part: str) -> bool:
    pattern = re.compile(r"(['\"])([a-zA-Z]{1,12})\1|(\()([a-zA-Z]{1,32})(\))")
    return pattern.match(part) is not None


class NameFormatter:
    """
    Class to format names as "Last, First".
    """

    def __init__(self, full_name: str):
        self.full_name = full_name
        if not full_name:
            return

    def name_parts(self) -> list[str] | None:
        """
        Splits the full name into parts and removes titles and extraneous elements.
        """
        parts = self.full_name.split(" ")
        filtered_parts = [
            part
            for part in parts
            if any(
                [
                    part.lower() in NAME_PARTICLES,
                    not is_title(part),
                    not is_enclosed(part),
                    not len(part) == 1,
                ]
            )
        ]
        return filtered_parts if filtered_parts else None

    def format_last_first(self) -> Optional[str]:
        """
        Formats the full name as "Last, First".
        """
        if not self.full_name:
            return

        if any(
            [
                " " not in self.full_name,
                (filtered_parts := self.name_parts()) is None,
                len(filtered_parts) not in range(2, 6),
            ]
        ):
            return self.full_name

        elif len(filtered_parts) == 5:
            first_name, last_name, preposition = filtered_parts[:3]
            if preposition != "for":
                return self.full_name

        elif len(filtered_parts) == 4:
            first_name, preposition, article, noun = filtered_parts
            if (
                preposition.lower() in NAME_PARTICLES
                and article.lower() in NAME_PARTICLES
            ):
                last_name = f"{preposition} {article} {noun}"
            else:
                return self.full_name

        elif len(filtered_parts) == 3:
            first_name, preposition, article = filtered_parts
            if preposition.lower() in NAME_PARTICLES:
                last_name = f"{preposition} {article}"
            else:
                return self.full_name

        elif len(filtered_parts) == 2:
            if "," in filtered_parts[0]:
                last_name, first_name = filtered_parts[0], filtered_parts[1]
            else:
                first_name, last_name = filtered_parts

        last_name = last_name if last_name.endswith(",") else f"{last_name},"

        full_name: str = f"{last_name} {first_name}"

        upper_count: int = sum(1 for char in full_name if str(char).isupper())

        full_name = full_name if 2 <= upper_count <= 5 else full_name.title()
        return full_name


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
        text = (
            text.encode("ascii", errors="ignore")
            .decode("utf-8")
            .replace("\r", "\n")
            .replace("\t", "    ")
        )
        text = " ".join(word for word in text.split(" ") if word)
        return text.strip()

    def __str__(self):
        return str(self.text)

    def key(self) -> Optional[str]:
        if not self.text:
            return
        return self.text.lower().replace(" ", "_")

    def value(self) -> Optional[str]:
        if not self.text:
            return
        return self.text

    def name(self) -> Optional[str]:
        """
        Class to format names as "Last, First".
        """
        if not self.text:
            return
        return NameFormatter(self.text).format_last_first()

    def justification(self) -> Optional[str]:
        """
        Formats the 'justification' content to allow line breaks within a single Excel cell.
        """
        if not self.text:
            return
        text = self.text.replace('"', "'")
        lines: list[str] = [line.strip() for line in text.split("\n") if line.strip()]
        for idx, line in enumerate(lines):
            match = re.match(r"^[a-zA-Z0-9]{1,3}\.", line)
            if line[0].isalnum() and not match:
                lines[idx] = f"> {line}"
            else:
                lines[idx] = f"    {line}"
        text = "\n".join(lines)
        return f'"{text}"'

    def numerical(self) -> Optional[str]:
        """
        Formats the text as a numerical value.
        """
        if not self.text:
            return
        numeric_string = "".join(
            char for char in self.text if char.isdigit() or char == "."
        )
        if not numeric_string:
            raise ValueError(f"No numeric value found in text: {self.text}")
        if numeric_string.count(".") > 1:
            raise ValueError(f"Multiple decimal points found in text: {self.text}")
        try:
            return float(numeric_string)
        except ValueError:
            source_text = self.text[:100]
            raise ValueError(
                "Cannot convert text to number\n"
                f"original text: {source_text}\n"
                f"parsed text: {numeric_string}"
            )

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
