"""
main.py
-------
Demo / testing ground for the PawPal+ logic layer.

Run:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# 1. Build owner
# ---------------------------------------------------------------------------

jordan = Owner(name="Jordan", available_minutes=150)
jordan.add_preference("prefer morning walks")
jordan.add_preference("no grooming before breakfast")


# ---------------------------------------------------------------------------
# 2. Build two pets and attach tasks to each
# ---------------------------------------------------------------------------

# --- Pet 1: Mochi (young dog) ---
mochi = Pet(name="Mochi", species="dog", age=3)

mochi.add_task(Task("Morning walk",    30, "high",   "exercise",  "morning"))
mochi.add_task(Task("Breakfast",       10, "high",   "feeding",   "morning"))
mochi.add_task(Task("Enrichment play", 20, "medium", "enrichment","afternoon"))
mochi.add_task(Task("Grooming brush",  15, "low",    "grooming"))

# --- Pet 2: Luna (senior cat) ---
luna = Pet(
    name="Luna",
    species="cat",
    age=12,
    special_needs="hyperthyroid medication twice daily",
)

luna.add_task(Task("Morning medication", 5,  "high",   "medication", "morning"))
luna.add_task(Task("Wet food feeding",   10, "high",   "feeding",    "morning"))
luna.add_task(Task("Evening medication", 5,  "high",   "medication", "evening"))
luna.add_task(Task("Playtime",           15, "medium", "enrichment", "afternoon"))


# ---------------------------------------------------------------------------
# 3. Register both pets with the owner
# ---------------------------------------------------------------------------

jordan.add_pet(mochi)
jordan.add_pet(luna)


# ---------------------------------------------------------------------------
# 4. Helper: pretty-print a section header
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    width = 54
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


# ---------------------------------------------------------------------------
# 5. Print pet profiles
# ---------------------------------------------------------------------------

section("PET PROFILES")
for pet in jordan.pets:
    print(f"  {pet.get_profile()}")


# ---------------------------------------------------------------------------
# 6. Generate and print today's schedule for each pet
# ---------------------------------------------------------------------------

section(f"TODAY'S SCHEDULE  --  owner: {jordan.name}")
print(f"  Available time: {jordan.get_available_minutes()} min\n")

for pet in jordan.pets:
    # Build a fresh owner with only this pet so the scheduler scopes to it
    single_pet_owner = Owner(name=jordan.name,
                             available_minutes=jordan.available_minutes)
    single_pet_owner.pets = [pet]

    scheduler = Scheduler(owner=single_pet_owner, pet=pet)
    scheduler.generate_schedule(start_time="08:00")

    print(f"\n  +-- {pet.name.upper()} {'[SENIOR]' if pet.is_senior() else ''}")
    for st in scheduler.schedule:
        for line in st.display().splitlines():
            print(f"  |  {line}")
    time_used = jordan.available_minutes - scheduler.remaining_minutes
    print(f"  +-- {len(scheduler.schedule)} task(s)  |  {time_used} min used")


# ---------------------------------------------------------------------------
# 7. Print all tasks across all pets (flat view)
# ---------------------------------------------------------------------------

section("ALL TASKS  (flat view across all pets)")
all_tasks = jordan.get_all_tasks()
print(f"  {'TASK':<25} {'PRIORITY':<10} {'DURATION':>8}  CATEGORY")
print(f"  {'-'*25} {'-'*10} {'-'*8}  {'-'*12}")
for t in all_tasks:
    print(
        f"  {t.title:<25} {t.priority:<10} {t.duration_minutes:>6} min  {t.category}"
    )

print()
