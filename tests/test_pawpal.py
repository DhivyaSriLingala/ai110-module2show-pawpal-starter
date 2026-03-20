"""
tests/test_pawpal.py
--------------------
Quick tests for core PawPal+ behaviours.

Run with:  python -m pytest
"""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Fixtures — reusable building blocks shared across tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    """A basic high-priority task used in multiple tests."""
    return Task(title="Morning walk", duration_minutes=30, priority="high",
                category="exercise")


@pytest.fixture
def sample_pet():
    """A pet with no tasks pre-loaded."""
    return Pet(name="Mochi", species="dog", age=3)


# ---------------------------------------------------------------------------
# Test 1 — Task completion
# Verify that calling mark_complete() actually changes the task's status.
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status(sample_task):
    """Task should start incomplete and become complete after mark_complete()."""
    # Starts as not completed
    assert sample_task.completed is False

    sample_task.mark_complete()

    # Should now be marked complete
    assert sample_task.completed is True


def test_mark_complete_is_idempotent(sample_task):
    """Calling mark_complete() twice should not raise an error."""
    sample_task.mark_complete()
    sample_task.mark_complete()
    assert sample_task.completed is True


# ---------------------------------------------------------------------------
# Test 2 — Task addition
# Verify that adding a task to a Pet increases that pet's task count.
# ---------------------------------------------------------------------------

def test_add_task_increases_count(sample_pet, sample_task):
    """Pet should have one more task after add_task() is called."""
    initial_count = len(sample_pet.tasks)

    sample_pet.add_task(sample_task)

    assert len(sample_pet.tasks) == initial_count + 1


def test_add_multiple_tasks_increases_count(sample_pet):
    """Adding three tasks should result in exactly three tasks on the pet."""
    sample_pet.add_task(Task("Walk",     30, "high",   "exercise"))
    sample_pet.add_task(Task("Feeding",  10, "high",   "feeding"))
    sample_pet.add_task(Task("Grooming", 15, "low",    "grooming"))

    assert len(sample_pet.tasks) == 3


def test_added_task_is_retrievable(sample_pet, sample_task):
    """The task added to a pet should appear in its task list."""
    sample_pet.add_task(sample_task)

    titles = [t.title for t in sample_pet.tasks]
    assert "Morning walk" in titles


# ---------------------------------------------------------------------------
# Bonus — Invalid priority raises ValueError
# ---------------------------------------------------------------------------

def test_invalid_priority_raises():
    """Task should raise ValueError when given an unrecognised priority."""
    with pytest.raises(ValueError, match="Invalid priority"):
        Task(title="Bad task", duration_minutes=10, priority="urgent")
