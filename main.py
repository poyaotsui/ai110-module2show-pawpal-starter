"""
PawPal+ — Demo script.
Exercises: schedule building, sort_by_duration, filter_by_pet/status,
           recurring task auto-rescheduling, and conflict detection.
Run with: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def section(title: str) -> None:
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print('=' * 55)


def main() -> None:
    # ----------------------------------------------------------------
    # Setup: owner + two pets
    # ----------------------------------------------------------------
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    luna  = Pet(name="Luna",  species="cat", age=5, breed="Siamese")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks added deliberately OUT OF duration order to test sorting
    mochi.add_task(Task(title="Brush coat",       duration_minutes=15, priority="low",    category="grooming",    frequency="weekly"))
    mochi.add_task(Task(title="Morning walk",      duration_minutes=30, priority="high",   category="walk",        frequency="daily"))
    mochi.add_task(Task(title="Heartworm tablet",  duration_minutes=5,  priority="medium", category="meds",        frequency="weekly"))
    mochi.add_task(Task(title="Breakfast",         duration_minutes=10, priority="high",   category="feeding",     frequency="daily"))

    luna.add_task(Task(title="Feed Luna",          duration_minutes=10, priority="high",   category="feeding",     frequency="daily"))
    luna.add_task(Task(title="Litter box clean",   duration_minutes=10, priority="medium", category="grooming",    frequency="daily"))
    luna.add_task(Task(title="Playtime",           duration_minutes=20, priority="low",    category="enrichment",  frequency="as-needed"))

    scheduler = Scheduler(owner=owner)

    # ----------------------------------------------------------------
    # 1. Basic schedule
    # ----------------------------------------------------------------
    section("1. Today's Schedule (priority-sorted)")
    plan = scheduler.build_plan()
    print(scheduler.explain_plan(plan))

    # ----------------------------------------------------------------
    # 2. Conflict detection — inject an artificial overlap to demonstrate
    # ----------------------------------------------------------------
    section("2. Conflict Detection")
    # Build a fake plan where two tasks start at the same time
    conflict_plan = [
        {"pet": mochi, "task": mochi.tasks[1], "start": 0,  "reason": "demo"},
        {"pet": luna,  "task": luna.tasks[0],  "start": 5,  "reason": "demo"},  # overlaps walk (0-30)
        {"pet": mochi, "task": mochi.tasks[3], "start": 30, "reason": "demo"},  # no overlap
    ]
    conflicts = scheduler.detect_conflicts(conflict_plan)
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts detected.")

    # ----------------------------------------------------------------
    # 3. Sort by duration (shortest first)
    # ----------------------------------------------------------------
    section("3. All tasks sorted by duration (shortest first)")
    all_pairs = owner.get_all_tasks()
    for pet, task in scheduler.sort_by_duration(all_pairs):
        print(f"  {task.duration_minutes:>3} min  |  {task.title:<25}  |  {pet.name}")

    # ----------------------------------------------------------------
    # 4. Filter — tasks for Mochi only
    # ----------------------------------------------------------------
    section("4. Filter: Mochi's tasks only")
    for pet, task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    # ----------------------------------------------------------------
    # 5. Recurring task auto-rescheduling
    # ----------------------------------------------------------------
    section("5. Recurring task auto-rescheduling")
    today = date.today()
    print(f"  Marking 'Morning walk' complete (frequency=daily, due {today})")
    mochi.mark_task_complete("Morning walk")

    # The new occurrence should now be in Mochi's task list
    recurring = [t for t in mochi.tasks if t.title == "Morning walk"]
    for t in recurring:
        marker = "(original - done)" if t.completed else "(auto-created next occurrence)"
        print(f"    {t.due_date}  {marker}")

    # ----------------------------------------------------------------
    # 6. Filter — completed vs pending after marking complete
    # ----------------------------------------------------------------
    section("6. Filter: pending vs completed tasks")
    pending   = scheduler.filter_by_status(completed=False)
    completed = scheduler.filter_by_status(completed=True)
    print(f"  Pending  : {len(pending)} task(s)")
    print(f"  Completed: {len(completed)} task(s)")
    for pet, task in completed:
        print(f"    [done] {task.title} ({pet.name})")


if __name__ == "__main__":
    main()
