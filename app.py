"""Streamlit interface for the PawPal+ domain model."""

from datetime import date, time

import streamlit as st

from main import make_demo_owner
from pawpal_system import CATEGORIES, FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+ | Daily care", page_icon="🐾", layout="wide")


def schedule_rows(entries):
    """Convert domain objects to readable table records."""
    return [{
        "Date": task.due_date.isoformat(), "Time": task.time,
        "Pet": pet.name, "Task": task.description,
        "Minutes": task.duration_minutes, "Priority": task.priority.title(),
        "Repeats": task.frequency.title(),
        "Status": "Complete" if task.completed else "Pending",
    } for pet, task in entries]


def show_schedule(entries):
    """Display a schedule or a useful empty state."""
    if entries:
        st.dataframe(schedule_rows(entries), hide_index=True, width="stretch")
    else:
        st.info("No tasks match these filters.")


def flash(message):
    """Preserve a confirmation across the next Streamlit rerun."""
    st.session_state.notice = message
    st.rerun()


def save_task(task_id):
    """Apply form edits before the next render so widget options stay current."""
    state = st.session_state
    try:
        Scheduler(state.owner).update_task(
            task_id,
            description=state[f"description_{task_id}"],
            due_date=state[f"date_{task_id}"],
            time=state[f"time_{task_id}"].strftime("%H:%M"),
            duration_minutes=int(state[f"duration_{task_id}"]),
            priority=state[f"priority_{task_id}"],
            frequency=state[f"frequency_{task_id}"],
            category=state[f"category_{task_id}"],
        )
        state.notice = "Task updated. The schedule and conflicts have been recalculated."
    except ValueError as exc:
        state.notice_error = str(exc)


def complete_task(task_id):
    """Complete a task before rerendering the schedule and editor controls."""
    try:
        active_scheduler = Scheduler(st.session_state.owner)
        _, task = active_scheduler.find_task(task_id)
        next_task = active_scheduler.mark_task_complete(task_id)
        message = f"Completed {task.description}."
        if next_task:
            message += f" Next occurrence: {next_task.due_date} at {next_task.time}."
        st.session_state.notice = message
    except ValueError as exc:
        st.session_state.notice_error = str(exc)


if "owner" not in st.session_state:
    st.session_state.owner = Owner("Pet owner")
owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("A little structure. A happier day for every pet.")
notice_area = st.empty()
error_area = st.empty()
if "notice" in st.session_state:
    notice_area.success(st.session_state.pop("notice"))
if "notice_error" in st.session_state:
    error_area.error(st.session_state.pop("notice_error"))

with st.sidebar:
    st.header("Your household")
    with st.form("owner_settings"):
        name = st.text_input("Owner name", value=owner.name)
        preferences = ["none", *CATEGORIES]
        preference = st.selectbox("Preferred activity", preferences,
                                  index=preferences.index(owner.preferred_category))
        st.caption("Preference breaks ties between tasks with the same priority.")
        if st.form_submit_button("Save owner"):
            try:
                updated_owner = Owner(name, owner.pets, preference)
                st.session_state.owner = updated_owner
                flash("Owner preferences saved.")
            except ValueError as exc:
                st.error(str(exc))
    st.divider()
    if not owner.pets and st.button("Load example household"):
        st.session_state.owner = make_demo_owner(date.today())
        flash("Loaded Mochi and Luna with five example care tasks.")
    st.caption("Data stays through interactions in this browser session. Reloading or closing the session can clear it; there is no disk storage.")

pending = scheduler.filter_tasks(completed=False)
metrics = st.columns(3)
metrics[0].metric("Pets", len(owner.pets))
metrics[1].metric("Pending tasks", len(pending))
metrics[2].metric("Completed", len(scheduler.filter_tasks(completed=True)))

schedule_tab, pets_tab, tasks_tab, plan_tab = st.tabs([
    "Daily schedule", "Pets", "Add / edit tasks", "Build a plan",
])

with pets_tab:
    st.subheader("Make room for another friend")
    with st.form("add_pet", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        if st.form_submit_button("Add pet"):
            try:
                owner.add_pet(Pet(pet_name, species))
                flash(f"Added {pet_name.strip()} to your household.")
            except ValueError as exc:
                st.error(str(exc))
    if owner.pets:
        st.table([{"Pet": pet.name, "Species": pet.species, "Tasks": len(pet.tasks)} for pet in owner.pets])
    else:
        st.info("Add your first pet, or load the example household in the sidebar.")

with tasks_tab:
    st.subheader("Plan the care they count on")
    if not owner.pets:
        st.info("Add a pet before scheduling a task.")
    else:
        pet_names = [pet.name for pet in owner.pets]
        with st.form("add_task", clear_on_submit=True):
            chosen_pet = st.selectbox("Task's pet", pet_names)
            description = st.text_input("Task description", placeholder="e.g. Morning walk")
            columns = st.columns(3)
            task_date = columns[0].date_input("Due date", date.today(), min_value=date.min, max_value=date.max)
            task_time = columns[1].time_input("Due time", time(8))
            duration = columns[2].number_input("Duration (minutes)", 1, 240, 15)
            columns = st.columns(3)
            priority = columns[0].selectbox("Priority", list(PRIORITIES))
            frequency = columns[1].selectbox("Repeat", list(FREQUENCIES))
            category = columns[2].selectbox("Activity type", list(CATEGORIES))
            if st.form_submit_button("Schedule task"):
                try:
                    task = Task(description, task_time.strftime("%H:%M"), task_date,
                                int(duration), priority, frequency, category)
                    pet = next(pet for pet in owner.pets if pet.name == chosen_pet)
                    pet.add_task(task)
                    flash(f"Scheduled {task.description} for {pet.name}.")
                except ValueError as exc:
                    st.error(str(exc))

        editable = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
        if editable:
            st.divider()
            st.subheader("Edit a pending task")
            labels = {
                task.id: f"{index}. {pet.name} · {task.description} · {task.due_date} {task.time}"
                for index, (pet, task) in enumerate(editable, start=1)
            }
            chosen_label = st.selectbox("Task to edit", list(labels.values()), key="task_to_edit")
            edit_id = next(task_id for task_id, label in labels.items() if label == chosen_label)
            _, current = scheduler.find_task(edit_id)
            with st.form(f"edit_{edit_id}"):
                st.text_input("Edit description", current.description, key=f"description_{edit_id}")
                columns = st.columns(3)
                columns[0].date_input("Edit date", current.due_date, min_value=date.min,
                                     max_value=date.max, key=f"date_{edit_id}")
                columns[1].time_input("Edit time", current.starts_at.time(), key=f"time_{edit_id}")
                columns[2].number_input("Edit duration", 1, 240, current.duration_minutes, key=f"duration_{edit_id}")
                columns = st.columns(3)
                columns[0].selectbox("Edit priority", list(PRIORITIES), index=list(PRIORITIES).index(current.priority), key=f"priority_{edit_id}")
                columns[1].selectbox("Edit repeat", list(FREQUENCIES), index=list(FREQUENCIES).index(current.frequency), key=f"frequency_{edit_id}")
                columns[2].selectbox("Edit activity type", list(CATEGORIES), index=list(CATEGORIES).index(current.category), key=f"category_{edit_id}")
                st.form_submit_button("Save task changes", on_click=save_task, args=(edit_id,))

with schedule_tab:
    st.subheader("One view. Every pet.")
    columns = st.columns(3)
    selected_day = columns[0].date_input("Schedule date", date.today(), min_value=date.min, max_value=date.max)
    pet_filters = {"All pets": None, **{f"Pet: {pet.name}": pet.name for pet in owner.pets}}
    selected_pet = columns[1].selectbox("Filter by pet", list(pet_filters))
    status = columns[2].selectbox("Filter by status", ["All", "Pending", "Complete"])
    completed = {"All": None, "Pending": False, "Complete": True}[status]
    entries = scheduler.sort_by_time(scheduler.filter_tasks(
        pet_filters[selected_pet], completed, selected_day,
    ))
    show_schedule(entries)
    warnings = scheduler.detect_conflicts(selected_day)
    if warnings:
        st.caption("Household warnings include every pet, regardless of the pet filter.")
        for warning in warnings:
            st.warning(warning)
    elif entries:
        st.success("No overlapping pending tasks for this day.")
    overdue = [task for _, task in pending if task.due_date < date.today()]
    if overdue:
        st.warning(f"{len(overdue)} overdue task(s). Change the schedule date to review them.")
    for pet, task in entries:
        if not task.completed:
            st.button(f"Complete: {pet.name} — {task.description}", key=f"complete_{task.id}",
                      on_click=complete_task, args=(task.id,))

with plan_tab:
    st.subheader("Spend your care time where it matters")
    st.write("Choose high-priority tasks first, then your preferred activity, then the earliest time. Tasks keep their scheduled times.")
    plan_day = st.date_input("Plan date", date.today(), min_value=date.min, max_value=date.max)
    budget = st.number_input("Available care time (minutes)", 0, 1440, 75)
    if st.button("Generate plan"):
        st.session_state.plan_request = (plan_day, int(budget))
    if "plan_request" in st.session_state:
        requested_day, requested_budget = st.session_state.plan_request
        st.caption(f"Generated for {requested_day} with {requested_budget} minutes. Click Generate plan to use changed inputs.")
        plan, explanations = scheduler.build_plan(requested_day, requested_budget)
        show_schedule(plan)
        st.metric("Planned care minutes", sum(task.duration_minutes for _, task in plan))
        for explanation in explanations:
            if explanation.startswith("Skipped"):
                st.warning(explanation)
            else:
                st.write(explanation)
        st.caption("A skipped task stays pending. This plan does not move appointments or mark tasks complete.")
