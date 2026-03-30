# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan daily care tasks for their pets. It uses a priority-based greedy scheduler, supports multiple pets and tasks, detects scheduling conflicts, and auto-reschedules recurring tasks.

## Features

| Feature | Description |
|---|---|
| Owner & pet setup | Enter owner name, available daily time, and multiple pets with species/breed/age |
| Task management | Add tasks with title, duration, priority (high/medium/low), category, and frequency (daily/weekly/as-needed) |
| Priority scheduling | `Scheduler.build_plan()` sorts tasks high → medium → low, then greedily fills the owner's time budget |
| Sort by duration | View tasks ordered by duration (shortest or longest first) using a `lambda` key with `sorted()` |
| Filter by pet or status | Isolate tasks for a single pet or show only pending / completed tasks |
| Recurring auto-rescheduling | Marking a daily/weekly task complete triggers `Task.next_occurrence()`, which uses `timedelta` to append the next due date automatically |
| Conflict detection | `Scheduler.detect_conflicts()` checks every pair of plan entries for time-block overlaps and surfaces warnings in the UI without crashing |
| Unscheduled task list | Tasks that don't fit within today's time budget are displayed separately so nothing is forgotten |
| 35-test suite | `pytest` suite covers all core behaviors and edge cases |

## Demo

> Add a screenshot here once the app is running:
> `<img src="demo_screenshot.png" title="PawPal App" width="700" alt="PawPal App" />`

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
python -m streamlit run app.py
```

## Smarter Scheduling

Beyond basic priority-based planning, PawPal+ includes the following algorithmic features:

- **Sort by duration** — `Scheduler.sort_by_duration()` orders any task list by `duration_minutes` (ascending or descending) using a `lambda` key with Python's `sorted()`.
- **Filter by pet or status** — `filter_by_pet(name)` returns all tasks for a specific animal; `filter_by_status(completed)` separates done tasks from pending ones.
- **Recurring task auto-rescheduling** — When `Pet.mark_task_complete(title)` is called on a `daily` or `weekly` task, it automatically appends a new `Task` instance with a `due_date` advanced by `timedelta(days=1)` or `timedelta(weeks=1)`. Tasks with `frequency="as-needed"` are never auto-rescheduled.
- **Conflict detection** — `Scheduler.detect_conflicts(plan)` scans every pair of scheduled entries for time-block overlaps and returns a list of warning strings rather than raising an exception, so the app can surface warnings to the user without crashing.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

The suite contains **35 tests** across four classes and covers:

| Area | What is tested |
|---|---|
| `Task` | `mark_complete`, `reset`, `is_high_priority`, `next_occurrence` (daily/weekly/as-needed) |
| `Pet` | `add_task`, `remove_task`, `get_pending_tasks`, `mark_task_complete` + recurrence side-effects |
| `Owner` | `add_pet`, `set_available_time`, `get_all_tasks` |
| `Scheduler` | `build_plan` (priority order, time budget, completed exclusion), `sort_by_duration` (asc/desc, no mutation), `filter_by_pet`, `filter_by_status`, `detect_conflicts` |
| Edge cases | Pet with no tasks, owner with no pets, zero available time, unknown pet name filter, back-to-back tasks (no false conflict), empty plan conflict check |

**Confidence level: 4 / 5**
Core happy paths and the most likely edge cases are covered. The main gap is integration testing between `app.py` (Streamlit session state) and the logic layer, and multi-day recurrence chains beyond a single next occurrence.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
