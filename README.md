# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond basic priority-based planning, PawPal+ includes the following algorithmic features:

- **Sort by duration** — `Scheduler.sort_by_duration()` orders any task list by `duration_minutes` (ascending or descending) using a `lambda` key with Python's `sorted()`.
- **Filter by pet or status** — `filter_by_pet(name)` returns all tasks for a specific animal; `filter_by_status(completed)` separates done tasks from pending ones.
- **Recurring task auto-rescheduling** — When `Pet.mark_task_complete(title)` is called on a `daily` or `weekly` task, it automatically appends a new `Task` instance with a `due_date` advanced by `timedelta(days=1)` or `timedelta(weeks=1)`. Tasks with `frequency="as-needed"` are never auto-rescheduled.
- **Conflict detection** — `Scheduler.detect_conflicts(plan)` scans every pair of scheduled entries for time-block overlaps and returns a list of warning strings rather than raising an exception, so the app can surface warnings to the user without crashing.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
