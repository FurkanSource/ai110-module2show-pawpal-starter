"""Compare scheduling behavior against independently generated time intervals."""

from datetime import date, timedelta
from random import Random

from pawpal_system import Owner, Pet, Scheduler, Task


def test_randomized_household_conflicts_and_plan_invariants():
    """Check 200 reproducible households using an integer-minute overlap oracle."""
    random = Random(20261023)
    base = date(2026, 10, 23)
    for case in range(200):
        pets = [Pet("Mochi", "dog"), Pet("Luna", "cat")]
        scheduler = Scheduler(Owner("Jordan", pets, preferred_category="walk"))
        records = []
        for number in range(12):
            pet = pets[random.randrange(2)]
            start = random.randrange(3 * 1440)
            day, minute = divmod(start, 1440)
            duration = random.randrange(1, 241)
            task = Task(
                f"Care {case}-{number}", f"{minute // 60:02}:{minute % 60:02}",
                base + timedelta(days=day), duration,
                random.choice(["high", "medium", "low"]),
                category=random.choice(["feeding", "walk"]),
                completed=random.random() < 0.2,
            )
            pet.add_task(task)
            records.append((pet, task, start, start + duration))

        pending = sorted([record for record in records if not record[1].completed], key=lambda r: r[2])
        for day in range(4):
            expected = set()
            for index, (pet, task, start, end) in enumerate(pending):
                for other_pet, other, other_start, other_end in pending[index + 1:]:
                    left = max(start, other_start, day * 1440)
                    right = min(end, other_end, (day + 1) * 1440)
                    if left < right:
                        expected.add(
                            f"Conflict: {pet.name} / {task.description} "
                            f"({task.due_date} {task.time}) overlaps "
                            f"{other_pet.name} / {other.description} "
                            f"({other.due_date} {other.time})."
                        )
            actual = scheduler.detect_conflicts(base + timedelta(days=day))
            assert len(actual) == len(expected)
            assert set(actual) == expected

        budget = random.randrange(0, 241)
        plan_day = base + timedelta(days=1)
        before = [(task.id, task.completed) for _, task in scheduler.owner.all_tasks()]
        plan, reasons = scheduler.build_plan(plan_day, budget)
        assert sum(task.duration_minutes for _, task in plan) <= budget
        assert all(task.due_date == plan_day and not task.completed for _, task in plan)
        selected_ids = {task.id for _, task in plan}
        chosen = sorted([record for record in records if record[1].id in selected_ids], key=lambda r: r[2])
        assert [task.id for _, task in plan] == [record[1].id for record in chosen]
        assert all(first[3] <= second[2] for first, second in zip(chosen, chosen[1:]))
        for _, _, start, end in chosen:
            for _, _, prior_start, prior_end in pending:
                if prior_start < 1440:
                    assert end <= prior_start or prior_end <= start
        assert len(reasons) == len(scheduler.filter_tasks(completed=False, on_date=plan_day))
        assert before == [(task.id, task.completed) for _, task in scheduler.owner.all_tasks()]
