"""Pet-care domain objects and scheduling rules, independent of Streamlit."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from uuid import uuid4

PRIORITIES = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = {"once": 0, "daily": 1, "weekly": 7}
CATEGORIES = ("feeding", "walk", "medication", "appointment", "grooming", "other")


def nonblank(value: str, label: str) -> str:
    """Normalize required text or raise a useful validation error."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    return value.strip()


@dataclass
class Task:
    """One dated occurrence of a care activity, with a stable identity."""

    description: str
    time: str
    due_date: date = field(default_factory=date.today)
    duration_minutes: int = 15
    priority: str = "medium"
    frequency: str = "once"
    category: str = "other"
    completed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate inputs and normalize time for reliable string sorting."""
        self.description = nonblank(self.description, "Task description")
        if not isinstance(self.time, str):
            raise ValueError("Time must use HH:MM, for example 08:30.")
        try:
            self.time = datetime.strptime(self.time.strip(), "%H:%M").strftime("%H:%M")
        except ValueError as exc:
            raise ValueError("Time must use HH:MM, for example 08:30.") from exc
        if type(self.due_date) is not date:
            raise ValueError("Due date must be a calendar date.")
        if type(self.duration_minutes) is not int or not 1 <= self.duration_minutes <= 240:
            raise ValueError("Duration must be a whole number from 1 to 240 minutes.")
        if self.priority not in PRIORITIES:
            raise ValueError("Priority must be high, medium, or low.")
        if self.frequency not in FREQUENCIES:
            raise ValueError("Frequency must be once, daily, or weekly.")
        if self.category not in CATEGORIES:
            raise ValueError("Choose a supported activity type.")
        if type(self.completed) is not bool:
            raise ValueError("Completion status must be true or false.")
        self.id = nonblank(self.id, "Task ID")

    @property
    def starts_at(self) -> datetime:
        """Return the start as a local, timezone-naive datetime."""
        return datetime.combine(self.due_date, datetime.strptime(self.time, "%H:%M").time())

    @property
    def ends_at(self) -> datetime:
        """Return the end, allowing activities to cross midnight."""
        return self.starts_at + timedelta(minutes=self.duration_minutes)

    def mark_complete(self) -> bool:
        """Mark this occurrence complete and report whether its state changed."""
        changed = not self.completed
        self.completed = True
        return changed


@dataclass
class Pet:
    """A pet with identifying information and an independent task list."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate identifying information."""
        self.name = nonblank(self.name, "Pet name")
        self.species = nonblank(self.species, "Species")

    def add_task(self, task: Task) -> None:
        """Add a task unless its identity is already present."""
        if any(existing.id == task.id for existing in self.tasks):
            raise ValueError("This task has already been added to this pet.")
        self.tasks.append(task)

    def list_tasks(self) -> list[Task]:
        """Return a copy of the task collection."""
        return list(self.tasks)


@dataclass
class Owner:
    """The household's pets and the owner's preferred activity type."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferred_category: str = "none"

    def __post_init__(self) -> None:
        """Validate the owner's name and optional activity preference."""
        self.name = nonblank(self.name, "Owner name")
        if self.preferred_category not in ("none", *CATEGORIES):
            raise ValueError("Choose a supported activity preference.")

    def add_pet(self, pet: Pet) -> None:
        """Add a uniquely named pet to avoid ambiguous household labels."""
        if any(p.id == pet.id or p.name.casefold() == pet.name.casefold() for p in self.pets):
            raise ValueError("A pet with this name or identity already exists.")
        self.pets.append(pet)

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return pet-task pairs across every pet in this household."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Sort, filter, complete, and plan tasks across an owner's pets."""

    owner: Owner

    def sort_by_time(self, tasks=None) -> list[tuple[Pet, Task]]:
        """Sort a supplied collection, or all tasks, by date then time."""
        entries = self.owner.all_tasks() if tasks is None else tasks
        return sorted(entries, key=lambda entry: entry[1].starts_at)

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None,
        on_date: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter by pet name, completion status, and due date; None means any."""
        return [
            (pet, task) for pet, task in self.owner.all_tasks()
            if (pet_name is None or pet.name.casefold() == pet_name.casefold())
            and (completed is None or task.completed == completed)
            and (on_date is None or task.due_date == on_date)
        ]

    def find_task(self, task_id: str) -> tuple[Pet, Task]:
        """Look up a task's owning pet and object by its stable ID."""
        for pet, task in self.owner.all_tasks():
            if task.id == task_id:
                return pet, task
        raise ValueError("Task was not found.")

    def update_task(self, task_id: str, **changes) -> Task:
        """Validate an edit before replacing a pending task in its pet's list."""
        allowed = {
            "description", "time", "due_date", "duration_minutes",
            "priority", "frequency", "category",
        }
        if set(changes) - allowed:
            raise ValueError("Only task details can be edited.")
        pet, old = self.find_task(task_id)
        if old.completed:
            raise ValueError("Completed occurrences are kept as history and cannot be edited.")
        updated = replace(old, **changes)
        pet.tasks[pet.tasks.index(old)] = updated
        return updated

    def mark_task_complete(self, task_id: str, completed_on: date | None = None) -> Task | None:
        """Complete once and append the next daily/weekly occurrence, if any."""
        pet, task = self.find_task(task_id)
        if task.completed:
            return None
        completion_day = date.today() if completed_on is None else completed_on
        if type(completion_day) is not date:
            raise ValueError("Completion date must be a calendar date.")
        next_task = None
        interval = FREQUENCIES[task.frequency]
        if interval:
            try:
                next_date = max(task.due_date, completion_day) + timedelta(days=interval)
            except OverflowError as exc:
                raise ValueError("The next occurrence exceeds the supported date range.") from exc
            next_task = replace(task, due_date=next_date, completed=False, id=uuid4().hex)
            pet.add_task(next_task)
        task.mark_complete()
        return next_task

    @staticmethod
    def overlaps(first: Task, second: Task) -> bool:
        """Use half-open intervals so touching endpoints do not conflict."""
        return first.starts_at < second.ends_at and second.starts_at < first.ends_at

    def detect_conflicts(self, on_date: date | None = None) -> list[str]:
        """Describe overlapping pending tasks, including cross-midnight conflicts."""
        entries = self.sort_by_time(self.filter_tasks(completed=False))
        warnings = []
        for index, (pet, task) in enumerate(entries):
            for other_pet, other in entries[index + 1:]:
                if other.starts_at >= task.ends_at:
                    break
                if on_date is not None:
                    overlap_start = max(task.starts_at, other.starts_at)
                    overlap_end = min(task.ends_at, other.ends_at)
                    last_day = (overlap_end - timedelta(microseconds=1)).date()
                    if not overlap_start.date() <= on_date <= last_day:
                        continue
                warnings.append(
                    f"Conflict: {pet.name} / {task.description} "
                    f"({task.due_date} {task.time}) overlaps "
                    f"{other_pet.name} / {other.description} "
                    f"({other.due_date} {other.time})."
                )
        return warnings

    def build_plan(
        self, on_date: date, available_minutes: int,
    ) -> tuple[list[tuple[Pet, Task]], list[str]]:
        """Greedily choose fixed-time tasks by priority, preference, then time."""
        if type(available_minutes) is not int or not 0 <= available_minutes <= 1440:
            raise ValueError("Available time must be a whole number from 0 to 1440 minutes.")
        candidates = self.filter_tasks(completed=False, on_date=on_date)
        ranked = sorted(candidates, key=lambda entry: (
            PRIORITIES[entry[1].priority],
            entry[1].category != self.owner.preferred_category,
            entry[1].starts_at,
        ))
        selected = []
        reasons = []
        used = 0
        carryovers = [
            task for _, task in self.filter_tasks(completed=False)
            if task.due_date < on_date and task.ends_at.date() >= on_date
        ]
        for pet, task in ranked:
            label = f"{pet.name} / {task.description}"
            if any(self.overlaps(task, other) for other in carryovers):
                reasons.append(f"Skipped {label}: overlaps an overnight task.")
            elif any(self.overlaps(task, other) for _, other in selected):
                reasons.append(f"Skipped {label}: overlaps an already selected task.")
            elif used + task.duration_minutes > available_minutes:
                reasons.append(f"Skipped {label}: exceeds the remaining time budget.")
            else:
                selected.append((pet, task))
                used += task.duration_minutes
                preference = "; preferred activity" if task.category == self.owner.preferred_category else ""
                reasons.append(
                    f"Selected {label}: {task.priority} priority{preference}; "
                    f"{task.duration_minutes} min fits ({used}/{available_minutes} min used)."
                )
        return self.sort_by_time(selected), reasons
