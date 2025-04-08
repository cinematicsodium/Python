import unicodedata

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

    def __init__(self, full_name: str):
        self.full_name = full_name

    def name_parts(self) -> list[str] | None:
        """
        Splits the full name into parts and removes titles and extraneous elements.
        """
        parts = self.full_name.split(" ")
        filtered_parts = [
            part
            for part in parts
            if part.lower() in NAME_PARTICLES
            or not (
                part.lower() in TITLES
                or (part.startswith('"') and part.endswith('"'))
                or (part.startswith("(") and part.endswith(")"))
                or ("." in part and (len(part.replace(".", "")) <= 3))
                or len(part) == 1
            )
        ]
        return filtered_parts if filtered_parts else None

    def format_last_first(self) -> str:
        """
        Formats the full name as "Last, First".
        """
        if " " not in self.full_name or len(
            filtered_parts := self.name_parts()
        ) not in (2, 3, 4):
            return self.full_name

        if len(filtered_parts) == 4:
            first, last1, last2, last3 = filtered_parts
            if last1.lower() in NAME_PARTICLES and last2.lower() in NAME_PARTICLES:
                last = f"{last1} {last2} {last3}"
            else:
                return self.full_name

        elif len(filtered_parts) == 3:
            first, last1, last2 = filtered_parts
            if last1.lower() in NAME_PARTICLES:
                last = f"{last1} {last2}"
            else:
                return self.full_name

        elif "," in filtered_parts[0]:
            last, first = filtered_parts[0].replace(",", ""), filtered_parts[1]
        else:
            first, last = filtered_parts

        return f"{last}, {first}".title()


class Formatter:
    def __init__(self, text: str):
        if not isinstance(text, str):
            raise TypeError(f"'{text}' must be a string, not {type(text)}")
        self.text = self.clean(text)

    @staticmethod
    def clean(text: str) -> str:
        """
        Normalizes the text, removes extra spaces, and applies a consistent newline prefix.
        """
        text = (
            unicodedata.normalize("NFKD", text)
            .replace("\r", " ")
            .replace("\t", " ")
            .strip()
        )
        if text != "":
            if "\n" in text:
                text = "\n".join(f"> {line}" for line in text.split("\n") if line)
            if " " in text:
                text = " ".join(word for word in text.split(" ") if word)
        return text

    def __str__(self):
        return self.text

    def key(self) -> str:
        return self.text.lower().replace(" ", "_")

    def value(self) -> str:
        if self.text.strip() == "":
            return None
        return self.text

    def name(self) -> str:
        """
        Class to format names as "Last, First".
        """
        return NameFormatter(self.text).format_last_first()

    def reason(self) -> str:
        """
        Formats the 'justification' content to allow line breaks within a single Excel cell.
        """
        self.text = self.text.replace('"', "'")
        return f'"{self.text}"'

    def numerical(self) -> str:
        """
        Formats the text as a numerical value.
        """
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
            source_text = (
                self.text if len(self.text) <= 100 else f"{self.text[:100]}..."
            )
            raise ValueError(
                "Cannot convert text to number\n"
                f"original text: {source_text}\n"
                f"parsed text: {numeric_string}"
            )

    def org_div(self) -> str:
        """
        Normalizes the text, removes hyphens, and applies a consistent lowercase.
        """
        return self.text.replace("-", "").strip().lower()

    def pay_plan(self) -> str:
        chars = list(self.text)
        for idx, char in enumerate(chars):
            chars[idx] = char.upper() if char.isalnum() else "-"
        return "".join(chars)


if __name__ == "__main__":
    pay = "NN/04/564/sdf4"
    print(Formatter(pay).pay_plan())
