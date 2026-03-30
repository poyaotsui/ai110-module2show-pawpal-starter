import streamlit as st

# Step 1: Import logic layer
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("PawPal+")

# ---------------------------------------------------------------------------
# Step 2: Session state — initialise owner once; persists across reruns
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None   # created when the user sets their name

# ---------------------------------------------------------------------------
# Owner setup
# ---------------------------------------------------------------------------

st.header("1. Owner Info")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=90, step=10
    )
    if st.form_submit_button("Save owner"):
        st.session_state.owner = Owner(
            name=owner_name, available_minutes=int(available_minutes)
        )
        st.success(f"Owner saved: {st.session_state.owner}")

if st.session_state.owner is None:
    st.info("Fill in your name and save to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Step 3a: Add a pet — calls owner.add_pet()
# ---------------------------------------------------------------------------

st.divider()
st.header("2. Pets")

with st.form("add_pet_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    with col4:
        breed = st.text_input("Breed", value="unknown")

    if st.form_submit_button("Add pet"):
        # Wire UI → Pet class → owner.add_pet()
        new_pet = Pet(name=pet_name, species=species, age=int(age), breed=breed)
        owner.add_pet(new_pet)
        st.success(f"Added {new_pet.describe()}")

if owner.pets:
    st.write("**Your pets:**")
    for pet in owner.pets:
        st.markdown(f"- {pet.describe()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets added yet.")

# ---------------------------------------------------------------------------
# Step 3b: Add a task to a pet — calls pet.add_task()
# ---------------------------------------------------------------------------

st.divider()
st.header("3. Tasks")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            target_pet = st.selectbox("For pet", [p.name for p in owner.pets])
        with col2:
            task_title = st.text_input("Task title", value="Morning walk")
        with col3:
            duration = st.number_input(
                "Duration (min)", min_value=1, max_value=240, value=20
            )
        with col4:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        category = st.text_input("Category (optional)", value="general")

        if st.form_submit_button("Add task"):
            # Wire UI → Task class → pet.add_task()
            pet_obj = next(p for p in owner.pets if p.name == target_pet)
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
            )
            pet_obj.add_task(new_task)
            st.success(f"Added task '{task_title}' to {target_pet}")

    # Show all current tasks grouped by pet
    any_tasks = any(p.tasks for p in owner.pets)
    if any_tasks:
        for pet in owner.pets:
            if pet.tasks:
                st.markdown(f"**{pet.name}**")
                rows = [
                    {
                        "Title": t.title,
                        "Duration (min)": t.duration_minutes,
                        "Priority": t.priority,
                        "Category": t.category,
                        "Done": t.completed,
                    }
                    for t in pet.tasks
                ]
                st.table(rows)
    else:
        st.info("No tasks yet.")

# ---------------------------------------------------------------------------
# Step 3c: Generate schedule — calls Scheduler.build_plan()
# ---------------------------------------------------------------------------

st.divider()
st.header("4. Generate Schedule")

if st.button("Generate today's schedule"):
    scheduler = Scheduler(owner=owner)
    plan = scheduler.build_plan()
    if plan:
        st.success(f"Scheduled {len(plan)} tasks for {owner.name}")
        rows = [
            {
                "Start (min)": e["start"],
                "Task": e["task"].title,
                "Pet": e["pet"].name,
                "Duration (min)": e["task"].duration_minutes,
                "Priority": e["task"].priority,
                "Reason": e["reason"],
            }
            for e in plan
        ]
        st.table(rows)
        total = sum(e["task"].duration_minutes for e in plan)
        st.caption(
            f"Total scheduled: {total} / {owner.available_minutes} minutes"
        )
    else:
        st.warning(
            "No tasks could be scheduled. "
            "Add some tasks or increase your available time."
        )
