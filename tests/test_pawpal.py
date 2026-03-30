"""
PawPal+ — pytest test suite.
Run with: python -m pytest

Covers:
  - Task: mark_complete, reset, is_high_priority, next_occurrence (recurrence)
  - Pet: add/remove task, get_pending_tasks, mark_task_complete + recurrence
  - Owner: add pet, set_available_time, get_all_tasks
  - Scheduler: build_plan (priority, time budget, completed exclusion),
               sort_by_duration, filter_by_pet, filter_by_status,
               detect_conflicts
  - Edge cases: pet with no tasks, owner with no pets, zero-time budget,
                as-needed recurrence, exact-same-start conflict
"""

from datetime import date, timedelta

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    return Task(title="Morning walk", duration_minutes=30, priority="high", category="walk")


@pytest.fixture
def sample_pet():
    return Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")


@pytest.fixture
def sample_owner():
    return Owner(name="Jordan", available_minutes=90)


@pytest.fixture
def owner_with_pets():
    """Owner pre-loaded with two pets and a mix of tasks."""
    owner = Owner(name="Jordan", available_minutes=90)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=5)
    mochi.add_task(Task(title="Walk",  duration_minutes=30, priority="high",   frequency="daily"))
    mochi.add_task(Task(title="Brush", duration_minutes=15, priority="low",    frequency="weekly"))
    luna.add_task( Task(title="Feed",  duration_minutes=10, priority="high",   frequency="daily"))
    luna.add_task( Task(title="Play",  duration_minutes=20, priority="medium", frequency="as-needed"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


# ---------------------------------------------------------------------------
# Task — basic behaviour
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status(sample_task):
    """mark_complete() should flip completed from False to True."""
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_reset_clears_completed_status(sample_task):
    """reset() should restore completed to False after mark_complete()."""
    sample_task.mark_complete()
    sample_task.reset()
    assert sample_task.completed is False


def test_is_high_priority_true_for_high(sample_task):
    """is_high_priority() returns True for a high-priority task."""
    assert sample_task.is_high_priority() is True


def test_is_high_priority_false_for_low():
    """is_high_priority() returns False for a low-priority task."""
    task = Task(title="Brush coat", duration_minutes=15, priority="low")
    assert task.is_high_priority() is False


# ---------------------------------------------------------------------------
# Task — recurrence (next_occurrence)
# ---------------------------------------------------------------------------

def test_daily_task_next_occurrence_is_tomorrow():
    """A daily task's next_occurrence() should have due_date = today + 1 day."""
    today = date.today()
    task = Task(title="Walk", duration_minutes=20, priority="high",
                frequency="daily", due_date=today)
    task.mark_complete()
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_weekly_task_next_occurrence_is_next_week():
    """A weekly task's next_occurrence() should advance due_date by 7 days."""
    today = date.today()
    task = Task(title="Bath", duration_minutes=30, priority="medium",
                frequency="weekly", due_date=today)
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_as_needed_task_has_no_next_occurrence():
    """A task with frequency='as-needed' should return None from next_occurrence()."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high",
                frequency="as-needed")
    assert task.next_occurrence() is None


def test_next_occurrence_copies_task_attributes():
    """next_occurrence() should preserve title, duration, priority, and category."""
    task = Task(title="Meds", duration_minutes=5, priority="medium",
                category="meds", frequency="daily")
    nxt = task.next_occurrence()
    assert nxt.title    == task.title
    assert nxt.duration_minutes == task.duration_minutes
    assert nxt.priority == task.priority
    assert nxt.category == task.category


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_task_count(sample_pet, sample_task):
    """add_task() should grow the task list by exactly 1."""
    before = len(sample_pet.tasks)
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == before + 1


def test_remove_task_removes_by_title(sample_pet, sample_task):
    """remove_task() should eliminate all tasks with the given title."""
    sample_pet.add_task(sample_task)
    sample_pet.remove_task(sample_task.title)
    assert all(t.title != sample_task.title for t in sample_pet.tasks)


def test_get_pending_tasks_excludes_completed(sample_pet):
    """get_pending_tasks() should not include tasks marked complete."""
    t1 = Task(title="Walk", duration_minutes=20, priority="high")
    t2 = Task(title="Feed", duration_minutes=10, priority="medium")
    sample_pet.add_task(t1)
    sample_pet.add_task(t2)
    t1.mark_complete()
    pending = sample_pet.get_pending_tasks()
    assert t1 not in pending
    assert t2 in pending


def test_pet_with_no_tasks_has_empty_pending(sample_pet):
    """A pet with no tasks should return an empty pending list (edge case)."""
    assert sample_pet.get_pending_tasks() == []


def test_mark_task_complete_appends_recurrence(sample_pet):
    """mark_task_complete() on a daily task should add a new future task."""
    today = date.today()
    task = Task(title="Walk", duration_minutes=30, priority="high",
                frequency="daily", due_date=today)
    sample_pet.add_task(task)
    sample_pet.mark_task_complete("Walk")

    walk_tasks = [t for t in sample_pet.tasks if t.title == "Walk"]
    assert len(walk_tasks) == 2                          # original + recurrence
    completed_tasks = [t for t in walk_tasks if t.completed]
    pending_tasks   = [t for t in walk_tasks if not t.completed]
    assert len(completed_tasks) == 1
    assert len(pending_tasks)   == 1
    assert pending_tasks[0].due_date == today + timedelta(days=1)


def test_mark_task_complete_no_recurrence_for_as_needed(sample_pet):
    """mark_task_complete() on an as-needed task should NOT add a new task."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high",
                frequency="as-needed")
    sample_pet.add_task(task)
    sample_pet.mark_task_complete("Vet visit")
    assert len(sample_pet.tasks) == 1       # no new task appended


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_add_pet_increases_pet_count(sample_owner, sample_pet):
    """add_pet() should grow the pets list by 1."""
    before = len(sample_owner.pets)
    sample_owner.add_pet(sample_pet)
    assert len(sample_owner.pets) == before + 1


def test_set_available_time(sample_owner):
    """set_available_time() should update available_minutes."""
    sample_owner.set_available_time(60)
    assert sample_owner.available_minutes == 60


def test_get_all_tasks_returns_all_pet_tasks(sample_owner):
    """get_all_tasks() should return one (pet, task) pair per task across all pets."""
    pet1 = Pet(name="Mochi", species="dog", age=3)
    pet2 = Pet(name="Luna",  species="cat", age=5)
    pet1.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    pet2.add_task(Task(title="Feed", duration_minutes=10, priority="high"))
    pet2.add_task(Task(title="Play", duration_minutes=20, priority="low"))
    sample_owner.add_pet(pet1)
    sample_owner.add_pet(pet2)
    assert len(sample_owner.get_all_tasks()) == 3


def test_owner_with_no_pets_has_no_tasks(sample_owner):
    """An owner with no pets should return an empty task list (edge case)."""
    assert sample_owner.get_all_tasks() == []


# ---------------------------------------------------------------------------
# Scheduler — build_plan
# ---------------------------------------------------------------------------

def test_build_plan_respects_available_time():
    """build_plan() must not exceed the owner's available_minutes."""
    owner = Owner(name="Alex", available_minutes=30)
    pet   = Pet(name="Buddy", species="dog", age=2)
    pet.add_task(Task(title="Long hike",  duration_minutes=60, priority="high"))
    pet.add_task(Task(title="Short walk", duration_minutes=20, priority="medium"))
    owner.add_pet(pet)
    plan  = Scheduler(owner).build_plan()
    total = sum(e["task"].duration_minutes for e in plan)
    assert total <= owner.available_minutes


def test_build_plan_orders_high_priority_first():
    """High-priority tasks must appear before low-priority tasks in the plan."""
    owner = Owner(name="Sam", available_minutes=120)
    pet   = Pet(name="Rex", species="dog", age=4)
    pet.add_task(Task(title="Low task",  duration_minutes=10, priority="low"))
    pet.add_task(Task(title="High task", duration_minutes=10, priority="high"))
    owner.add_pet(pet)
    plan       = Scheduler(owner).build_plan()
    priorities = [e["task"].priority for e in plan]
    assert priorities.index("high") < priorities.index("low")


def test_build_plan_excludes_completed_tasks():
    """Tasks already completed should never appear in the plan."""
    owner = Owner(name="Taylor", available_minutes=120)
    pet   = Pet(name="Cleo", species="cat", age=2)
    done  = Task(title="Already done", duration_minutes=10, priority="high")
    done.mark_complete()
    pet.add_task(done)
    owner.add_pet(pet)
    plan = Scheduler(owner).build_plan()
    assert all(e["task"].title != "Already done" for e in plan)


def test_build_plan_empty_when_no_tasks(sample_owner):
    """build_plan() should return an empty list when the owner has no pets (edge case)."""
    plan = Scheduler(sample_owner).build_plan()
    assert plan == []


def test_build_plan_empty_when_zero_time():
    """build_plan() should return empty list when available_minutes is 0 (edge case)."""
    owner = Owner(name="Busy", available_minutes=0)
    pet   = Pet(name="Spark", species="dog", age=1)
    pet.add_task(Task(title="Walk", duration_minutes=10, priority="high"))
    owner.add_pet(pet)
    plan = Scheduler(owner).build_plan()
    assert plan == []


# ---------------------------------------------------------------------------
# Scheduler — sorting
# ---------------------------------------------------------------------------

def test_sort_by_duration_ascending(owner_with_pets):
    """sort_by_duration() should return tasks shortest-first by default."""
    scheduler = Scheduler(owner_with_pets)
    pairs     = owner_with_pets.get_all_tasks()
    sorted_pairs = scheduler.sort_by_duration(pairs)
    durations = [task.duration_minutes for _, task in sorted_pairs]
    assert durations == sorted(durations)


def test_sort_by_duration_descending(owner_with_pets):
    """sort_by_duration(descending=True) should return longest tasks first."""
    scheduler    = Scheduler(owner_with_pets)
    pairs        = owner_with_pets.get_all_tasks()
    sorted_pairs = scheduler.sort_by_duration(pairs, descending=True)
    durations    = [task.duration_minutes for _, task in sorted_pairs]
    assert durations == sorted(durations, reverse=True)


def test_sort_does_not_mutate_original(owner_with_pets):
    """sort_by_duration() should not change the original list in place."""
    scheduler = Scheduler(owner_with_pets)
    pairs     = owner_with_pets.get_all_tasks()
    original_order = [t.title for _, t in pairs]
    scheduler.sort_by_duration(pairs)
    assert [t.title for _, t in pairs] == original_order


# ---------------------------------------------------------------------------
# Scheduler — filtering
# ---------------------------------------------------------------------------

def test_filter_by_pet_returns_only_that_pet(owner_with_pets):
    """filter_by_pet() should return only tasks belonging to the named pet."""
    scheduler = Scheduler(owner_with_pets)
    result    = scheduler.filter_by_pet("Mochi")
    assert all(pet.name == "Mochi" for pet, _ in result)
    assert len(result) > 0


def test_filter_by_pet_unknown_name_returns_empty(owner_with_pets):
    """filter_by_pet() with a name that doesn't exist should return [] (edge case)."""
    scheduler = Scheduler(owner_with_pets)
    assert scheduler.filter_by_pet("Ghost") == []


def test_filter_by_status_pending(owner_with_pets):
    """filter_by_status(completed=False) should return only incomplete tasks."""
    scheduler = Scheduler(owner_with_pets)
    pending   = scheduler.filter_by_status(completed=False)
    assert all(not task.completed for _, task in pending)


def test_filter_by_status_completed(owner_with_pets):
    """filter_by_status(completed=True) should return only finished tasks."""
    mochi = owner_with_pets.pets[0]
    mochi.tasks[0].mark_complete()
    scheduler = Scheduler(owner_with_pets)
    done      = scheduler.filter_by_status(completed=True)
    assert all(task.completed for _, task in done)
    assert len(done) == 1


# ---------------------------------------------------------------------------
# Scheduler — conflict detection
# ---------------------------------------------------------------------------

def _make_entry(pet, task, start):
    """Helper: build a plan entry dict."""
    return {"pet": pet, "task": task, "start": start, "reason": "test"}


def test_no_conflicts_when_tasks_are_sequential():
    """Sequential non-overlapping tasks should produce no conflict warnings."""
    pet   = Pet(name="Buddy", species="dog", age=2)
    t1    = Task(title="Walk",  duration_minutes=20, priority="high")
    t2    = Task(title="Feed",  duration_minutes=10, priority="high")
    plan  = [_make_entry(pet, t1, 0), _make_entry(pet, t2, 20)]
    owner = Owner(name="Sam", available_minutes=60)
    owner.add_pet(pet)
    warnings = Scheduler(owner).detect_conflicts(plan)
    assert warnings == []


def test_conflict_detected_when_tasks_overlap():
    """Two tasks whose time blocks overlap should generate a conflict warning."""
    pet  = Pet(name="Rex", species="dog", age=3)
    t1   = Task(title="Walk",  duration_minutes=30, priority="high")   # 0-30
    t2   = Task(title="Feed",  duration_minutes=10, priority="high")   # 5-15 (overlaps)
    plan = [_make_entry(pet, t1, 0), _make_entry(pet, t2, 5)]
    owner = Owner(name="Alex", available_minutes=60)
    owner.add_pet(pet)
    warnings = Scheduler(owner).detect_conflicts(plan)
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


def test_conflict_detected_for_exact_same_start_time():
    """Two tasks starting at the same minute should always be flagged."""
    pet  = Pet(name="Cleo", species="cat", age=4)
    t1   = Task(title="Groom", duration_minutes=15, priority="medium")
    t2   = Task(title="Play",  duration_minutes=10, priority="low")
    plan = [_make_entry(pet, t1, 0), _make_entry(pet, t2, 0)]
    owner = Owner(name="Morgan", available_minutes=60)
    owner.add_pet(pet)
    warnings = Scheduler(owner).detect_conflicts(plan)
    assert len(warnings) >= 1


def test_no_conflict_for_back_to_back_tasks():
    """Tasks that are exactly back-to-back (end == next start) should not conflict."""
    pet  = Pet(name="Max", species="dog", age=2)
    t1   = Task(title="Walk",  duration_minutes=20, priority="high")   # 0-20
    t2   = Task(title="Feed",  duration_minutes=10, priority="high")   # 20-30 (no overlap)
    plan = [_make_entry(pet, t1, 0), _make_entry(pet, t2, 20)]
    owner = Owner(name="Lee", available_minutes=60)
    owner.add_pet(pet)
    warnings = Scheduler(owner).detect_conflicts(plan)
    assert warnings == []


def test_empty_plan_has_no_conflicts():
    """An empty plan should return no warnings (edge case)."""
    owner    = Owner(name="Empty", available_minutes=60)
    warnings = Scheduler(owner).detect_conflicts([])
    assert warnings == []
