# Clinic Operations

Python utilities for day-to-day clinic operations: catch overlapping appointments, assign shifts under skill and hour limits, normalize intake records, and strip identifiers from clinical notes.

## Programs

| File | What it does |
| --- | --- |
| `detect_scheduling_conflicts.py` | Sorts appointment intervals and reports whether any of them overlap. Back-to-back slots are allowed. |
| `shift_allocator.py` | Fills weekly shifts with employees who have the required skills and remaining hours. |
| `normalize_patient_data.py` | Cleans names, dates, phones, emails, gender, and medical-record numbers into one shape. |
| `medical_record_anonymizer.py` | Replaces emails, phones, IDs, and name-like spans in clinical text with redaction tokens. |

## Requirements

- Python 3.10 or newer

## Run

```bash
python detect_scheduling_conflicts.py
python shift_allocator.py
python normalize_patient_data.py
python medical_record_anonymizer.py
```
