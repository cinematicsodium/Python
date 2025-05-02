import re
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
    def _name_parts(name_string: str) -> Optional[list[str]]:
        parts = name_string.split(" ")
        filtered_parts = []
        for part in parts:
            if NameFormatter._is_valid(part):
                filtered_parts.append(part)
        return filtered_parts if filtered_parts else None

    @staticmethod
    def format_last_first(name_string: str) -> Optional[str]:
        if any(
            [
                not name_string,
                " " not in name_string,
                (filtered_parts := NameFormatter._name_parts(name_string)) is None,
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
