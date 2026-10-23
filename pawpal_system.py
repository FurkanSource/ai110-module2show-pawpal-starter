"""Domain objects and scheduling rules for PawPal+."""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    """A dated pet-care activity."""

    description: str
    time: str
    due_date: date
    duration_minutes: int = 15
    priority: str = "medium"
    frequency: str = "once"
    completed: bool = False

    def mark_complete(self):
        """Mark this occurrence complete."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet and its care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task):
        """Add one care task."""
        raise NotImplementedError


@dataclass
class Owner:
    """An owner and their pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet):
        """Add a pet to this household."""
        raise NotImplementedError

    def all_tasks(self):
        """Collect pet-task pairs across the household."""
        raise NotImplementedError


@dataclass
class Scheduler:
    """Organize an owner's tasks without UI dependencies."""

    owner: Owner

    def sort_by_time(self):
        """Return household tasks in chronological order."""
        raise NotImplementedError

    def filter_tasks(self):
        """Select tasks by pet, date, and completion status."""
        raise NotImplementedError

    def mark_task_complete(self, task_id):
        """Complete a task and create its next recurring occurrence."""
        raise NotImplementedError

    def detect_conflicts(self):
        """Report overlapping pending tasks."""
        raise NotImplementedError

    def build_plan(self):
        """Choose non-overlapping tasks within the owner's time budget."""
        raise NotImplementedError
