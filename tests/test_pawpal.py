"""
PawPal+ — pytest test suite.
Run with: python -m pytest
"""

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


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status(sample_task):
    """Calling mark_complete() should set completed to True."""
    assert sample_task.completed is False
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_reset_clears_completed_status(sample_task):
    """Calling reset() after mark_complete() should set completed back to False."""
    sample_task.mark_complete()
    sample_task.reset()
    assert sample_task.completed is False


def test_is_high_priority_true_for_high(sample_task):
    """is_high_priority() should return True when priority is 'high'."""
    assert sample_task.is_high_priority() is True


def test_is_high_priority_false_for_low():
    """is_high_priority() should return False when priority is 'low'."""
    task = Task(title="Brush coat", duration_minutes=15, priority="low")
    assert task.is_high_priority() is False


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_task_count(sample_pet, sample_task):
    """Adding a task to a Pet should increase its task list by 1."""
    before = len(sample_pet.tasks)
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == before + 1


def test_remove_task_decreases_task_count(sample_pet, sample_task):
    """Removing a task by title should reduce the task list by 1."""
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


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_add_pet_increases_pet_count(sample_owner, sample_pet):
    """Adding a pet should increase the owner's pet list by 1."""
    before = len(sample_owner.pets)
    sample_owner.add_pet(sample_pet)
    assert len(sample_owner.pets) == before + 1


def test_set_available_time(sample_owner):
    """set_available_time() should update the available_minutes value."""
    sample_owner.set_available_time(60)
    assert sample_owner.available_minutes == 60


def test_get_all_tasks_returns_all_pet_tasks(sample_owner):
    """get_all_tasks() should return a (pet, task) pair for every task across all pets."""
    pet1 = Pet(name="Mochi", species="dog", age=3)
    pet2 = Pet(name="Luna", species="cat", age=5)
    pet1.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    pet2.add_task(Task(title="Feed", duration_minutes=10, priority="high"))
    pet2.add_task(Task(title="Play", duration_minutes=20, priority="low"))
    sample_owner.add_pet(pet1)
    sample_owner.add_pet(pet2)
    all_tasks = sample_owner.get_all_tasks()
    assert len(all_tasks) == 3


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_build_plan_respects_available_time():
    """build_plan() should not schedule more minutes than the owner has available."""
    owner = Owner(name="Alex", available_minutes=30)
    pet = Pet(name="Buddy", species="dog", age=2)
    pet.add_task(Task(title="Long hike",  duration_minutes=60, priority="high"))
    pet.add_task(Task(title="Short walk", duration_minutes=20, priority="medium"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()
    total = sum(e["task"].duration_minutes for e in plan)
    assert total <= owner.available_minutes


def test_build_plan_orders_high_priority_first():
    """High-priority tasks should appear before lower-priority ones in the plan."""
    owner = Owner(name="Sam", available_minutes=120)
    pet = Pet(name="Rex", species="dog", age=4)
    pet.add_task(Task(title="Low task",  duration_minutes=10, priority="low"))
    pet.add_task(Task(title="High task", duration_minutes=10, priority="high"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()
    priorities = [e["task"].priority for e in plan]
    high_idx = priorities.index("high")
    low_idx = priorities.index("low")
    assert high_idx < low_idx


def test_build_plan_excludes_completed_tasks():
    """Tasks already marked complete should not appear in the plan."""
    owner = Owner(name="Taylor", available_minutes=120)
    pet = Pet(name="Cleo", species="cat", age=2)
    done_task = Task(title="Already done", duration_minutes=10, priority="high")
    done_task.mark_complete()
    pet.add_task(done_task)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()
    assert all(e["task"].title != "Already done" for e in plan)
