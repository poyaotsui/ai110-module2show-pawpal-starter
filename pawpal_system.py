"""
PawPal+ — Backend logic layer.
Classes: Owner, Pet, Task, Scheduler
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Data classes (simple value-holding objects)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet care task (walk, feeding, medication, etc.)."""

    title: str
    duration_minutes: int
    priority: Literal["low", "medium", "high"]
    category: str = "general"  # e.g. "walk", "feeding", "meds", "grooming"

    def is_high_priority(self) -> bool:
        """Return True if the task is marked high priority."""
        pass


@dataclass
class Pet:
    """Represents a pet in the system."""

    name: str
    species: str          # "dog", "cat", "other"
    age: int              # in years
    breed: str = "unknown"

    def describe(self) -> str:
        """Return a short human-readable description of the pet."""
        pass


# ---------------------------------------------------------------------------
# Owner class
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily constraints."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = []   # e.g. ["morning", "outdoors"]
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list."""
        pass

    def set_available_time(self, minutes: int) -> None:
        """Update how many minutes the owner has today."""
        pass


# ---------------------------------------------------------------------------
# Scheduler class
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Builds a daily care plan for an owner's pet.

    Strategy: sort tasks by priority (high → medium → low), then greedily
    fit them within the owner's available_minutes.
    """

    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the pool of candidate tasks."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove a task by title from the pool."""
        pass

    def build_plan(self) -> list[dict]:
        """
        Select and order tasks that fit within the owner's available time.

        Returns a list of dicts, each containing:
            - task (Task)
            - start_minute (int)
            - reason (str)
        """
        pass

    def explain_plan(self, plan: list[dict]) -> str:
        """Return a human-readable summary of the generated plan."""
        pass
