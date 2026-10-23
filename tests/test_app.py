"""Exercise Streamlit form submission, reruns, and domain integration."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def widget(elements, label):
    """Find a widget by its user-facing label."""
    return next(element for element in elements if element.label == label)


def test_add_pet_task_edit_complete_and_plan():
    app = AppTest.from_file(str(APP)).run()
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
    app = AppTest.from_file(str(APP)).run()
    widget(app.button, "Load example household").click().run()
    assert not app.exception
    assert len(app.session_state.owner.pets) == 2
    assert any("Conflict:" in warning.value for warning in app.warning)
    widget(app.selectbox, "Filter by pet").select("Luna").run()
    assert not app.exception
    assert set(app.dataframe[0].value["Pet"]) == {"Luna"}
    assert any("Mochi" in warning.value for warning in app.warning)
    widget(app.button, "Generate plan").click().run()
    assert not app.exception
    assert any("Skipped Luna / Grooming" in warning.value for warning in app.warning)


def test_validation_and_owner_settings_survive_reruns():
    app = AppTest.from_file(str(APP)).run()
    widget(app.button, "Add pet").click().run()
    assert any("cannot be blank" in error.value for error in app.error)
    assert app.session_state.owner.pets == []
    widget(app.text_input, "Owner name").input("Jordan")
    widget(app.selectbox, "Preferred activity").select("walk")
    widget(app.button, "Save owner").click().run()
    assert not app.exception
    assert app.session_state.owner.name == "Jordan"
    assert app.session_state.owner.preferred_category == "walk"
