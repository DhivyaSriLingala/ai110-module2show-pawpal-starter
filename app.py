"""
app.py
------
Streamlit UI for PawPal+.

All backend logic lives in pawpal_system.py.
This file is purely the bridge between the user interface and the logic layer.

Session-state design:
  st.session_state.owner  -> Owner object (holds all pets; pets hold all tasks)
  One key holds the entire object graph so data persists across reruns.
"""

import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask, VALID_PRIORITIES

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner.")

# ---------------------------------------------------------------------------
# Session state — initialise once, persist across reruns
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

owner: Owner | None = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 1 — Owner profile
# ---------------------------------------------------------------------------

st.header("1. Owner profile")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Your name",
                                   value=owner.name if owner else "Jordan")
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
        st.session_state.owner = Owner(owner_name, int(available_minutes))
    else:
        owner.name = owner_name
        owner.available_minutes = int(available_minutes)
    st.success(f"Profile saved: **{owner_name}** — {available_minutes} min available today.")
    st.rerun()

owner = st.session_state.owner

if owner:
    st.info(
        f"Owner: **{owner.name}** &nbsp;|&nbsp; "
        f"Daily budget: **{owner.available_minutes} min**"
    )
else:
    st.warning("Please save an owner profile before adding pets or tasks.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Pets panel
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
    if not pet_name.strip():
        st.error("Pet name cannot be empty.")
    elif pet_name.strip().lower() in [p.name.lower() for p in owner.pets]:
        st.error(f"A pet named '{pet_name}' already exists.")
    else:
        new_pet = Pet(pet_name.strip(), species, int(age), special_needs.strip())
        owner.add_pet(new_pet)
        st.success(f"Added: {new_pet.get_profile()}")
        st.rerun()

# --- Pet cards with task list, filtering, and mark-complete ---
if not owner.pets:
    st.info("No pets added yet. Use the form above.")
else:
    # Global filter toggle shown above all pet cards
    show_filter = st.radio(
        "Show tasks",
        ["All", "Incomplete only", "Completed only"],
        horizontal=True,
        label_visibility="collapsed",
    )
    completed_filter = None
    if show_filter == "Incomplete only":
        completed_filter = False
    elif show_filter == "Completed only":
        completed_filter = True

    for pet in owner.pets:
        senior_badge = " 🔵 Senior" if pet.is_senior() else ""
        task_count   = len(pet.tasks)
        done_count   = sum(1 for t in pet.tasks if t.completed)

        with st.expander(
            f"**{pet.name}** — {pet.species}, age {pet.age}{senior_badge} "
            f"&nbsp; ({done_count}/{task_count} done)",
            expanded=True,
        ):
            if pet.special_needs:
                st.caption(f"Special needs: {pet.special_needs}")

            # Apply filter using Scheduler.filter_tasks()
            visible = Scheduler.filter_tasks(pet.tasks, completed=completed_filter)

            if not visible:
                st.caption("No tasks match the current filter." if pet.tasks
                           else "No tasks yet — add some below.")
            else:
                for t in visible:
                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        priority_icon = (
                            "🔴" if t.priority == "high"
                            else "🟡" if t.priority == "medium"
                            else "🟢"
                        )
                        recur_tag = (
                            f" _(repeats {t.frequency})_"
                            if t.frequency != "once" else ""
                        )
                        status_icon = "✅" if t.completed else "⬜"
                        st.markdown(
                            f"{status_icon} {priority_icon} **{t.title}** &nbsp; "
                            f"`{t.duration_minutes} min` &nbsp; _{t.category}_{recur_tag}"
                        )
                    with col_btn:
                        if not t.completed:
                            btn_key = f"done_{pet.name}_{t.title}"
                            if st.button("Done", key=btn_key):
                                next_task = t.mark_complete()
                                if next_task:
                                    # Recurring — add next occurrence to the pet
                                    pet.add_task(next_task)
                                    st.success(
                                        f"**{t.title}** marked complete. "
                                        f"Next occurrence added: {next_task.due_date}"
                                    )
                                else:
                                    st.success(f"**{t.title}** marked complete.")
                                st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a care task
# ---------------------------------------------------------------------------

st.header("3. Add a care task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form"):
        selected_pet_name = st.selectbox(
            "Add task to pet", [p.name for p in owner.pets]
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col3:
            priority = st.selectbox(
                "Priority", list(VALID_PRIORITIES), index=2
            )

        col4, col5, col6 = st.columns(3)
        with col4:
            category = st.selectbox(
                "Category",
                ["exercise", "feeding", "medication",
                 "grooming", "enrichment", "general"],
            )
        with col5:
            preferred_time = st.selectbox(
                "Preferred time",
                ["", "morning", "afternoon", "evening"],
            )
        with col6:
            frequency = st.selectbox(
                "Repeats",
                ["once", "daily", "weekly"],
            )

        due_date_input = None
        if frequency != "once":
            due_date_input = st.date_input(
                "First due date", value=date.today()
            )

        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        if not task_title.strip():
            st.error("Task title cannot be empty.")
        else:
            target_pet = next(
                p for p in owner.pets if p.name == selected_pet_name
            )
            try:
                new_task = Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    category=category,
                    preferred_time=preferred_time,
                    frequency=frequency,
                    due_date=due_date_input,
                )
                target_pet.add_task(new_task)
                recur_note = (
                    f", repeats {frequency} from {due_date_input}"
                    if frequency != "once" else ""
                )
                st.success(
                    f"Added **{new_task.title}** ({new_task.priority} priority, "
                    f"{new_task.duration_minutes} min) to {target_pet.name}{recur_note}."
                )
                st.rerun()
            except ValueError as e:
                st.error(str(e))

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Task filter view (cross-pet)
# ---------------------------------------------------------------------------

st.header("4. Task overview")

all_tasks = owner.get_all_tasks()

if not all_tasks:
    st.info("No tasks added yet.")
else:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_pet = st.selectbox(
            "Filter by pet",
            ["All pets"] + [p.name for p in owner.pets],
            key="filter_pet",
        )
    with col_f2:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Incomplete", "Completed"],
            key="filter_status",
        )

    pet_filter_arg     = None if filter_pet == "All pets" else filter_pet
    status_filter_arg  = (
        None  if filter_status == "All"
        else False if filter_status == "Incomplete"
        else True
    )

    # Use Scheduler.filter_tasks() — the algorithmic layer method
    filtered = Scheduler.filter_tasks(
        all_tasks,
        pet_name=pet_filter_arg,
        completed=status_filter_arg,
    )

    if not filtered:
        st.warning("No tasks match the selected filters.")
    else:
        # Build a display-friendly list of dicts for st.table
        rows = [
            {
                "Status":   "Done" if t.completed else "Todo",
                "Pet":      t.pet_name,
                "Task":     t.title,
                "Priority": t.priority,
                "Duration": f"{t.duration_minutes} min",
                "Category": t.category,
                "Repeats":  t.frequency,
            }
            for t in filtered
        ]
        st.table(rows)
        st.caption(f"{len(filtered)} task(s) shown.")

st.divider()

# ---------------------------------------------------------------------------
# Section 5 — Generate today's schedule
# ---------------------------------------------------------------------------

st.header("5. Today's schedule")

if not owner.pets:
    st.info("Add a pet and some tasks first.")
elif not all_tasks:
    st.info("Add at least one task before generating a schedule.")
else:
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        schedule_for = st.selectbox(
            "Generate schedule for",
            [p.name for p in owner.pets],
            key="sched_pet",
        )
    with col_s2:
        start_time_input = st.time_input("Start time", value=None)
        start_str = start_time_input.strftime("%H:%M") if start_time_input else "08:00"

    if st.button("Generate schedule", type="primary"):
        target_pet = next(p for p in owner.pets if p.name == schedule_for)

        # Scope the scheduler to this pet only
        scoped_owner = Owner(owner.name, owner.available_minutes)
        scoped_owner.pets = [target_pet]

        scheduler = Scheduler(owner=scoped_owner, pet=target_pet)
        raw_schedule = scheduler.generate_schedule(start_time=start_str)

        if not raw_schedule:
            st.warning(
                "No tasks fit within the available time budget. "
                "Try adding shorter tasks or increasing available minutes."
            )
        else:
            # --- Sort schedule by time using Scheduler.sort_by_time() ---
            schedule = Scheduler.sort_by_time(raw_schedule)

            st.success(
                f"Scheduled **{len(schedule)}** task(s) for **{target_pet.name}** "
                f"starting at {start_str}"
            )

            # --- Conflict detection — shown prominently before the task list ---
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.error(
                    f"**{len(conflicts)} scheduling conflict(s) detected!** "
                    "Two or more tasks overlap in time. "
                    "Review the warnings below and adjust start times or durations."
                )
                for w in conflicts:
                    # Extract task names for a friendlier message
                    st.warning(f"⚠️ {w}")
            else:
                st.success("No scheduling conflicts — your plan looks clean!")

            st.markdown("---")

            # --- Display each scheduled task as a card ---
            for item in schedule:
                priority_color = (
                    "🔴" if item.task.priority == "high"
                    else "🟡" if item.task.priority == "medium"
                    else "🟢"
                )
                recur_badge = (
                    f" &nbsp; 🔁 _{item.task.frequency}_"
                    if item.task.frequency != "once" else ""
                )

                with st.container(border=True):
                    left, right = st.columns([4, 1])
                    with left:
                        st.markdown(
                            f"**{item.start_time} – {item.end_time}** &nbsp;&nbsp; "
                            f"{item.task.title}{recur_badge}"
                        )
                        st.caption(item.reason)
                    with right:
                        st.markdown(
                            f"{priority_color} {item.task.priority}<br>"
                            f"_{item.task.duration_minutes} min_",
                            unsafe_allow_html=True,
                        )

            # --- Summary bar ---
            time_used = owner.available_minutes - scheduler.remaining_minutes
            skipped = [
                t for t in target_pet.tasks
                if not any(s.task.title == t.title for s in schedule)
            ]

            st.markdown("---")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Tasks scheduled", len(schedule))
            col_b.metric("Time used", f"{time_used} min")
            col_c.metric("Time remaining", f"{scheduler.remaining_minutes} min")

            # --- Tasks that didn't fit in the budget ---
            if skipped:
                with st.expander(
                    f"**{len(skipped)} task(s) not scheduled** "
                    "(did not fit within your time budget)"
                ):
                    for t in skipped:
                        st.markdown(
                            f"- **{t.title}** ({t.duration_minutes} min, "
                            f"{t.priority} priority) — needs "
                            f"{t.duration_minutes - scheduler.remaining_minutes} "
                            f"more minutes than available"
                        )
                    st.caption(
                        "Tip: increase your available minutes or remove lower-priority tasks."
                    )
