"""Exercise Streamlit form submission, reruns, and domain integration."""

from pathlib import Path
from datetime import date, timedelta

from streamlit.testing.v1 import AppTest

from pawpal_system import Owner, Pet, Task

APP = Path(__file__).resolve().parents[1] / "app.py"


def widget(elements, label):
    """Find a widget by its user-facing label."""
    return next(element for element in elements if element.label == label)


def test_add_pet_task_edit_complete_and_plan():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    widget(app.text_input, "Pet name").input("Biscuit")
    widget(app.button, "Add pet").click().run()
    assert not app.exception
    assert app.session_state.owner.pets[0].name == "Biscuit"
    widget(app.text_input, "Task description").input("Breakfast")
    widget(app.selectbox, "Repeat").select("daily")
    widget(app.button, "Schedule task").click().run()
    assert not app.exception
    assert len(app.session_state.owner.pets[0].tasks) == 1
    widget(app.text_input, "Edit description").input("Morning breakfast")
    widget(app.number_input, "Edit duration").set_value(20)
    widget(app.button, "Save task changes").click().run()
    assert not app.exception
    task = app.session_state.owner.pets[0].tasks[0]
    assert task.description == "Morning breakfast"
    assert task.duration_minutes == 20
    widget(app.button, "Generate plan").click().run()
    assert not app.exception
    assert any(metric.value == "20" for metric in app.metric)
    widget(app.button, "Complete: Biscuit — Morning breakfast").click().run()
    assert not app.exception
    tasks = app.session_state.owner.pets[0].tasks
    assert len(tasks) == 2
    assert tasks[0].completed
    assert not tasks[1].completed
    assert tasks[1].due_date > tasks[0].due_date


def test_demo_conflicts_and_pet_filter():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    widget(app.button, "Load example household").click().run()
    assert not app.exception
    assert len(app.session_state.owner.pets) == 2
    assert any("Conflict:" in warning.value for warning in app.warning)
    widget(app.selectbox, "Filter by pet").select("Pet: Luna").run()
    assert not app.exception
    assert set(app.dataframe[0].value["Pet"]) == {"Luna"}
    assert any("Mochi" in warning.value for warning in app.warning)
    widget(app.button, "Generate plan").click().run()
    assert not app.exception
    assert any("Skipped Luna / Grooming" in warning.value for warning in app.warning)


def test_validation_and_owner_settings_survive_reruns():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    widget(app.button, "Add pet").click().run()
    assert any("cannot be blank" in error.value for error in app.error)
    assert app.session_state.owner.pets == []
    widget(app.text_input, "Owner name").input("Jordan")
    widget(app.selectbox, "Preferred activity").select("walk")
    widget(app.button, "Save owner").click().run()
    assert not app.exception
    assert app.session_state.owner.name == "Jordan"
    assert app.session_state.owner.preferred_category == "walk"


def test_duplicate_descriptions_can_be_edited_independently():
    app = AppTest.from_file(str(APP), default_timeout=30)
    first = Task("Feed", "08:00", duration_minutes=5)
    second = Task("Feed", "08:00", duration_minutes=10)
    app.session_state.owner = Owner("Jordan", [Pet("Mochi", "dog", [first, second])])
    app.run()
    selector = widget(app.selectbox, "Task to edit")
    assert len(set(selector.options)) == 2
    selector.select(selector.options[1]).run()
    widget(app.text_input, "Edit description").input("Second feeding")
    widget(app.button, "Save task changes").click().run()
    assert not app.exception
    tasks = app.session_state.owner.pets[0].tasks
    assert tasks[0].description == "Feed"
    assert tasks[1].description == "Second feeding"


def test_pet_named_all_pets_can_be_filtered():
    app = AppTest.from_file(str(APP), default_timeout=30)
    app.session_state.owner = Owner("Jordan", [
        Pet("All pets", "dog", [Task("Walk", "08:00")]),
        Pet("Luna", "cat", [Task("Feed", "09:00")]),
    ])
    app.run()
    selector = widget(app.selectbox, "Filter by pet")
    assert len(set(selector.options)) == 3
    selector.select("Pet: All pets").run()
    assert not app.exception
    assert set(app.dataframe[0].value["Pet"]) == {"All pets"}
    widget(app.selectbox, "Filter by pet").select("All pets").run()
    assert set(app.dataframe[0].value["Pet"]) == {"All pets", "Luna"}


def test_future_recurring_task_remains_reachable_in_date_filters():
    app = AppTest.from_file(str(APP), default_timeout=30)
    future_day = date(2040, 1, 1)
    task = Task("Daily care", "08:00", future_day, frequency="daily")
    app.session_state.owner = Owner("Jordan", [Pet("Mochi", "dog", [task])])
    app.run()
    assert not app.exception
    for label in ["Due date", "Edit date", "Schedule date", "Plan date"]:
        picker = widget(app.date_input, label)
        assert picker.proto.min == date.min.isoformat()
        assert picker.proto.max == date.max.isoformat()
    widget(app.date_input, "Schedule date").set_value(future_day).run()
    widget(app.button, "Complete: Mochi — Daily care").click().run()
    following_day = future_day + timedelta(days=1)
    widget(app.date_input, "Schedule date").set_value(following_day).run()
    assert not app.exception
    assert list(app.dataframe[0].value["Date"]) == [following_day.isoformat()]
    assert list(app.dataframe[0].value["Status"]) == ["Pending"]
    widget(app.date_input, "Plan date").set_value(following_day)
    widget(app.button, "Generate plan").click().run()
    assert not app.exception
    assert any(metric.value == "15" for metric in app.metric)
