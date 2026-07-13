"""
# Medical Record Anonymizer

## What it is

A utility for removing personally identifiable information (PII) from clinical text
such as doctor notes, discharge summaries, and referral letters. The methodology
centers on ordered regex passes and whole-span token replacement:

- **Ordered regex passes** - Patterns are applied from most specific to least
  specific (email, phone, ID, custom words, then names) so structured identifiers
  are caught before broader name heuristics fire, reducing false partial matches.
- **Whole-span replacement** - Each match is replaced with a standardized token;
  surrounding whitespace, punctuation, and clinical terminology are preserved so
  note structure and readability remain intact.
- **Name heuristics** - Detect title-prefixed names (`Dr. Jane Doe`), label-prefixed
  names (`Patient: John Smith`), and consecutive Title-Case tokens that resemble
  person names (e.g. `Mary Ann Lopez`).
- **Custom word flagging** - User-supplied terms (facility names, rare surnames,
  study codes) are matched case-insensitively on word boundaries and replaced with
  `[REDACTED_CUSTOM]`.
- **Non-destructive input** - `anonymize()` returns a new string; the original
  text is never mutated.

## What it is used for

Stripping PII from medical records is mandatory before data leaves the clinical
environment:

- **HIPAA / GDPR de-identification** - Remove direct identifiers before exporting
  notes for secondary use.
- **Medical research datasets** - Share clinical narratives with IRB-approved
  studies without exposing patient identity.
- **Cross-institution data sharing** - Transfer records to partners under BAAs
  while minimizing re-identification risk.
- **ML training pipelines** - Prepare labeled clinical text for model development
  without leaking PII into training corpora.
"""

from __future__ import annotations

import re

REDACTED_NAME = "[REDACTED_NAME]"
REDACTED_PHONE = "[REDACTED_PHONE]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
REDACTED_ID = "[REDACTED_ID]"
REDACTED_CUSTOM = "[REDACTED_CUSTOM]"

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)"
)

SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

MRN_PATTERN = re.compile(r"\bMRN-\d{3,}-[A-Z0-9]+\b", re.IGNORECASE)

ALPHANUMERIC_ID_PATTERN = re.compile(r"\b[A-Z]{2,}\d{4,}[A-Z0-9-]*\b")

TITLE_NAME_PATTERN = re.compile(
    r"(?:Dr|Mr|Mrs|Ms|Patient)\.?\s+"
    r"[A-Z][a-z]+(?:['-][A-Za-z]+)?"
    r"(?:\s+[A-Z][a-z]+(?:['-][A-Za-z]+)?){0,2}"
)

TWO_PART_NAME_PATTERN = re.compile(
    r"\b[A-Z][a-z]+(?:['-][A-Za-z]+)?\s+[A-Z][a-z]+(?:['-][A-Za-z]+)?\b"
)


class MedicalRecordAnonymizer:
    """Redact PII from clinical text using regex-based pattern matching."""

    def __init__(self, extra_words: list[str] | None = None) -> None:
        self._extra_words = extra_words or []
        self._custom_patterns = [
            re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            for word in self._extra_words
        ]

    def anonymize(self, text: str) -> str:
        """Return a copy of text with PII replaced by standardized redaction tokens."""
        result = text
        result = EMAIL_PATTERN.sub(REDACTED_EMAIL, result)
        result = PHONE_PATTERN.sub(REDACTED_PHONE, result)
        result = SSN_PATTERN.sub(REDACTED_ID, result)
        result = MRN_PATTERN.sub(REDACTED_ID, result)
        result = ALPHANUMERIC_ID_PATTERN.sub(REDACTED_ID, result)
        for pattern in self._custom_patterns:
            result = pattern.sub(REDACTED_CUSTOM, result)
        result = TITLE_NAME_PATTERN.sub(REDACTED_NAME, result)
        result = TWO_PART_NAME_PATTERN.sub(REDACTED_NAME, result)
        return result


if __name__ == "__main__":
    mock_notes = (
        "Patient John Smith (MRN-00458-XY) was seen by Dr. Emily Carter on 03/15/2025 "
        "at St. Mary's Cardiology. Contact: (555) 987-6543 or john.smith@email.com. "
        "SSN on file: 123-45-6789. Enrolled in CardioStudy trial."
    )

    anonymizer = MedicalRecordAnonymizer(extra_words=["St. Mary's", "CardioStudy"])

    print("Original:")
    print(mock_notes)
    print("\nAnonymized:")
    print(anonymizer.anonymize(mock_notes))
