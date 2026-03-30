"""
PawPal+ — Demo script.
Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # --- Owner ---
    owner = Owner(name="Jordan", available_minutes=90)

    # --- Pets ---
    mochi = Pet(name="Mochi", species="dog", age=3, breed="Shiba Inu")
    luna = Pet(name="Luna", species="cat", age=5, breed="Siamese")

    owner.add_pet(mochi)
    owner.add_pet(luna)

    # --- Tasks for Mochi ---
    mochi.add_task(Task(title="Morning walk",     duration_minutes=30, priority="high",   category="walk"))
    mochi.add_task(Task(title="Breakfast",        duration_minutes=10, priority="high",   category="feeding"))
    mochi.add_task(Task(title="Heartworm tablet", duration_minutes=5,  priority="medium", category="meds"))
    mochi.add_task(Task(title="Brush coat",       duration_minutes=15, priority="low",    category="grooming"))

    # --- Tasks for Luna ---
    luna.add_task(Task(title="Feed Luna",         duration_minutes=10, priority="high",   category="feeding"))
    luna.add_task(Task(title="Litter box clean",  duration_minutes=10, priority="medium", category="grooming"))
    luna.add_task(Task(title="Playtime",          duration_minutes=20, priority="low",    category="enrichment"))

    # --- Build and print schedule ---
    scheduler = Scheduler(owner=owner)
    plan = scheduler.build_plan()
    print(scheduler.explain_plan(plan))

    # --- Show individual task details ---
    print("\n--- All tasks ---")
    for pet, task in owner.get_all_tasks():
        print(f"  {pet.name:8} | {task}")


if __name__ == "__main__":
    main()
