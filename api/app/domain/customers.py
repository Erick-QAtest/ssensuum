import re
from typing import Optional

PHONE_DIGITS = 10
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_phone(value: str) -> Optional[str]:
    """Devuelve el teléfono a 10 dígitos (México) o None si no es válido."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == PHONE_DIGITS + 3 and digits.startswith("521"):
        digits = digits[3:]
    elif len(digits) == PHONE_DIGITS + 2 and digits.startswith("52"):
        digits = digits[2:]
    return digits if len(digits) == PHONE_DIGITS else None


def normalize_email(value: str) -> Optional[str]:
    email = value.strip().lower()
    return email if _EMAIL.match(email) else None
