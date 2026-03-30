import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("PawPal+ — Pet Care Planner")

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# 1. Owner Info
# ---------------------------------------------------------------------------
st.header("1. Owner Info")

with st.form("owner_form"):
    owner_name        = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=90, step=10
    )
    if st.form_submit_button("Save owner"):
        st.session_state.owner = Owner(
            name=owner_name, available_minutes=int(available_minutes)
        )
        st.success(f"Saved: {st.session_state.owner}")

if st.session_state.owner is None:
    st.info("Fill in your name above and click Save owner to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# 2. Pets
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Pets")

with st.form("add_pet_form"):
    c1, c2, c3, c4 = st.columns(4)
    with c1: pet_name = st.text_input("Name", value="Mochi")
    with c2: species  = st.selectbox("Species", ["dog", "cat", "other"])
    with c3: age      = st.number_input("Age", min_value=0, max_value=30, value=3)
    with c4: breed    = st.text_input("Breed", value="unknown")

    if st.form_submit_button("Add pet"):
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age), breed=breed))
        st.success(f"Added {pet_name}!")

if owner.pets:
    for pet in owner.pets:
        st.markdown(f"- **{pet.describe()}** — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# 3. Tasks
# ---------------------------------------------------------------------------
st.divider()
st.header("3. Tasks")

if not owner.pets:
    st.info("Add a pet first.")
else:
    with st.form("add_task_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: target_pet = st.selectbox("For pet",  [p.name for p in owner.pets])
        with c2: task_title = st.text_input("Title",   value="Morning walk")
        with c3: duration   = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with c4: priority   = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        c5, c6 = st.columns(2)
        with c5: category  = st.text_input("Category", value="general")
        with c6: frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

        if st.form_submit_button("Add task"):
            pet_obj = next(p for p in owner.pets if p.name == target_pet)
            pet_obj.add_task(Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                frequency=frequency,
            ))
            st.success(f"Added '{task_title}' to {target_pet}")

    # --- Task view with sort/filter controls ---
    any_tasks = any(p.tasks for p in owner.pets)
    if any_tasks:
        st.subheader("Current Tasks")
        c1, c2 = st.columns(2)
        with c1:
            sort_opt = st.selectbox(
                "Sort by",
                ["Default (by pet)", "Duration — shortest first", "Duration — longest first"],
            )
        with c2:
            filter_pet = st.selectbox(
                "Filter by pet", ["All pets"] + [p.name for p in owner.pets]
            )

        scheduler = Scheduler(owner)

        # Gather pairs to display
        if filter_pet == "All pets":
            pairs = owner.get_all_tasks()
        else:
            pairs = scheduler.filter_by_pet(filter_pet)

        if sort_opt == "Duration — shortest first":
            pairs = scheduler.sort_by_duration(pairs)
        elif sort_opt == "Duration — longest first":
            pairs = scheduler.sort_by_duration(pairs, descending=True)

        rows = [
            {
                "Pet":           pet.name,
                "Task":          task.title,
                "Duration (min)": task.duration_minutes,
                "Priority":      task.priority,
                "Category":      task.category,
                "Frequency":     task.frequency,
                "Done":          task.completed,
            }
            for pet, task in pairs
        ]
        st.table(rows)

        # Mark a task complete
        st.subheader("Mark Task Complete")
        all_pairs      = owner.get_all_tasks()
        pending_pairs  = [(p, t) for p, t in all_pairs if not t.completed]
        if pending_pairs:
            options = [f"{p.name} — {t.title}" for p, t in pending_pairs]
            chosen  = st.selectbox("Select task to mark complete", options)
            if st.button("Mark complete"):
                idx     = options.index(chosen)
                pet_obj = pending_pairs[idx][0]
                task_obj = pending_pairs[idx][1]
                pet_obj.mark_task_complete(task_obj.title)
                if task_obj.frequency in ("daily", "weekly"):
                    st.success(
                        f"'{task_obj.title}' marked done. "
                        f"Next occurrence auto-scheduled for {task_obj.frequency} recurrence."
                    )
                else:
                    st.success(f"'{task_obj.title}' marked done.")
        else:
            st.info("All tasks are already completed.")
    else:
        st.info("No tasks yet.")

# ---------------------------------------------------------------------------
# 4. Generate Schedule
# ---------------------------------------------------------------------------
st.divider()
st.header("4. Generate Schedule")

if st.button("Generate today's schedule"):
    scheduler = Scheduler(owner=owner)
    plan      = scheduler.build_plan()

    if not plan:
        st.warning("No tasks could be scheduled. Add tasks or increase your available time.")
    else:
        # Conflict detection — show warnings prominently before the plan
        conflicts = scheduler.detect_conflicts(plan)
        if conflicts:
            st.error(f"**{len(conflicts)} scheduling conflict(s) detected:**")
            for warn in conflicts:
                st.warning(warn)
        else:
            st.success(f"No conflicts — {len(plan)} tasks scheduled cleanly for {owner.name}.")

        # Plan table
        rows = [
            {
                "Start (min)":    e["start"],
                "End (min)":      e["start"] + e["task"].duration_minutes,
                "Task":           e["task"].title,
                "Pet":            e["pet"].name,
                "Duration (min)": e["task"].duration_minutes,
                "Priority":       e["task"].priority,
                "Reason":         e["reason"],
            }
            for e in plan
        ]
        st.table(rows)

        total = sum(e["task"].duration_minutes for e in plan)
        pct   = int(total / owner.available_minutes * 100)
        st.progress(pct, text=f"Time used: {total} / {owner.available_minutes} min ({pct}%)")

        # Unscheduled tasks (didn't fit)
        scheduled_titles = {e["task"].title for e in plan}
        unscheduled = [
            (pet, task)
            for pet, task in owner.get_all_tasks()
            if not task.completed and task.title not in scheduled_titles
        ]
        if unscheduled:
            st.subheader("Tasks that didn't fit today")
            st.caption("These tasks were skipped because the time budget ran out.")
            skip_rows = [
                {"Pet": p.name, "Task": t.title,
                 "Duration (min)": t.duration_minutes, "Priority": t.priority}
                for p, t in unscheduled
            ]
            st.table(skip_rows)
