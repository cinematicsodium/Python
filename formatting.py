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
            if part.lower() in NAME_PARTICLES
            or part.lower() in TITLES
            or not any(
                [
                    (part.startswith('"') and part.endswith('"')),
                    (part.startswith("(") and part.endswith(")")),
                    ("." in part and len(part.replace(".", "")) in (1, 3)),
                    len(part) == 1,
                ]
            )
        ]
        return filtered_parts if filtered_parts else None

    def format_last_first(self) -> str:
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
        if isinstance(text, str):
            self.text = self._clean(text)
        elif text is None:
            self.text = None
        else:
            raise ValueError(
                f"Unable to format '{text}'.\n"
                f"Expected Type: [str, None]\n"
                f"Received Type: {type(text)}"
            )

    @staticmethod
    def _clean(text: str) -> str:
        """
        Normalizes the text, removes extra spaces, and applies a consistent newline prefix.
        """
        text = (
            unicodedata.normalize("NFKD", text)
            .replace("\r", "\n")
            .replace("\t", "    ")
        )
        if " " in text:
            text = " ".join(word for word in text.split(" ") if word)
        return text.strip()

    def __str__(self):
        return str(self.text)

    def key(self) -> str:
        return self.text.lower().replace(" ", "_") if self.text else None

    def value(self) -> str:
        return self.text if self.text else None

    def name(self) -> str:
        """
        Class to format names as "Last, First".
        """
        return NameFormatter(self.text).format_last_first() if self.text else None

    def justification(self) -> str:
        """
        Formats the 'justification' content to allow line breaks within a single Excel cell.
        """
        if not self.text:
            return
        text = self.text.replace('"', "'")
        if "\n" in text:
            text = "\n".join(f"> {line}" for line in text.split("\n") if line.strip())
        return f'"{text}"'

    def numerical(self) -> str:
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

    def standardized_org_div(self) -> str:
        """
        Normalizes the text, removes hyphens, and applies a consistent lowercase.
        """
        if not self.text:
            return
        chars: list[str] = ["-", ".", " "]
        for char in chars:
            self.text = self.text.replace(char, "")
        return self.text.lower().strip()

    def pay_plan(self) -> str:
        if not self.text:
            return
        chars = list(self.text)
        for idx, char in enumerate(chars):
            chars[idx] = char.upper() if char.isalnum() else "-"
        if chars[1].isalpha() and chars[2].isnumeric():
            chars.insert(2, "-")
        return "".join(chars)


if __name__ == "__main__":
    val = None
    print(Formatter(val).key())
