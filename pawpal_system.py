"""
pawpal_system.py
----------------
Logic layer for PawPal+.

Contains all backend classes as defined in the UML class diagram:
  Owner, Pet, Task, ScheduledTask, Scheduler

Pet and Task use Python dataclasses to keep their definitions clean and concise.
Owner, ScheduledTask, and Scheduler use regular classes because they carry
behaviour that benefits from explicit __init__ control or post-init logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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
    """

    def __init__(self, name: str, available_minutes: int,
                 preferences: Optional[list[str]] = None) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = preferences if preferences is not None else []

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def get_available_minutes(self) -> int:
        """Return how many minutes are available for scheduling today."""
        pass  # TODO: implement

    def add_preference(self, preference: str) -> None:
        """Append a new preference string to the preferences list."""
        pass  # TODO: implement


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
    """

    name: str
    species: str
    age: int
    special_needs: str = ""

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def get_profile(self) -> str:
        """Return a readable summary of the pet's information."""
        pass  # TODO: implement

    def is_senior(self) -> bool:
        """Return True if the pet's age qualifies as senior.

        Threshold: dogs >= 8 years, cats >= 11 years, others >= 10 years.
        Flags gentler / shorter scheduling for senior animals.
        """
        pass  # TODO: implement


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

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        pass  # TODO: implement

    def to_dict(self) -> dict:
        """Return the task as a plain dictionary (for display and storage)."""
        pass  # TODO: implement


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
        self.end_time = ""      # calculated in __post_init logic below
        self.reason = reason
        self._calculate_end_time()

    def _calculate_end_time(self) -> None:
        """Derive end_time from start_time + task.duration_minutes."""
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def display(self) -> str:
        """Return a formatted schedule entry.

        Example: '08:00–08:20  Morning walk  (high priority)'
        """
        pass  # TODO: implement


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Core engine that takes all inputs and produces an ordered daily plan.

    Attributes
    ----------
    owner : Owner
        Provides time constraints for the day.
    pet : Pet
        Provides context that influences task suitability (e.g. senior status).
    tasks : list[Task]
        The pool of care tasks to be scheduled.
    schedule : list[ScheduledTask]
        The ordered output plan produced by generate_schedule().
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []
        self.schedule: list[ScheduledTask] = []

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Add a new Task to the task pool."""
        pass  # TODO: implement

    def remove_task(self, title: str) -> None:
        """Remove a task from the pool by its title (case-insensitive)."""
        pass  # TODO: implement

    # ------------------------------------------------------------------
    # Scheduling logic
    # ------------------------------------------------------------------

    def prioritize_tasks(self) -> list[Task]:
        """Return tasks sorted by priority: high → medium → low."""
        pass  # TODO: implement

    def fits_in_time(self, task: Task) -> bool:
        """Return True if the task's duration fits within remaining available time."""
        pass  # TODO: implement

    def generate_schedule(self) -> list[ScheduledTask]:
        """Run the scheduling logic and populate self.schedule.

        Steps (to implement):
        1. Sort tasks by priority via prioritize_tasks().
        2. Walk through sorted tasks; include each that fits_in_time().
        3. Assign a start_time and build a ScheduledTask for each included task.
        4. Deduct duration from remaining available time.
        5. Store the result in self.schedule and return it.
        """
        pass  # TODO: implement

    def explain_plan(self) -> str:
        """Return a human-readable summary of the full day's plan."""
        pass  # TODO: implement
