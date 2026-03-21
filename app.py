"""
app.py
------
Streamlit UI for PawPal+.

All backend logic lives in pawpal_system.py.
This file is purely the "bridge" between the user interface and the logic layer.

Session-state design:
  st.session_state.owner  -> Owner object (holds all pets; pets hold all tasks)
  One key holds the entire object graph, so data persists across reruns.
"""

import streamlit as st

# Step 1 — Import the classes we need from the logic layer.
from pawpal_system import Owner, Pet, Task, Scheduler, VALID_PRIORITIES

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner.")

# ---------------------------------------------------------------------------
# Step 2 — Initialise session state.
#
# Streamlit re-runs the entire script on every interaction.
# We check whether 'owner' already exists in the "vault" before creating one
# so we never overwrite an owner (and their pets/tasks) that the user built up.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None   # will be set when the user fills the form

# Convenience shorthand used throughout this file
owner: Owner | None = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------

st.header("1. Owner profile")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input(
            "Your name",
            value=owner.name if owner else "Jordan",
        )
    with col2:
        available_minutes = st.number_input(
            "Free time today (minutes)",
            min_value=10, max_value=480,
            value=owner.available_minutes if owner else 120,
            step=10,
        )
    submitted_owner = st.form_submit_button("Save owner profile")

if submitted_owner:
    if owner is None:
        # First time — create a brand-new Owner and store it in the vault.
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
        )
    else:
        # Update the existing owner without wiping out their pets.
        owner.name = owner_name
        owner.available_minutes = int(available_minutes)
    st.success(f"Owner profile saved: {owner_name} ({available_minutes} min available)")
    st.rerun()

# Re-read after possible update
owner = st.session_state.owner

if owner:
    st.info(f"Current owner: **{owner.name}** | Available today: **{owner.available_minutes} min**")
else:
    st.warning("Please save an owner profile before adding pets or tasks.")
    st.stop()   # nothing below can work without an owner

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------

st.header("2. Your pets")

with st.form("add_pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    special_needs = st.text_input(
        "Special needs (optional)",
        placeholder="e.g. takes medication twice daily",
    )
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    if pet_name.strip() == "":
        st.error("Pet name cannot be empty.")
    else:
        # Check for duplicate name
        existing_names = [p.name.lower() for p in owner.pets]
        if pet_name.strip().lower() in existing_names:
            st.error(f"A pet named '{pet_name}' already exists.")
        else:
            # Step 3 — Wire UI action to class method: owner.add_pet()
            new_pet = Pet(
                name=pet_name.strip(),
                species=species,
                age=int(age),
                special_needs=special_needs.strip(),
            )
            owner.add_pet(new_pet)
            st.success(f"Added {new_pet.get_profile()}")
            st.rerun()

# Show all current pets
if owner.pets:
    for pet in owner.pets:
        senior_badge = " 🔵 Senior" if pet.is_senior() else ""
        with st.expander(f"**{pet.name}** — {pet.species}, age {pet.age}{senior_badge}"):
            if pet.special_needs:
                st.caption(f"Special needs: {pet.special_needs}")
            if pet.tasks:
                for t in pet.tasks:
                    status = "✅" if t.completed else "⬜"
                    st.markdown(
                        f"{status} **{t.title}** &nbsp; `{t.priority}` &nbsp; "
                        f"{t.duration_minutes} min &nbsp; _{t.category}_"
                    )
            else:
                st.caption("No tasks yet — add some below.")
else:
    st.info("No pets added yet. Use the form above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a task to a pet
# ---------------------------------------------------------------------------

st.header("3. Add a care task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]

    with st.form("add_task_form"):
        selected_pet_name = st.selectbox("Add task to pet", pet_names)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col3:
            priority = st.selectbox(
                "Priority", list(VALID_PRIORITIES), index=2   # default: "high"
            )

        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox(
                "Category",
                ["exercise", "feeding", "medication", "grooming", "enrichment", "general"],
            )
        with col5:
            preferred_time = st.selectbox(
                "Preferred time (optional)",
                ["", "morning", "afternoon", "evening"],
            )

        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        if task_title.strip() == "":
            st.error("Task title cannot be empty.")
        else:
            # Find the selected pet object from the owner's list
            target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
            try:
                # Step 3 — Wire UI action to class method: pet.add_task()
                new_task = Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category,
                    preferred_time=preferred_time,
                )
                target_pet.add_task(new_task)
                st.success(
                    f"Added **{new_task.title}** ({new_task.priority} priority, "
                    f"{new_task.duration_minutes} min) to {target_pet.name}."
                )
                st.rerun()
            except ValueError as e:
                st.error(str(e))

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate today's schedule
# ---------------------------------------------------------------------------

st.header("4. Today's schedule")

if not owner.pets:
    st.info("Add a pet and some tasks first.")
elif not owner.get_all_tasks():
    st.info("Add at least one task before generating a schedule.")
else:
    pet_names = [p.name for p in owner.pets]
    schedule_for = st.selectbox("Generate schedule for", pet_names, key="sched_pet")
    start_time = st.time_input("Start time", value=None)
    start_str = start_time.strftime("%H:%M") if start_time else "08:00"

    if st.button("Generate schedule", type="primary"):
        target_pet = next(p for p in owner.pets if p.name == schedule_for)

        # Build a scoped owner so the scheduler only sees this pet's tasks
        scoped_owner = Owner(
            name=owner.name,
            available_minutes=owner.available_minutes,
        )
        scoped_owner.pets = [target_pet]

        # Step 3 — Wire UI action to Scheduler
        scheduler = Scheduler(owner=scoped_owner, pet=target_pet)
        schedule = scheduler.generate_schedule(start_time=start_str)

        if not schedule:
            st.warning(
                "No tasks fit within the available time budget. "
                "Try adding shorter tasks or increasing available minutes."
            )
        else:
            st.success(
                f"Scheduled {len(schedule)} task(s) for **{target_pet.name}** "
                f"starting at {start_str}"
            )

            # Display each scheduled task as a clean card
            for st_item in schedule:
                with st.container(border=True):
                    left, right = st.columns([3, 1])
                    with left:
                        st.markdown(
                            f"**{st_item.start_time} – {st_item.end_time}** &nbsp; "
                            f"{st_item.task.title}"
                        )
                        st.caption(st_item.reason)
                    with right:
                        badge_color = (
                            "🔴" if st_item.task.priority == "high"
                            else "🟡" if st_item.task.priority == "medium"
                            else "🟢"
                        )
                        st.markdown(
                            f"{badge_color} {st_item.task.priority}<br>"
                            f"_{st_item.task.duration_minutes} min_",
                            unsafe_allow_html=True,
                        )

            # Summary footer
            time_used = owner.available_minutes - scheduler.remaining_minutes
            st.markdown(
                f"**Time used:** {time_used} / {owner.available_minutes} min &nbsp;|&nbsp; "
                f"**Remaining:** {scheduler.remaining_minutes} min"
            )
