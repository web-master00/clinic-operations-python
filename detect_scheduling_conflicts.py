"""
# Scheduling Conflict Detector

## What it is

A utility for detecting whether any appointment intervals in a daily schedule overlap.
Intervals are expressed as `(start, end)` tuples of minutes from midnight (e.g.
`(600, 630)` is 10:00 AM to 10:30 AM).

**Brute-force alternative:** Compare every pair of intervals - O(n²) time. This works
for tiny schedules but becomes impractical when validating a full clinic day with
hundreds of provider, room, or equipment bookings.

**Chosen approach: sort + linear scan**

1. Sort intervals by start time - O(n log n).
2. Walk the sorted list once, tracking the maximum end time seen so far - O(n).
3. If any interval starts before that maximum end, a conflict exists.

**Overlap rule:** Two intervals conflict if they share any minute. After sorting,
that means `current_start < max_previous_end`. Back-to-back slots where one ends
exactly when the next begins (e.g. `(600, 630)` then `(630, 645)`) are **not**
conflicts.

**Complexity:** O(n log n) time, O(n) auxiliary space for the sorted copy. The
input list is not mutated.

## What it is used for

Hospital and clinic scheduling software must prevent double-booking of limited
resources. Conflict detection supports:

- **Provider and room scheduling** - Avoid assigning the same doctor, exam room, or
  imaging suite to two patients at once.
- **Batch validation** - Check imported or bulk-scheduled appointment files before
  writing them to the EHR calendar.
- **Real-time booking** - Reject conflicting slots during patient self-scheduling or
  front-desk booking before a confirmation is sent.
"""


def has_scheduling_conflicts(appointments: list[tuple[int, int]]) -> bool:
    """Return True if any appointment intervals overlap, False otherwise."""
    valid = [(start, end) for start, end in appointments if start < end]
    if len(valid) < 2:
        return False

    sorted_appointments = sorted(valid, key=lambda interval: interval[0])
    max_end = sorted_appointments[0][1]

    for start, end in sorted_appointments[1:]:
        if start < max_end:
            return True
        max_end = max(max_end, end)

    return False


if __name__ == "__main__":
    overlapping_appointments = [(600, 630), (615, 645)]  # 10:00-10:30 vs 10:15-10:45
    non_overlapping_appointments = [(540, 570), (600, 630), (630, 660)]  # 9:00-9:30, 10:00-10:30, 10:30-11:00

    print("Overlapping appointments:")
    print(f"  intervals: {overlapping_appointments}")
    print(f"  has conflict: {has_scheduling_conflicts(overlapping_appointments)}")

    print("\nNon-overlapping appointments:")
    print(f"  intervals: {non_overlapping_appointments}")
    print(f"  has conflict: {has_scheduling_conflicts(non_overlapping_appointments)}")
