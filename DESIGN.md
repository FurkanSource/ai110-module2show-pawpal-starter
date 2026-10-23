# Design plan

Three core actions: register a pet; schedule and complete a care task; view a
sorted daily schedule across all pets with conflict warnings.

Keep four domain classes in `pawpal_system.py`, separate from Streamlit. Owner
contains pets, each Pet contains tasks, and Scheduler operates on the Owner.
Task and Pet use dataclasses with independent default lists.

Use calendar dates plus normalized HH:MM times. Preserve completed occurrences
and create a new pending occurrence for daily/weekly recurrence. Generate the
next date from the later of the original due date and completion date so overdue
tasks do not create another overdue task. Use unique IDs for task identity.

Sort chronologically; filter by pet, date and completion state. Warn about
overlapping time intervals across the whole household. Adjacent tasks are valid.
For a daily plan, choose high-priority tasks first, then owner-preferred activity
types, then due time, within a minute budget and without overlaps. Explain skips.
This greedy plan does not optimize total utility or reschedule fixed appointments.

CLI comes before UI. Verify recurrence, filters, cross-pet conflicts, validation,
budget boundaries, and Streamlit forms with pytest. Documentation will record
actual command output and explicitly distinguish AI work from student work.
