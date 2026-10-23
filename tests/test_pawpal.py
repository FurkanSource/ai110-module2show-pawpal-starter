"""Behavioral tests for household scheduling and boundary conditions."""

from datetime import date, timedelta

import pytest

from main import DEMO_DATE, make_demo_owner
from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 10, 23)


@pytest.fixture
def household():
    """Provide two initially empty pets and their shared scheduler."""
    first, second = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner = Owner("Jordan", [first, second])
    return first, second, Scheduler(owner)


def test_completion_changes_status():
    task = Task("Walk", "8:00", DAY)
    assert task.time == "08:00"
    assert task.mark_complete() is True
    assert task.completed is True
    assert task.mark_complete() is False


def test_pet_addition_and_independent_collections():
    first, second = Pet("Mochi", "dog"), Pet("Luna", "cat")
    task = Task("Walk", "08:00", DAY)
    first.add_task(task)
    assert first.list_tasks() == [task]
    assert second.list_tasks() == []
    first.list_tasks().clear()
    assert len(first.tasks) == 1
    with pytest.raises(ValueError):
        first.add_task(task)


def test_sorting_across_pets_and_dates(household):
    first, second, scheduler = household
    later = Task("Tomorrow", "07:00", DAY + timedelta(days=1))
    evening = Task("Evening", "18:00", DAY)
    morning = Task("Morning", "08:00", DAY)
    first.add_task(later)
    first.add_task(evening)
    second.add_task(morning)
    assert [task for _, task in scheduler.sort_by_time()] == [morning, evening, later]
    assert first.tasks == [later, evening]
    assert scheduler.sort_by_time([]) == []


def test_combined_filters(household):
    first, second, scheduler = household
    pending = Task("Walk", "08:00", DAY)
    done = Task("Feed", "09:00", DAY, completed=True)
    first.add_task(pending)
    first.add_task(done)
    second.add_task(Task("Feed", "10:00", DAY))
    assert scheduler.filter_tasks("mochi", False, DAY) == [(first, pending)]
    assert scheduler.filter_tasks(completed=True) == [(first, done)]
    assert scheduler.filter_tasks("Missing") == []


@pytest.mark.parametrize("frequency,days", [("once", 0), ("daily", 1), ("weekly", 7)])
def test_recurrence_is_new_occurrence_and_idempotent(household, frequency, days):
    first, _, scheduler = household
    task = Task("Walk", "08:00", DAY, frequency=frequency)
    first.add_task(task)
    following = scheduler.mark_task_complete(task.id, DAY)
    assert task.completed
    if days:
        assert following.due_date == DAY + timedelta(days=days)
        assert following.id != task.id
        assert following.completed is False
        assert following.time == task.time
        assert following.frequency == frequency
    else:
        assert following is None
    count = len(first.tasks)
    assert scheduler.mark_task_complete(task.id, DAY) is None
    assert len(first.tasks) == count


@pytest.mark.parametrize("due,completed,expected", [
    (date(2026, 10, 20), DAY, date(2026, 10, 24)),
    (date(2026, 10, 31), date(2026, 10, 31), date(2026, 11, 1)),
    (date(2026, 12, 31), date(2026, 12, 31), date(2027, 1, 1)),
    (date(2028, 2, 28), date(2028, 2, 28), date(2028, 2, 29)),
    (date(2026, 10, 25), DAY, date(2026, 10, 26)),
])
def test_recurrence_calendar_boundaries(household, due, completed, expected):
    first, _, scheduler = household
    task = Task("Daily", "08:00", due, frequency="daily")
    first.add_task(task)
    assert scheduler.mark_task_complete(task.id, completed).due_date == expected


def test_overlaps_across_pets_and_touching_endpoints(household):
    first, second, scheduler = household
    first.add_task(Task("Walk", "08:00", DAY, 30))
    second.add_task(Task("Food", "08:00", DAY, 10))
    second.add_task(Task("Brush", "08:20", DAY, 10))
    second.add_task(Task("Adjacent", "08:30", DAY, 10))
    second.add_task(Task("Already done", "08:00", DAY, completed=True))
    second.add_task(Task("Next day", "08:00", DAY + timedelta(days=1)))
    warnings = scheduler.detect_conflicts(DAY)
    assert len(warnings) == 2
    assert all("Mochi" in warning and "Luna" in warning for warning in warnings)
    assert all("Adjacent" not in warning for warning in warnings)


def test_same_pet_conflict(household):
    first, _, scheduler = household
    first.add_task(Task("Walk", "08:00", DAY))
    first.add_task(Task("Feed", "08:00", DAY))
    assert len(scheduler.detect_conflicts()) == 1


def test_overnight_conflict_and_carryover_plan(household):
    first, second, scheduler = household
    first.add_task(Task("Overnight", "23:50", DAY, 30))
    next_day = DAY + timedelta(days=1)
    second.add_task(Task("Early", "00:10", next_day, 10))
    assert len(scheduler.detect_conflicts(next_day)) == 1
    assert scheduler.detect_conflicts(DAY) == []
    plan, reasons = scheduler.build_plan(next_day, 60)
    assert plan == []
    assert "overnight" in reasons[0]


def test_priority_precedes_preference_and_earlier_time(household):
    first, second, scheduler = household
    scheduler.owner.preferred_category = "walk"
    low = Task("Quick walk", "07:00", DAY, 5, "low", category="walk")
    high = Task("Important", "08:00", DAY, 20, "high")
    first.add_task(low)
    second.add_task(high)
    plan, reasons = scheduler.build_plan(DAY, 20)
    assert plan == [(second, high)]
    assert any("budget" in reason for reason in reasons)


def test_preference_breaks_equal_priority_ties(household):
    first, second, scheduler = household
    scheduler.owner.preferred_category = "walk"
    first.add_task(Task("Earlier", "08:00", DAY, 10, "medium"))
    preferred = Task("Walk", "09:00", DAY, 10, "medium", category="walk")
    second.add_task(preferred)
    plan, _ = scheduler.build_plan(DAY, 10)
    assert plan == [(second, preferred)]


def test_demo_plan_budget_conflicts_and_completion():
    owner = make_demo_owner()
    scheduler = Scheduler(owner)
    plan, reasons = scheduler.build_plan(DEMO_DATE, 75)
    assert sum(task.duration_minutes for _, task in plan) == 75
    assert len(plan) == 4
    assert any("Skipped Luna / Grooming" in reason for reason in reasons)
    assert all(not task.completed for _, task in owner.all_tasks())
    assert scheduler.build_plan(DEMO_DATE, 0)[0] == []


def test_empty_household():
    scheduler = Scheduler(Owner("Jordan"))
    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.build_plan(DAY, 60) == ([], [])
    with pytest.raises(ValueError, match="not found"):
        scheduler.mark_task_complete("missing")


def test_invalid_edit_leaves_original_unchanged(household):
    first, _, scheduler = household
    task = Task("Walk", "08:00", DAY)
    first.add_task(task)
    with pytest.raises(ValueError):
        scheduler.update_task(task.id, duration_minutes=0)
    assert first.tasks[0] is task
    updated = scheduler.update_task(task.id, description="Long walk", time="09:00", duration_minutes=30)
    assert updated.id == task.id
    assert first.tasks[0].time == "09:00"
    assert first.tasks[0].duration_minutes == 30
    scheduler.mark_task_complete(task.id)
    with pytest.raises(ValueError, match="history"):
        scheduler.update_task(task.id, description="Changed")


@pytest.mark.parametrize("changes", [
    {"description": "  "}, {"time": "24:00"}, {"time": "bad"},
    {"duration_minutes": 0}, {"duration_minutes": 241},
    {"duration_minutes": True}, {"duration_minutes": 2.5},
    {"priority": "urgent"}, {"frequency": "hourly"},
    {"due_date": "2026-10-23"}, {"category": "invalid"},
])
def test_invalid_task_inputs(changes):
    data = {"description": "Walk", "time": "08:00", "due_date": DAY}
    data.update(changes)
    with pytest.raises(ValueError):
        Task(**data)


@pytest.mark.parametrize("budget", [-1, 1441, True, 1.5])
def test_invalid_budgets(budget):
    with pytest.raises(ValueError):
        Scheduler(Owner("Jordan")).build_plan(DAY, budget)


def test_duplicate_pet_names_and_blank_names():
    owner = Owner("Jordan")
    owner.add_pet(Pet("Mochi", "dog"))
    with pytest.raises(ValueError):
        owner.add_pet(Pet(" mochi ", "cat"))
    with pytest.raises(ValueError):
        Owner(" ")
    with pytest.raises(ValueError):
        Pet(" ", "dog")


def test_recurrence_overflow_does_not_partially_complete(household):
    first, _, scheduler = household
    task = Task("Daily", "08:00", date.max, frequency="daily")
    first.add_task(task)
    with pytest.raises(ValueError, match="date range"):
        scheduler.mark_task_complete(task.id, date.max)
    assert not task.completed
    assert len(first.tasks) == 1
