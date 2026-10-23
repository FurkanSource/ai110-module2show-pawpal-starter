"""Run a reproducible CLI demo with two pets and a fixed example date."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

DEMO_DATE = date(2026, 10, 23)


def make_demo_owner(day: date = DEMO_DATE) -> Owner:
    """Create fictional household data with unsorted tasks and one conflict."""
    owner = Owner("Jordan", preferred_category="walk")
    dog = Pet("Mochi", "dog")
    cat = Pet("Luna", "cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Evening walk", "18:00", day, 30, "medium", "daily", "walk"))
    dog.add_task(Task("Breakfast", "08:00", day, 10, "high", "daily", "feeding"))
    cat.add_task(Task("Grooming", "18:15", day, 20, "low", "weekly", "grooming"))
    cat.add_task(Task("Medication reminder", "09:00", day, 5, "high", "daily", "medication"))
    cat.add_task(Task("Vet appointment", "11:00", day, 30, "high", "once", "appointment"))
    return owner


def format_schedule(entries: list[tuple[Pet, Task]]) -> str:
    """Format schedule entries as an aligned, portable text table."""
    lines = [
        "DATE       TIME  PET      TASK                     MIN PRIORITY STATUS",
        "---------- ----- -------- ------------------------ --- -------- --------",
    ]
    for pet, task in entries:
        status = "done" if task.completed else "pending"
        lines.append(
            f"{task.due_date} {task.time} {pet.name:<8} {task.description:<24} "
            f"{task.duration_minutes:>3} {task.priority:<8} {status}"
        )
    if not entries:
        lines.append("(No tasks match.)")
    return "\n".join(lines)


def main() -> None:
    """Demonstrate sorting, filtering, conflicts, planning, and recurrence."""
    owner = make_demo_owner()
    scheduler = Scheduler(owner)
    print(f"Today's Schedule - {DEMO_DATE} (fixed demo date)")
    print(format_schedule(scheduler.sort_by_time()))
    print("\nPending tasks for Luna")
    print(format_schedule(scheduler.sort_by_time(scheduler.filter_tasks("Luna", False))))
    print("\nConflict warnings")
    for warning in scheduler.detect_conflicts():
        print(warning)
    print("\nPriority-first plan: 75 minutes, preferred activity = walk")
    plan, explanations = scheduler.build_plan(DEMO_DATE, 75)
    print(format_schedule(plan))
    for explanation in explanations:
        print(explanation)
    breakfast = next(task for _, task in owner.all_tasks() if task.description == "Breakfast")
    next_task = scheduler.mark_task_complete(breakfast.id, DEMO_DATE)
    assert next_task is not None
    print(f"\nCompleted Breakfast; next daily occurrence: {next_task.due_date} {next_task.time}")
    print("Repeated completion creates another task:", scheduler.mark_task_complete(breakfast.id) is not None)
    print("\nTomorrow's schedule")
    print(format_schedule(scheduler.sort_by_time(scheduler.filter_tasks(on_date=date(2026, 10, 24)))))


if __name__ == "__main__":
    main()
