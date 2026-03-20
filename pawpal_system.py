"""
pawpal_system.py
----------------
Logic layer for PawPal+.

Contains all backend classes as defined in the UML class diagram:
  Owner, Pet, Task, ScheduledTask, Scheduler

Pet and Task use Python dataclasses to keep their definitions clean and concise.
Owner, ScheduledTask, and Scheduler use regular classes because they carry
behaviour that benefits from explicit __init__ control or post-init logic.

Data-flow design:
  Tasks live on Pet  →  Owner aggregates them via get_all_tasks()
  →  Scheduler retrieves and schedules them
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Valid priority levels — used by Task validation and Scheduler sorting.
# Order matters: index 0 = lowest, index 2 = highest.
VALID_PRIORITIES: tuple[str, ...] = ("low", "medium", "high")


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the person who cares for the pet.

    Attributes
    ----------
    name : str
        Owner's display name.
    available_minutes : int
        Total free time available in the day (e.g. 180).
    preferences : list[str]
        Optional list of scheduling preferences
        (e.g. "prefer morning walks").
    pets : list[Pet]
        Pets registered to this owner.
    """

    def __init__(self, name: str, available_minutes: int,
                 preferences: Optional[list[str]] = None) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = preferences if preferences is not None else []
        self.pets: list[Pet] = []

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def get_available_minutes(self) -> int:
        """Return how many minutes are available for scheduling today."""
        return self.available_minutes

    def add_preference(self, preference: str) -> None:
        """Append a new preference string to the preferences list."""
        self.preferences.append(preference)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet as belonging to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of every Task across all of this owner's pets.

        The Scheduler calls this to build its scheduling pool, so tasks
        are always sourced from the pets rather than held separately.
        """
        return [task for pet in self.pets for task in pet.tasks]


# ---------------------------------------------------------------------------
# Pet  (dataclass)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents the animal being cared for.

    Attributes
    ----------
    name : str
        Pet's name.
    species : str
        Type of animal — 'dog', 'cat', or 'other'.
    age : int
        Age in years; used to adjust task intensity or frequency.
    special_needs : str
        Optional notes (e.g. 'takes medication twice daily').
    tasks : list[Task]
        Care tasks that belong to this pet.
    """

    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def get_profile(self) -> str:
        """Return a readable summary of the pet's information."""
        senior_tag = "  [senior]" if self.is_senior() else ""
        profile = f"{self.name} ({self.species}, age {self.age}){senior_tag}"
        if self.special_needs:
            profile += f"  |  Special needs: {self.special_needs}"
        return profile

    def is_senior(self) -> bool:
        """Return True if the pet's age qualifies as senior.

        Thresholds: dogs >= 8 years, cats >= 11 years, all others >= 10 years.
        Flags gentler / shorter scheduling for senior animals.
        """
        thresholds = {"dog": 8, "cat": 11}
        threshold = thresholds.get(self.species.lower(), 10)
        return self.age >= threshold

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task from this pet's list by title (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]


# ---------------------------------------------------------------------------
# Task  (dataclass)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single care activity that needs to happen during the day.

    Attributes
    ----------
    title : str
        Short name for the task (e.g. 'Morning walk').
    duration_minutes : int
        How long the task takes.
    priority : str
        Importance level: 'low', 'medium', or 'high'.
    category : str
        Type of task — 'exercise', 'feeding', 'grooming', 'medication', etc.
    preferred_time : str
        Optional hint for when to schedule it (e.g. 'morning', 'evening').
    """

    title: str
    duration_minutes: int
    priority: str                   # 'low' | 'medium' | 'high'
    category: str = "general"
    preferred_time: str = ""

    def __post_init__(self) -> None:
        # Normalise to lowercase and reject unknown values immediately so
        # invalid priorities cause a clear error at construction time rather
        # than a silent bug inside the scheduler.
        self.priority = self.priority.lower()
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. "
                f"Must be one of: {VALID_PRIORITIES}"
            )

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def to_dict(self) -> dict:
        """Return the task as a plain dictionary (for display and storage)."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "preferred_time": self.preferred_time,
        }


# ---------------------------------------------------------------------------
# ScheduledTask
# ---------------------------------------------------------------------------

class ScheduledTask:
    """A Task that has been placed into a specific time slot in the day's plan.

    Attributes
    ----------
    task : Task
        Reference to the original Task object.
    start_time : str
        When the task begins, e.g. '08:00'.
    end_time : str
        When the task ends — derived from start_time + task.duration_minutes.
    reason : str
        Plain-language explanation of why this task was placed here.
    """

    def __init__(self, task: Task, start_time: str, reason: str = "") -> None:
        self.task = task
        self.start_time = start_time
        self.end_time = ""
        self.reason = reason
        self._calculate_end_time()

    def _calculate_end_time(self) -> None:
        """Derive end_time from start_time + task.duration_minutes."""
        h, m = map(int, self.start_time.split(":"))
        total_minutes = h * 60 + m + self.task.duration_minutes
        self.end_time = f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def display(self) -> str:
        """Return a formatted schedule entry.

        Example:
            08:00–08:20  Morning walk  (high priority)
                Reason: Scheduled first — highest priority task of the day.
        """
        line = (
            f"{self.start_time}-{self.end_time}  "
            f"{self.task.title}  ({self.task.priority} priority)"
        )
        if self.reason:
            line += f"\n    Reason: {self.reason}"
        return line


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Core engine that takes all inputs and produces an ordered daily plan.

    Tasks are sourced from the owner's pets via owner.get_all_tasks().
    Additional tasks can be injected directly via add_task() for cases
    where a task isn't attached to a specific pet.

    Attributes
    ----------
    owner : Owner
        Provides time constraints for the day.
    pet : Pet
        The primary pet — used for context (e.g. senior status).
    tasks : list[Task]
        The full pool of tasks to schedule (sourced from owner + any extras).
    schedule : list[ScheduledTask]
        The ordered output plan produced by generate_schedule().
    remaining_minutes : int
        Live counter of minutes still available as tasks are scheduled.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        # Pull tasks from all of the owner's pets at construction time.
        # This can be refreshed by calling generate_schedule() again.
        self.tasks: list[Task] = owner.get_all_tasks()
        self.schedule: list[ScheduledTask] = []
        self.remaining_minutes: int = owner.available_minutes

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Add a Task directly to the scheduler's pool (not attached to a pet)."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task from the pool by title (case-insensitive)."""
        self.tasks = [t for t in self.tasks if t.title.lower() != title.lower()]

    # ------------------------------------------------------------------
    # Scheduling logic
    # ------------------------------------------------------------------

    def prioritize_tasks(self) -> list[Task]:
        """Return a copy of the task pool sorted by priority: high → medium → low."""
        return sorted(
            self.tasks,
            key=lambda t: VALID_PRIORITIES.index(t.priority),
            reverse=True,   # high index (2) first
        )

    def fits_in_time(self, task: Task) -> bool:
        """Return True if the task's duration fits within remaining available time."""
        return task.duration_minutes <= self.remaining_minutes

    def generate_schedule(self, start_time: str = "08:00") -> list[ScheduledTask]:
        """Run the scheduling logic and populate self.schedule.

        Algorithm:
        1. Refresh the task pool from owner's pets (picks up any changes).
        2. Merge with any tasks added directly via add_task(), de-duplicate by title.
        3. Sort by priority (high → medium → low).
        4. Walk tasks in priority order; include each one that fits in
           the remaining time budget.
        5. Assign consecutive time slots starting from start_time.
        6. Build a plain-English reason for each included task.

        Parameters
        ----------
        start_time : str
            The first slot of the day in 'HH:MM' format. Default '08:00'.

        Returns
        -------
        list[ScheduledTask]
            The ordered list of scheduled tasks (also stored in self.schedule).
        """
        # Reset output state so repeated calls produce a clean result.
        self.schedule = []
        self.remaining_minutes = self.owner.available_minutes

        # Refresh from owner's pets and merge with any directly-added tasks.
        from_pets = self.owner.get_all_tasks()
        seen_titles = {t.title.lower() for t in from_pets}
        extras = [t for t in self.tasks if t.title.lower() not in seen_titles]
        merged = from_pets + extras

        # Temporarily replace self.tasks so prioritize_tasks() works on the
        # merged pool, then restore it afterwards.
        original_tasks = self.tasks
        self.tasks = merged
        sorted_tasks = self.prioritize_tasks()
        self.tasks = original_tasks

        # Convert start_time to total minutes for easy arithmetic.
        h, m = map(int, start_time.split(":"))
        current_minutes = h * 60 + m

        is_senior_pet = self.pet.is_senior()

        for task in sorted_tasks:
            if not self.fits_in_time(task):
                continue

            slot_start = f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"

            # Build a plain-English reason.
            parts = []
            if task.is_high_priority():
                parts.append("high-priority task")
            elif task.priority == "medium":
                parts.append("medium-priority task")
            else:
                parts.append("low-priority task included because time allows")

            if task.preferred_time:
                parts.append(f"preferred time: {task.preferred_time}")

            if is_senior_pet and task.category == "exercise":
                parts.append(f"kept in plan - {self.pet.name} needs gentle activity even as a senior")

            reason = "; ".join(parts).capitalize() + "."

            scheduled = ScheduledTask(task, slot_start, reason)
            self.schedule.append(scheduled)

            current_minutes += task.duration_minutes
            self.remaining_minutes -= task.duration_minutes

        return self.schedule

    def explain_plan(self) -> str:
        """Return a human-readable summary of the full day's plan."""
        if not self.schedule:
            return "No schedule generated yet. Call generate_schedule() first."

        lines = [
            f"Daily plan for {self.pet.name} "
            f"— {len(self.schedule)} task(s) scheduled\n"
            + "=" * 50,
        ]
        for st in self.schedule:
            lines.append(st.display())

        time_used = self.owner.available_minutes - self.remaining_minutes
        lines.append(
            "-" * 50 + f"\nTime used: {time_used} / {self.owner.available_minutes} min"
            f"  |  Remaining: {self.remaining_minutes} min"
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick smoke-test  (run: python pawpal_system.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Build owner
    jordan = Owner(name="Jordan", available_minutes=120)
    jordan.add_preference("prefer morning walks")

    # Build pet and attach tasks directly to the pet
    mochi = Pet(name="Mochi", species="dog", age=3)
    mochi.add_task(Task("Morning walk",   30, "high",   "exercise",  "morning"))
    mochi.add_task(Task("Breakfast",      10, "high",   "feeding",   "morning"))
    mochi.add_task(Task("Enrichment play",20, "medium", "enrichment","afternoon"))
    mochi.add_task(Task("Grooming brush", 15, "low",    "grooming"))
    mochi.add_task(Task("Evening walk",   25, "medium", "exercise",  "evening"))

    # Register pet to owner
    jordan.add_pet(mochi)

    # Build scheduler and generate plan
    scheduler = Scheduler(owner=jordan, pet=mochi)
    scheduler.generate_schedule(start_time="08:00")

    print(scheduler.explain_plan())
    print()

    # Verify priority validation raises correctly
    try:
        bad = Task("Bad task", 10, "urgent")
    except ValueError as e:
        print(f"[OK] Priority validation caught: {e}")

    # Verify is_senior thresholds
    senior_dog = Pet("Rex", "dog", 9)
    young_cat  = Pet("Whiskers", "cat", 5)
    print(f"[OK] Rex is senior: {senior_dog.is_senior()}")        # True
    print(f"[OK] Whiskers is senior: {young_cat.is_senior()}")    # False
