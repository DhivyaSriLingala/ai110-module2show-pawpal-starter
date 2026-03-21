"""
tests/test_pawpal.py
--------------------
Automated test suite for PawPal+ core behaviours.

Test plan (5 groups, 28 tests):
  1. Task basics         — completion status, task addition, priority validation
  2. Sorting             — chronological order, edge cases
  3. Recurrence          — daily/weekly next-task creation, one-off returns None
  4. Conflict detection  — overlapping, back-to-back, empty, single-task
  5. Filtering           — by pet name, by status, combined, empty input
  6. Scheduler           — priority ordering, time budget, schedule reset

Run with:  python -m pytest
"""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner():
    """Owner with 120 minutes available."""
    return Owner(name="Jordan", available_minutes=120)


@pytest.fixture
def pet():
    """Young dog with no tasks."""
    return Pet(name="Mochi", species="dog", age=3)


@pytest.fixture
def senior_pet():
    """Senior cat (age 12) with no tasks."""
    return Pet(name="Luna", species="cat", age=12)


@pytest.fixture
def sample_task():
    """One-off high-priority exercise task."""
    return Task(title="Morning walk", duration_minutes=30, priority="high",
                category="exercise")


@pytest.fixture
def daily_task():
    """High-priority daily task with an explicit due date."""
    return Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        category="exercise",
        frequency="daily",
        due_date=date(2026, 3, 20),
    )


@pytest.fixture
def weekly_task():
    """Medium-priority weekly grooming task."""
    return Task(
        title="Bath time",
        duration_minutes=20,
        priority="medium",
        category="grooming",
        frequency="weekly",
        due_date=date(2026, 3, 20),
    )


@pytest.fixture
def loaded_pet(pet):
    """Pet pre-loaded with three tasks at various priorities."""
    pet.add_task(Task("Morning walk",    30, "high",   "exercise"))
    pet.add_task(Task("Enrichment play", 20, "medium", "enrichment"))
    pet.add_task(Task("Grooming brush",  15, "low",    "grooming"))
    return pet


@pytest.fixture
def scheduler(owner, loaded_pet):
    """Scheduler wired to owner + loaded_pet."""
    owner.add_pet(loaded_pet)
    return Scheduler(owner=owner, pet=loaded_pet)


# ---------------------------------------------------------------------------
# Group 1 — Task basics
# ---------------------------------------------------------------------------

class TestTaskBasics:
    """Original behaviours: completion, addition, priority guard."""

    def test_mark_complete_changes_status(self, sample_task):
        """Task starts incomplete; mark_complete() flips it to True."""
        assert sample_task.completed is False
        sample_task.mark_complete()
        assert sample_task.completed is True

    def test_mark_complete_idempotent(self, sample_task):
        """Calling mark_complete() twice must not raise or reset the flag."""
        sample_task.mark_complete()
        sample_task.mark_complete()
        assert sample_task.completed is True

    def test_add_task_increases_count(self, pet, sample_task):
        """add_task() grows the pet's task list by exactly one."""
        before = len(pet.tasks)
        pet.add_task(sample_task)
        assert len(pet.tasks) == before + 1

    def test_add_multiple_tasks(self, pet):
        """Three add_task() calls → exactly three tasks on the pet."""
        pet.add_task(Task("Walk",     30, "high", "exercise"))
        pet.add_task(Task("Feeding",  10, "high", "feeding"))
        pet.add_task(Task("Grooming", 15, "low",  "grooming"))
        assert len(pet.tasks) == 3

    def test_added_task_retrievable(self, pet, sample_task):
        """The added task's title must appear in the pet's task list."""
        pet.add_task(sample_task)
        assert "Morning walk" in [t.title for t in pet.tasks]

    def test_invalid_priority_raises(self):
        """Task raises ValueError for an unrecognised priority string."""
        with pytest.raises(ValueError, match="Invalid priority"):
            Task(title="Bad task", duration_minutes=10, priority="urgent")

    def test_priority_normalised_to_lowercase(self):
        """Priority 'HIGH' should be silently normalised to 'high'."""
        t = Task("Test", 10, "HIGH", "general")
        assert t.priority == "high"

    def test_pet_name_tagged_on_add(self, pet, sample_task):
        """add_task() must set task.pet_name to the pet's name."""
        pet.add_task(sample_task)
        assert sample_task.pet_name == "Mochi"

    def test_is_senior_dog(self):
        """Dog aged 8 or above should be flagged as senior."""
        assert Pet("Rex", "dog", 8).is_senior() is True
        assert Pet("Rex", "dog", 7).is_senior() is False

    def test_is_senior_cat(self):
        """Cat aged 11 or above should be flagged as senior."""
        assert Pet("Whiskers", "cat", 11).is_senior() is True
        assert Pet("Whiskers", "cat", 10).is_senior() is False


# ---------------------------------------------------------------------------
# Group 2 — Sorting correctness
# ---------------------------------------------------------------------------

class TestSorting:
    """sort_by_time() returns ScheduledTasks in chronological order."""

    def _make_slot(self, title: str, start: str, mins: int = 10) -> ScheduledTask:
        return ScheduledTask(Task(title, mins, "low", "general"), start)

    def test_sorts_three_out_of_order(self):
        """Three slots in reverse order must come back sorted earliest first."""
        slots = [
            self._make_slot("Evening", "17:00"),
            self._make_slot("Noon",    "12:30"),
            self._make_slot("Morning", "08:15"),
        ]
        result = Scheduler.sort_by_time(slots)
        times = [s.start_time for s in result]
        assert times == ["08:15", "12:30", "17:00"]

    def test_already_sorted_unchanged(self):
        """An already-sorted list must be returned in the same order."""
        slots = [
            self._make_slot("First",  "08:00"),
            self._make_slot("Second", "09:00"),
            self._make_slot("Third",  "10:00"),
        ]
        result = Scheduler.sort_by_time(slots)
        assert [s.start_time for s in result] == ["08:00", "09:00", "10:00"]

    def test_single_task_unchanged(self):
        """A one-item list must be returned as-is."""
        slots = [self._make_slot("Only", "11:00")]
        result = Scheduler.sort_by_time(slots)
        assert result[0].start_time == "11:00"

    def test_empty_list_returns_empty(self):
        """sort_by_time() on an empty list must return an empty list."""
        assert Scheduler.sort_by_time([]) == []

    def test_does_not_mutate_original(self):
        """sort_by_time() must return a new list without changing the input."""
        slots = [
            self._make_slot("B", "10:00"),
            self._make_slot("A", "08:00"),
        ]
        original_order = [s.start_time for s in slots]
        Scheduler.sort_by_time(slots)
        assert [s.start_time for s in slots] == original_order  # unchanged


# ---------------------------------------------------------------------------
# Group 3 — Recurrence logic
# ---------------------------------------------------------------------------

class TestRecurrence:
    """mark_complete() returns the correct next-occurrence Task."""

    def test_one_off_returns_none(self, sample_task):
        """A task with frequency='once' must return None from mark_complete()."""
        result = sample_task.mark_complete()
        assert result is None

    def test_daily_returns_next_task(self, daily_task):
        """Daily task must return a new Task with due_date = original + 1 day."""
        next_task = daily_task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == date(2026, 3, 21)

    def test_weekly_returns_next_task(self, weekly_task):
        """Weekly task must return a new Task with due_date = original + 7 days."""
        next_task = weekly_task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == date(2026, 3, 27)

    def test_recurrence_preserves_fields(self, daily_task):
        """Next occurrence must inherit title, duration, priority, category, frequency."""
        next_task = daily_task.mark_complete()
        assert next_task.title            == daily_task.title
        assert next_task.duration_minutes == daily_task.duration_minutes
        assert next_task.priority         == daily_task.priority
        assert next_task.category         == daily_task.category
        assert next_task.frequency        == daily_task.frequency

    def test_next_occurrence_starts_incomplete(self, daily_task):
        """The next occurrence must start with completed=False."""
        next_task = daily_task.mark_complete()
        assert next_task.completed is False

    def test_original_marked_complete_after_recur(self, daily_task):
        """The original task must be marked complete even when recurrence occurs."""
        daily_task.mark_complete()
        assert daily_task.completed is True

    def test_daily_no_due_date_uses_today(self):
        """Daily task with no due_date set should use today as the base."""
        t = Task("Walk", 20, "high", "exercise", frequency="daily")
        next_task = t.mark_complete()
        assert next_task.due_date == date.today() + timedelta(days=1)


# ---------------------------------------------------------------------------
# Group 4 — Conflict detection
# ---------------------------------------------------------------------------

class TestConflictDetection:
    """detect_conflicts() identifies overlapping ScheduledTask pairs."""

    def _sched(self, owner, pet) -> Scheduler:
        s = Scheduler(owner=owner, pet=pet)
        s.schedule = []
        return s

    def _slot(self, title: str, start: str, mins: int) -> ScheduledTask:
        return ScheduledTask(Task(title, mins, "high", "general"), start)

    def test_overlap_detected(self, owner, pet):
        """Two tasks whose windows overlap must produce a conflict warning."""
        s = self._sched(owner, pet)
        s.schedule = [
            self._slot("Walk",    "09:00", 30),   # 09:00-09:30
            self._slot("Vet",     "09:15", 20),   # 09:15-09:35 → overlaps Walk
        ]
        warnings = s.detect_conflicts()
        assert len(warnings) == 1
        assert "Walk" in warnings[0]
        assert "Vet" in warnings[0]

    def test_no_conflict_for_sequential_tasks(self, owner, pet):
        """Tasks placed back-to-back (one ends when the next begins) must NOT conflict."""
        s = self._sched(owner, pet)
        s.schedule = [
            self._slot("Breakfast", "08:00", 10),  # 08:00-08:10
            self._slot("Walk",      "08:10", 30),  # 08:10-08:40  — exact boundary, no overlap
        ]
        assert s.detect_conflicts() == []

    def test_no_conflict_empty_schedule(self, owner, pet):
        """An empty schedule must return zero conflicts."""
        s = self._sched(owner, pet)
        assert s.detect_conflicts() == []

    def test_no_conflict_single_task(self, owner, pet):
        """A schedule with only one task cannot have any conflicts."""
        s = self._sched(owner, pet)
        s.schedule = [self._slot("Solo", "10:00", 15)]
        assert s.detect_conflicts() == []

    def test_three_way_overlap_reports_all_pairs(self, owner, pet):
        """Three mutually overlapping tasks must report all conflicting pairs."""
        s = self._sched(owner, pet)
        s.schedule = [
            self._slot("A", "09:00", 30),   # 09:00-09:30
            self._slot("B", "09:10", 30),   # 09:10-09:40  overlaps A
            self._slot("C", "09:20", 30),   # 09:20-09:50  overlaps A and B
        ]
        warnings = s.detect_conflicts()
        # A-B, A-C, B-C → 3 pairs
        assert len(warnings) == 3

    def test_conflict_warning_is_string(self, owner, pet):
        """Each conflict warning must be a non-empty string."""
        s = self._sched(owner, pet)
        s.schedule = [
            self._slot("X", "08:00", 20),
            self._slot("Y", "08:10", 20),
        ]
        for w in s.detect_conflicts():
            assert isinstance(w, str)
            assert len(w) > 0


# ---------------------------------------------------------------------------
# Group 5 — Filtering
# ---------------------------------------------------------------------------

class TestFiltering:
    """filter_tasks() returns correct subsets by pet_name and/or completed."""

    @pytest.fixture
    def mixed_tasks(self):
        """Eight tasks across two pets with some completed."""
        mochi_tasks = [
            Task("Walk",     30, "high",   "exercise"),
            Task("Breakfast",10, "high",   "feeding"),
            Task("Grooming", 15, "low",    "grooming"),
        ]
        luna_tasks = [
            Task("Morning meds", 5,  "high",   "medication"),
            Task("Wet food",     10, "high",   "feeding"),
            Task("Playtime",     15, "medium", "enrichment"),
        ]
        # Tag pet names manually (normally done by pet.add_task)
        for t in mochi_tasks:
            t.pet_name = "Mochi"
        for t in luna_tasks:
            t.pet_name = "Luna"
        # Mark one from each pet as complete
        mochi_tasks[2].completed = True   # Grooming
        luna_tasks[1].completed  = True   # Wet food
        return mochi_tasks + luna_tasks

    def test_filter_by_pet_name(self, mixed_tasks):
        """filter_tasks(pet_name='Mochi') must return only Mochi's tasks."""
        result = Scheduler.filter_tasks(mixed_tasks, pet_name="Mochi")
        assert len(result) == 3
        assert all(t.pet_name == "Mochi" for t in result)

    def test_filter_by_pet_name_case_insensitive(self, mixed_tasks):
        """Pet name filter must be case-insensitive."""
        result = Scheduler.filter_tasks(mixed_tasks, pet_name="mochi")
        assert len(result) == 3

    def test_filter_completed(self, mixed_tasks):
        """filter_tasks(completed=True) must return only completed tasks."""
        result = Scheduler.filter_tasks(mixed_tasks, completed=True)
        assert len(result) == 2
        assert all(t.completed for t in result)

    def test_filter_incomplete(self, mixed_tasks):
        """filter_tasks(completed=False) must return only incomplete tasks."""
        result = Scheduler.filter_tasks(mixed_tasks, completed=False)
        assert len(result) == 4
        assert all(not t.completed for t in result)

    def test_filter_combined(self, mixed_tasks):
        """Combining pet_name + completed must apply both filters."""
        result = Scheduler.filter_tasks(mixed_tasks, pet_name="Luna", completed=False)
        assert len(result) == 2
        assert all(t.pet_name == "Luna" and not t.completed for t in result)

    def test_filter_empty_input(self):
        """filter_tasks on an empty list must return an empty list."""
        assert Scheduler.filter_tasks([], pet_name="Mochi") == []

    def test_filter_no_criteria_returns_all(self, mixed_tasks):
        """Calling filter_tasks() with no filters must return the full list."""
        result = Scheduler.filter_tasks(mixed_tasks)
        assert len(result) == len(mixed_tasks)


# ---------------------------------------------------------------------------
# Group 6 — Scheduler behaviour
# ---------------------------------------------------------------------------

class TestScheduler:
    """generate_schedule(), prioritize_tasks(), and edge cases."""

    def test_high_priority_scheduled_before_low(self, owner, pet):
        """High-priority tasks must appear before low-priority ones in the plan."""
        pet.add_task(Task("Grooming", 15, "low",  "grooming"))
        pet.add_task(Task("Meds",      5, "high", "medication"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner, pet=pet)
        s.generate_schedule()
        titles = [st.task.title for st in s.schedule]
        assert titles.index("Meds") < titles.index("Grooming")

    def test_task_exceeding_budget_skipped(self, pet):
        """A task longer than available_minutes must not appear in the schedule."""
        tiny_owner = Owner("Test", available_minutes=10)
        pet.add_task(Task("Long walk", 60, "high", "exercise"))
        tiny_owner.add_pet(pet)
        s = Scheduler(owner=tiny_owner, pet=pet)
        s.generate_schedule()
        assert len(s.schedule) == 0

    def test_schedule_resets_on_repeated_call(self, scheduler):
        """Calling generate_schedule() twice must not duplicate tasks."""
        scheduler.generate_schedule()
        first_count = len(scheduler.schedule)
        scheduler.generate_schedule()
        assert len(scheduler.schedule) == first_count

    def test_empty_pet_produces_empty_schedule(self, owner, pet):
        """A pet with no tasks must produce an empty schedule."""
        owner.add_pet(pet)
        s = Scheduler(owner=owner, pet=pet)
        s.generate_schedule()
        assert s.schedule == []

    def test_remaining_minutes_decremented(self, owner, pet):
        """remaining_minutes must decrease by the sum of scheduled task durations."""
        pet.add_task(Task("Walk", 30, "high", "exercise"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner, pet=pet)
        s.generate_schedule()
        assert s.remaining_minutes == owner.available_minutes - 30

    def test_scheduled_task_end_time_correct(self, owner, pet):
        """end_time must equal start_time + duration_minutes."""
        pet.add_task(Task("Walk", 25, "high", "exercise"))
        owner.add_pet(pet)
        s = Scheduler(owner=owner, pet=pet)
        s.generate_schedule(start_time="08:00")
        slot = s.schedule[0]
        assert slot.start_time == "08:00"
        assert slot.end_time   == "08:25"

    def test_get_all_tasks_aggregates_across_pets(self):
        """Owner.get_all_tasks() must return tasks from every pet combined."""
        o = Owner("Sam", 180)
        p1 = Pet("Mochi", "dog", 3)
        p2 = Pet("Luna",  "cat", 5)
        p1.add_task(Task("Walk",  30, "high", "exercise"))
        p2.add_task(Task("Meds",   5, "high", "medication"))
        p2.add_task(Task("Food",  10, "high", "feeding"))
        o.add_pet(p1)
        o.add_pet(p2)
        assert len(o.get_all_tasks()) == 3
