"""
PawPal+ — Backend logic layer.
Classes: Task, Pet, Owner, Scheduler
"""

from __future__ import annotations

from dataclasses import dataclass, field
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

    def is_high_priority(self) -> bool:
        """Return True when priority is 'high'."""
        return self.priority == "high"

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def reset(self) -> None:
        """Reset completion status (e.g. start of a new day)."""
        self.completed = False

    def __str__(self) -> str:
        status = "[x]" if self.completed else "[ ]"
        return (
            f"{status} {self.title} ({self.duration_minutes} min, "
            f"{self.priority} priority)"
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
        pairs: list[tuple[Pet, Task]] = []
        for pet in self.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs

    def __str__(self) -> str:
        pet_names = ", ".join(p.name for p in self.pets) or "no pets yet"
        return f"{self.name} (available: {self.available_minutes} min, pets: {pet_names})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Builds a daily care plan by retrieving tasks from all of an owner's pets.

    Strategy: collect pending tasks across all pets, sort by priority
    (high → medium → low), then greedily fit them within the owner's
    available_minutes.
    """

    def __init__(self, owner: Owner):
        self.owner = owner

    def _collect_tasks(self) -> list[tuple[Pet, Task]]:
        """Retrieve all pending (pet, task) pairs from the owner's pets."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed
        ]

    def build_plan(self) -> list[dict]:
        """
        Select and order tasks that fit within the owner's available time.

        Returns a list of dicts, each with:
            - pet      (Pet)
            - task     (Task)
            - start    (int)  minutes from start of day
            - reason   (str)  brief explanation
        """
        candidates = sorted(
            self._collect_tasks(),
            key=lambda pair: _PRIORITY_ORDER.get(pair[1].priority, 99),
        )

        plan: list[dict] = []
        elapsed = 0

        for pet, task in candidates:
            if elapsed + task.duration_minutes <= self.owner.available_minutes:
                reason = (
                    f"{task.priority.capitalize()}-priority care for {pet.name}"
                )
                plan.append(
                    {
                        "pet": pet,
                        "task": task,
                        "start": elapsed,
                        "reason": reason,
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
        """Mark every task in the plan as completed."""
        for entry in plan:
            entry["task"].mark_complete()
