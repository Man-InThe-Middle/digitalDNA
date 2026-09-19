import re
import unicodedata


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", value)


def normalize_username(value: str | None) -> str:
    return normalize_text(value.lstrip("@") if value else "")
