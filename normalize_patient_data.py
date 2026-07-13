"""
# Patient Data Normalizer

## What it is

A utility for cleaning raw, inconsistent patient intake records into a standardized
shape. The following data-cleaning techniques are applied:

- **Whitespace normalization** - Leading/trailing spaces are stripped and repeated
  internal spaces are collapsed to a single space.
- **Title-casing for names and addresses** - Person names and street addresses are
  converted to title case, including hyphenated names (e.g. `mary-jane` → `Mary-Jane`
  and `o'connor` → `O'Connor`).
- **Multi-format date parsing** - Date-of-birth values arriving as `MM/DD/YYYY`,
  `DD-MM-YYYY`, `YYYY/MM/DD`, and other common separators are parsed and emitted
  as ISO `YYYY-MM-DD`.
- **Phone digit extraction** - Punctuation such as parentheses, dashes, and spaces
  is removed, leaving digits only (e.g. `(555) 123-4567` → `5551234567`).
- **Email normalization** - Email addresses are lowercased and trimmed.
- **Gender canonicalization** - Free-text or abbreviated gender values (`M`, `male`,
  `F`, etc.) are mapped to one of: `Male`, `Female`, `Other`, `Unknown`.
- **MRN/ID normalization** - Medical record numbers and patient IDs are uppercased
  and stripped of non-alphanumeric separators.

## What it is used for

Healthcare systems depend on absolute data uniformity across intake channels,
legacy imports, and partner feeds. Standardized records enable:

- **Reliable indexing and search** - Queries match the same logical patient because
  field shapes are predictable.
- **Duplicate detection and record linkage** - Consistent names, DOBs, and phone
  numbers reduce false negatives when merging or deduplicating charts.
- **Interoperability** - EHR, HL7, and FHIR pipelines expect fixed formats; cleaning
  at ingestion avoids downstream validation failures.
- **Reporting and audit consistency** - Analytics, compliance exports, and audit
  trails rely on uniform values rather than source-specific quirks.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%m-%d-%Y",
    "%d/%m/%Y",
)

GENDER_ALIASES: dict[str, str] = {
    "m": "Male",
    "male": "Male",
    "man": "Male",
    "f": "Female",
    "female": "Female",
    "woman": "Female",
    "o": "Other",
    "other": "Other",
    "nonbinary": "Other",
    "non-binary": "Other",
    "nb": "Other",
    "u": "Unknown",
    "unknown": "Unknown",
    "": "Unknown",
}

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "first_name": ("first_name", "firstName", "fname"),
    "last_name": ("last_name", "lastName", "lname"),
    "date_of_birth": ("date_of_birth", "dob", "birth_date"),
    "phone": ("phone", "phone_number", "mobile"),
    "email": ("email", "email_address"),
    "address": ("address", "street_address"),
    "gender": ("gender", "sex"),
    "mrn": ("mrn", "patient_id", "id"),
}


def _collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def _title_name(value: str) -> str:
    collapsed = _collapse_whitespace(value)

    def title_part(part: str) -> str:
        if not part:
            return part
        if "'" in part:
            prefix, _, suffix = part.partition("'")
            return prefix.capitalize() + "'" + suffix.capitalize()
        return part.capitalize()

    return " ".join(
        "-".join(title_part(piece) for piece in segment.split("-"))
        for segment in collapsed.split(" ")
    )


def _normalize_date(value: str) -> str:
    cleaned = _collapse_whitespace(value)
    if not cleaned:
        return ""

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return ""


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value.strip())


def _normalize_email(value: str) -> str:
    return _collapse_whitespace(value).lower()


def _normalize_gender(value: str) -> str:
    key = _collapse_whitespace(value).lower()
    return GENDER_ALIASES.get(key, "Unknown")


def _normalize_mrn(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()


def _normalize_address(value: str) -> str:
    return _title_name(value)


def _extract_raw_value(raw: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in raw:
            return raw[alias]
    return ""


def normalize_patient_data(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a cleaned copy of raw patient data with standardized field values."""
    canonical_values: dict[str, str] = {
        "first_name": _title_name(str(_extract_raw_value(raw, FIELD_ALIASES["first_name"]))),
        "last_name": _title_name(str(_extract_raw_value(raw, FIELD_ALIASES["last_name"]))),
        "date_of_birth": _normalize_date(str(_extract_raw_value(raw, FIELD_ALIASES["date_of_birth"]))),
        "phone": _normalize_phone(str(_extract_raw_value(raw, FIELD_ALIASES["phone"]))),
        "email": _normalize_email(str(_extract_raw_value(raw, FIELD_ALIASES["email"]))),
        "address": _normalize_address(str(_extract_raw_value(raw, FIELD_ALIASES["address"]))),
        "gender": _normalize_gender(str(_extract_raw_value(raw, FIELD_ALIASES["gender"]))),
        "mrn": _normalize_mrn(str(_extract_raw_value(raw, FIELD_ALIASES["mrn"]))),
    }

    alias_keys = {alias for aliases in FIELD_ALIASES.values() for alias in aliases}
    clean: dict[str, Any] = dict(canonical_values)

    for key, value in raw.items():
        if key not in alias_keys and key not in clean:
            clean[key] = value

    return clean


if __name__ == "__main__":
    from pprint import pprint

    messy_patient = {
        "first_name": "  jOhN   ",
        "last_name": "  o'connor ",
        "date_of_birth": "03/15/1985",
        "phone": "(555) 123-4567",
        "email": "  John.OConnor@Example.COM ",
        "address": "  123 main st, apt 4b  ",
        "gender": "M",
        "mrn": "mrn-00123-abc",
        "notes": "Referred by Dr. Smith",
    }

    print("Raw patient data:")
    pprint(messy_patient)
    print("\nNormalized patient data:")
    pprint(normalize_patient_data(messy_patient))
