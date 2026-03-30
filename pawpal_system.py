"""
PawPal+ — Backend logic layer.
Classes: Task, Pet, Owner, Scheduler
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

# Priority ordering used for sorting
_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care activity with duration, priority, and completion state."""

    title: str
    duration_minutes: int
    priority: Literal["low", "medium", "high"]
    category: str = "general"       # "walk", "feeding", "meds", "grooming", …
    frequency: str = "daily"        # "daily", "weekly", "as-needed"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def is_high_priority(self) -> bool:
        """Return True when priority is 'high'."""
        return self.priority == "high"

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def reset(self) -> None:
        """Reset completion status (e.g. start of a new day)."""
        self.completed = False

    def next_occurrence(self) -> Task | None:
        """
        Return a fresh Task for the next occurrence of a recurring task.

        Returns None if frequency is 'as-needed' (no automatic recurrence).
        Uses timedelta to advance due_date by 1 day (daily) or 7 days (weekly).
        """
        if self.frequency == "daily":
            delta = timedelta(days=1)
        elif self.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None  # "as-needed" — no automatic next occurrence

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            completed=False,
            due_date=self.due_date + delta,
        )

    def __str__(self) -> str:
        status = "[x]" if self.completed else "[ ]"
        return (
            f"{status} {self.title} ({self.duration_minutes} min, "
            f"{self.priority} priority, due {self.due_date})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet belonging to an Owner; holds its own task list."""

    name: str
    species: str            # "dog", "cat", "other"
    age: int                # years
    breed: str = "unknown"
    tasks: list[Task] = field(default_factory=list)

    def describe(self) -> str:
        """Return a short human-readable description of the pet."""
        return f"{self.name} ({self.breed} {self.species}, age {self.age})"

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title from this pet's list."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been completed today."""
        return [t for t in self.tasks if not t.completed]

    def mark_task_complete(self, title: str) -> None:
        """
        Mark a task complete by title and automatically append its next
        occurrence to the pet's task list if the task is recurring.
        """
        for task in self.tasks:
            if task.title == title and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    self.tasks.append(next_task)
                break

    def __str__(self) -> str:
        return self.describe()


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily time constraints."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = []   # e.g. ["morning", "outdoors"]
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's household."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != name]

    def set_available_time(self, minutes: int) -> None:
        """Update how many minutes the owner has available today."""
        self.available_minutes = minutes

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [
            (pet, task)
            for pet in self.pets
            for task in pet.tasks
        ]

    def __str__(self) -> str:
        pet_names = ", ".join(p.name for p in self.pets) or "no pets yet"
        return f"{self.name} (available: {self.available_minutes} min, pets: {pet_names})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Builds a daily care plan by retrieving tasks from all of an owner's pets.

    Strategy: collect pending tasks, sort by priority (high → medium → low),
    then greedily fit them within the owner's available_minutes.
    Also provides sorting, filtering, and conflict detection utilities.
    """

    def __init__(self, owner: Owner):
        self.owner = owner

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_tasks(self) -> list[tuple[Pet, Task]]:
        """Retrieve all pending (pet, task) pairs from the owner's pets."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed
        ]

    # ------------------------------------------------------------------
    # Step 2 — Sorting
    # ------------------------------------------------------------------

    def sort_by_duration(
        self, pairs: list[tuple[Pet, Task]], descending: bool = False
    ) -> list[tuple[Pet, Task]]:
        """
        Sort (pet, task) pairs by task duration_minutes using a lambda key.

        Args:
            pairs: list of (Pet, Task) tuples to sort.
            descending: if True, longest tasks come first.

        Returns:
            A new sorted list; the original is not modified.
        """
        return sorted(pairs, key=lambda pair: pair[1].duration_minutes, reverse=descending)

    # ------------------------------------------------------------------
    # Step 2 — Filtering
    # ------------------------------------------------------------------

    def filter_by_pet(self, pet_name: str) -> list[tuple[Pet, Task]]:
        """
        Return all (pet, task) pairs belonging to the named pet.

        Args:
            pet_name: exact name of the pet to filter by.
        """
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if pet.name == pet_name
        ]

    def filter_by_status(self, completed: bool) -> list[tuple[Pet, Task]]:
        """
        Return (pet, task) pairs whose completion status matches the argument.

        Args:
            completed: True to get finished tasks, False to get pending tasks.
        """
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if task.completed == completed
        ]

    # ------------------------------------------------------------------
    # Step 4 — Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, plan: list[dict]) -> list[str]:
        """
        Scan a built plan for time-overlap conflicts.

        Two entries conflict when the first task's time block
        (start → start + duration) overlaps with a later task's block,
        regardless of which pet they belong to.

        Returns a list of warning strings (empty if no conflicts).
        """
        warnings: list[str] = []
        for i, a in enumerate(plan):
            a_start = a["start"]
            a_end = a_start + a["task"].duration_minutes
            for b in plan[i + 1 :]:
                b_start = b["start"]
                b_end = b_start + b["task"].duration_minutes
                # Overlap when one interval starts before the other ends
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"CONFLICT: '{a['task'].title}' ({a['pet'].name}, "
                        f"{a_start}-{a_end} min) overlaps with "
                        f"'{b['task'].title}' ({b['pet'].name}, "
                        f"{b_start}-{b_end} min)"
                    )
        return warnings

    # ------------------------------------------------------------------
    # Core planning
    # ------------------------------------------------------------------

    def build_plan(self) -> list[dict]:
        """
        Select and order tasks that fit within the owner's available time.

        Tasks are sorted by priority (high first), then greedily scheduled.
        Returns a list of dicts, each with:
            - pet      (Pet)
            - task     (Task)
            - start    (int)  cumulative minutes from the start of the day
            - reason   (str)  brief human-readable explanation
        """
        candidates = sorted(
            self._collect_tasks(),
            key=lambda pair: _PRIORITY_ORDER.get(pair[1].priority, 99),
        )

        plan: list[dict] = []
        elapsed = 0

        for pet, task in candidates:
            if elapsed + task.duration_minutes <= self.owner.available_minutes:
                plan.append(
                    {
                        "pet": pet,
                        "task": task,
                        "start": elapsed,
                        "reason": f"{task.priority.capitalize()}-priority care for {pet.name}",
                    }
                )
                elapsed += task.duration_minutes

        return plan

    def explain_plan(self, plan: list[dict]) -> str:
        """Return a formatted, human-readable summary of the generated plan."""
        if not plan:
            return "No tasks fit within the available time today."

        lines = [
            f"=== Today's Schedule for {self.owner.name} ===",
            f"Available time: {self.owner.available_minutes} minutes\n",
        ]
        for entry in plan:
            pet: Pet = entry["pet"]
            task: Task = entry["task"]
            start: int = entry["start"]
            reason: str = entry["reason"]
            lines.append(
                f"  {start:>3} min  |  {task.title:<25}  |  {pet.name:<10}  |  {reason}"
            )

        total = sum(e["task"].duration_minutes for e in plan)
        lines.append(f"\nTotal scheduled: {total} / {self.owner.available_minutes} minutes")
        return "\n".join(lines)

    def mark_all_complete(self, plan: list[dict]) -> None:
        """Mark every task in the plan as completed via the pet's method (triggers recurrence)."""
        for entry in plan:
            entry["pet"].mark_task_complete(entry["task"].title)
