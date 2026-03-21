"""
main.py
-------
Demo / testing ground for the PawPal+ logic layer.

Run:  python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    width = 58
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


# ---------------------------------------------------------------------------
# 1. Build owner + two pets
# ---------------------------------------------------------------------------

jordan = Owner(name="Jordan", available_minutes=150)
jordan.add_preference("prefer morning walks")
jordan.add_preference("no grooming before breakfast")

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=12,
            special_needs="hyperthyroid medication twice daily")

# --- Mochi tasks (added deliberately OUT OF ORDER for the sort demo) ---
mochi.add_task(Task("Enrichment play", 20, "medium", "enrichment", "afternoon"))
mochi.add_task(Task("Grooming brush",  15, "low",    "grooming"))
mochi.add_task(Task("Morning walk",    30, "high",   "exercise",   "morning",
                    frequency="daily", due_date=date.today()))
mochi.add_task(Task("Breakfast",       10, "high",   "feeding",    "morning",
                    frequency="daily", due_date=date.today()))

# --- Luna tasks ---
luna.add_task(Task("Morning medication", 5,  "high",   "medication", "morning",
                   frequency="daily", due_date=date.today()))
luna.add_task(Task("Wet food feeding",   10, "high",   "feeding",    "morning",
                   frequency="daily", due_date=date.today()))
luna.add_task(Task("Evening medication", 5,  "high",   "medication", "evening",
                   frequency="daily", due_date=date.today()))
luna.add_task(Task("Playtime",           15, "medium", "enrichment", "afternoon"))

jordan.add_pet(mochi)
jordan.add_pet(luna)


# ---------------------------------------------------------------------------
# 2. Pet profiles
# ---------------------------------------------------------------------------

section("PET PROFILES")
for pet in jordan.pets:
    print(f"  {pet.get_profile()}")


# ---------------------------------------------------------------------------
# 3. Generate and display schedules
# ---------------------------------------------------------------------------

section(f"TODAY'S SCHEDULE  --  owner: {jordan.name}")
print(f"  Available time: {jordan.get_available_minutes()} min\n")

for pet in jordan.pets:
    scoped = Owner(name=jordan.name, available_minutes=jordan.available_minutes)
    scoped.pets = [pet]
    sched = Scheduler(owner=scoped, pet=pet)
    sched.generate_schedule(start_time="08:00")

    print(f"\n  +-- {pet.name.upper()} {'[SENIOR]' if pet.is_senior() else ''}")
    for st in sched.schedule:
        for line in st.display().splitlines():
            print(f"  |  {line}")
    time_used = jordan.available_minutes - sched.remaining_minutes
    print(f"  +-- {len(sched.schedule)} task(s)  |  {time_used} min used")


# ---------------------------------------------------------------------------
# FEATURE 1 — Sorting: tasks added out of order, sorted by scheduled time
# ---------------------------------------------------------------------------

section("FEATURE 1: sort_by_time()")

# Build a small schedule with deliberate out-of-order slots
dummy_tasks = [
    Task("Evening walk",    20, "medium", "exercise", "evening"),
    Task("Lunch feeding",   10, "high",   "feeding",  "afternoon"),
    Task("Morning medicine", 5, "high",   "medication","morning"),
]
manual_slots = [
    ScheduledTask(dummy_tasks[0], "17:00"),
    ScheduledTask(dummy_tasks[1], "12:30"),
    ScheduledTask(dummy_tasks[2], "08:15"),
]

print("  Before sort:")
for s in manual_slots:
    print(f"    {s.start_time}  {s.task.title}")

sorted_slots = Scheduler.sort_by_time(manual_slots)

print("  After sort_by_time():")
for s in sorted_slots:
    print(f"    {s.start_time}  {s.task.title}")


# ---------------------------------------------------------------------------
# FEATURE 2 — Filtering: by pet name and by completion status
# ---------------------------------------------------------------------------

section("FEATURE 2: filter_tasks()")

all_tasks = jordan.get_all_tasks()

# Mark one task complete to make the filter interesting
all_tasks[0].mark_complete()   # Enrichment play (Mochi) → completed

mochi_only = Scheduler.filter_tasks(all_tasks, pet_name="Mochi")
print(f"  Tasks for Mochi only ({len(mochi_only)}):")
for t in mochi_only:
    status = "[done]" if t.completed else "[todo]"
    print(f"    {status}  {t.title}")

incomplete = Scheduler.filter_tasks(all_tasks, completed=False)
print(f"\n  Incomplete tasks across all pets ({len(incomplete)}):")
for t in incomplete:
    print(f"    {t.pet_name:<8}  {t.title}")

combined = Scheduler.filter_tasks(all_tasks, pet_name="Luna", completed=False)
print(f"\n  Luna's incomplete tasks ({len(combined)}):")
for t in combined:
    print(f"    {t.title}")


# ---------------------------------------------------------------------------
# FEATURE 3 — Recurring tasks: mark_complete() returns next occurrence
# ---------------------------------------------------------------------------

section("FEATURE 3: recurring tasks")

# Pick Mochi's "Morning walk" which was created with frequency="daily"
morning_walk = next(t for t in mochi.tasks if t.title == "Morning walk")

print(f"  Before: '{morning_walk.title}'  completed={morning_walk.completed}"
      f"  due={morning_walk.due_date}  freq={morning_walk.frequency}")

next_task = morning_walk.mark_complete()

print(f"  After:  '{morning_walk.title}'  completed={morning_walk.completed}")

if next_task:
    print(f"  Next occurrence created automatically:")
    print(f"    title={next_task.title}  due={next_task.due_date}"
          f"  freq={next_task.frequency}  completed={next_task.completed}")
    # Register the next occurrence back on the pet
    mochi.add_task(next_task)
    print(f"  Mochi now has {len(mochi.tasks)} tasks (next walk added to list)")


# ---------------------------------------------------------------------------
# FEATURE 4 — Conflict detection
# ---------------------------------------------------------------------------

section("FEATURE 4: detect_conflicts()")

# Build a scheduler and manually inject two overlapping ScheduledTasks
conflict_sched = Scheduler(
    owner=Owner("Test", 120),
    pet=mochi,
)
t1 = Task("Walk in park",   30, "high",   "exercise")
t2 = Task("Vet appointment", 20, "high",  "medication")
t3 = Task("Breakfast",      10, "high",   "feeding")

# t1: 09:00-09:30,  t2: 09:15-09:35 (overlaps t1),  t3: 09:30-09:40 (no overlap)
conflict_sched.schedule = [
    ScheduledTask(t1, "09:00"),
    ScheduledTask(t2, "09:15"),
    ScheduledTask(t3, "09:30"),
]

print("  Schedule under test:")
for s in conflict_sched.schedule:
    print(f"    {s.start_time}-{s.end_time}  {s.task.title}")

conflicts = conflict_sched.detect_conflicts()
if conflicts:
    print(f"\n  {len(conflicts)} conflict(s) detected:")
    for w in conflicts:
        print(f"  [!] {w}")
else:
    print("\n  No conflicts detected.")

# Verify a clean schedule produces no warnings
clean_sched = Scheduler(owner=Owner("Test", 120), pet=mochi)
clean_sched.schedule = [
    ScheduledTask(t3, "08:00"),
    ScheduledTask(t1, "08:10"),
]
print(f"\n  Clean schedule conflict count: {len(clean_sched.detect_conflicts())}  (expected 0)")

print()
