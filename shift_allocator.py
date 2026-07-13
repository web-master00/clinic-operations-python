"""
# Shift Allocator

## What it is

A constraint-based workforce matching utility that assigns employees to weekly
shifts while respecting skill requirements and hour caps:

- **Hard constraints** - An employee may be assigned to a shift only if (1) their
  skillset is a superset of the shift's required skills, and (2) accepting the
  shift would not push their total assigned hours above `max_weekly_hours`.
- **Greedy assignment strategy** - Shifts are processed hardest-first (most required
  skills, then longest duration) so specialized slots are filled before flexible
  staff consume capacity. Among eligible employees, the one with the **most
  remaining hours** is chosen to spread workload and reduce burnout risk.
- **Hour budget tracking** - A running `assigned_hours` map tracks each employee's
  cumulative scheduled time as shifts are filled.
- **Partial success** - The algorithm always completes; filled shifts go in
  `roster`, shifts with no eligible employee go in `unfillable`.

## What it is used for

Automated shift allocation supports day-to-day workforce operations:

- **Maximize scheduling efficiency** - Fill weekly clinic rosters without manual
  spreadsheet matching across skills and availability.
- **Manage labor costs** - Respect contracted hour caps so overtime and agency
  backfill needs surface early via `unfillable` slots.
- **Prevent staff burnout** - Enforce weekly hour limits and distribute assignments
  toward under-utilized qualified staff.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Employee:
    name: str
    max_weekly_hours: float
    skills: frozenset[str]


@dataclass(frozen=True)
class Shift:
    shift_id: str
    day: str
    label: str
    duration_hours: float
    required_skills: frozenset[str]


@dataclass
class AllocationResult:
    roster: dict[str, str]
    unfillable: list[str]
    employee_hours: dict[str, float]


class ShiftAllocator:
    """Assign employees to shifts under skill and weekly-hour constraints."""

    def __init__(self, employees: list[Employee], shifts: list[Shift]) -> None:
        self._employees = employees
        self._shifts = shifts

    def allocate(self) -> AllocationResult:
        assigned_hours = {employee.name: 0.0 for employee in self._employees}
        roster: dict[str, str] = {}
        unfillable: list[str] = []

        sorted_shifts = sorted(
            self._shifts,
            key=lambda shift: (-len(shift.required_skills), -shift.duration_hours),
        )

        for shift in sorted_shifts:
            eligible = [
                employee
                for employee in self._employees
                if shift.required_skills <= employee.skills
                and assigned_hours[employee.name] + shift.duration_hours
                <= employee.max_weekly_hours
            ]

            if not eligible:
                unfillable.append(shift.shift_id)
                continue

            chosen = max(
                eligible,
                key=lambda employee: employee.max_weekly_hours
                - assigned_hours[employee.name],
            )
            roster[shift.shift_id] = chosen.name
            assigned_hours[chosen.name] += shift.duration_hours

        return AllocationResult(
            roster=roster,
            unfillable=unfillable,
            employee_hours=assigned_hours,
        )


def print_schedule_matrix(
    shifts: list[Shift],
    result: AllocationResult,
    employees: list[Employee],
) -> None:
    """Print a fixed-width schedule table and utilization summary."""
    headers = ("Day", "Shift", "Duration", "Required Skills", "Assigned", "Status")
    rows: list[tuple[str, ...]] = []

    for shift in shifts:
        assigned = result.roster.get(shift.shift_id, "UNFILLED")
        status = "FILLED" if shift.shift_id in result.roster else "OPEN"
        skills = ", ".join(sorted(shift.required_skills))
        rows.append(
            (
                shift.day,
                shift.label,
                f"{shift.duration_hours:g}h",
                skills,
                assigned,
                status,
            )
        )

    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows))
        for i in range(len(headers))
    ]

    def format_row(cells: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    separator = "-+-".join("-" * width for width in widths)
    print(format_row(headers))
    print(separator)
    for row in rows:
        print(format_row(row))

    filled = len(result.roster)
    open_slots = len(result.unfillable)
    print(f"\nSummary: {filled} filled, {open_slots} unfillable")

    print("\nEmployee utilization:")
    employee_max = {employee.name: employee.max_weekly_hours for employee in employees}
    for name, hours in sorted(result.employee_hours.items()):
        max_hours = employee_max[name]
        print(f"  {name}: {hours:g}/{max_hours:g} hours")


def _demo_employees() -> list[Employee]:
    return [
        Employee("Alice Chen", 40, frozenset({"rn", "triage", "iv"})),
        Employee("Ben Ortiz", 32, frozenset({"rn", "pediatrics"})),
        Employee("Carla Diaz", 40, frozenset({"rn", "triage", "surgery_assist"})),
        Employee("David Kim", 24, frozenset({"emt", "triage"})),
        Employee("Elena Ruiz", 36, frozenset({"rn", "icu", "iv"})),
        Employee("Frank Ng", 20, frozenset({"emt"})),
    ]


if __name__ == "__main__":
    employees = _demo_employees()
    shifts = [
        Shift("mon_er_am", "Mon", "ER Morning", 8, frozenset({"triage", "rn"})),
        Shift("mon_peds", "Mon", "Pediatrics", 6, frozenset({"rn", "pediatrics"})),
        Shift("tue_surgery", "Tue", "Surgery Prep", 10, frozenset({"rn", "surgery_assist"})),
        Shift("tue_icu", "Tue", "ICU Night", 12, frozenset({"rn", "icu", "iv"})),
        Shift("wed_er_pm", "Wed", "ER Evening", 8, frozenset({"triage", "rn"})),
        Shift("thu_triage", "Thu", "Triage Desk", 6, frozenset({"triage"})),
        Shift("fri_or", "Fri", "OR Support", 10, frozenset({"rn", "surgery_assist"})),
        Shift("sat_urgent", "Sat", "Urgent Care", 8, frozenset({"rn", "triage", "iv"})),
        Shift(
            "sun_picu",
            "Sun",
            "Pediatric ICU",
            8,
            frozenset({"rn", "pediatrics", "icu"}),
        ),
    ]

    allocator = ShiftAllocator(employees, shifts)
    result = allocator.allocate()

    print("Weekly Shift Schedule\n")
    print_schedule_matrix(shifts, result, employees)
