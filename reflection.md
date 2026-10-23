# PawPal+ Project Reflection

This reflection records confirmed student decisions and the AI-assisted process.
It does not claim that Furkan independently wrote or personally tested the code.

## 1. System Design

### a. Initial design

Three user actions are adding a pet, scheduling/completing a care task, and
viewing a daily household schedule. The AI-generated draft used four classes:
Task for one activity, Pet for its identifying details and tasks, Owner for pets
and a preference, and Scheduler for cross-pet organization. This keeps scheduling
rules separate from Streamlit, so the same behavior can be exercised in a CLI.

### b. Design changes

The implementation added unique task IDs so two tasks with the same description
can still be edited or completed independently. It added interval endpoints for
duration-based conflict detection rather than only comparing exact times.
The final UML also includes task editing and the owner's preferred activity.
These changes were made by Codex, not independently coded by Furkan.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities

Confirmed student choice: “Priority first, then preferred activity type.”
The scheduler considers a daily minute budget, priority, owner preference,
scheduled time and overlapping intervals. The preference only breaks ties at
the same priority; it cannot move a low-priority walk ahead of a high-priority
task. This is the policy Furkan chose when offered priority-first versus
shortest-task-first planning.

### b. Tradeoffs

The chosen policy can finish fewer tasks than shortest-first scheduling. For
example, with 20 minutes available, a 20-minute high-priority activity is selected
before a 5-minute low-priority activity. This favors important care rather than
the number of completed tasks. The greedy algorithm is easy to explain but does
not search for a mathematically optimal combination. Skipped tasks remain visible
and pending, and the plan never silently moves an appointment.

## 3. AI Collaboration

### a. How AI was used

Furkan asked Codex to inspect the CodePath instructions and complete Project 2,
then confirmed “starting fresh.” Codex read the starter
and rubric, generated a design/UML, implemented the backend and Streamlit UI,
created tests, ran the demo, checked the browser and prepared documentation.
The useful capabilities were multi-file editing, running tests, and browser
inspection. Work stayed in one main chat with a focused Python review agent;
separate student chat sessions for each phase were not used.

### b. Judgment and verification

Furkan accepted priority-first planning and chose it over the shortest-task-first
alternative. This is a real student decision, not an invented rejection story.
The implementation also changed after verification: the first edit form used an
immediate rerun that left stale selector state in the UI test. Codex replaced
the edit and completion handlers with callbacks that update the data before
rendering. Automated tests then passed. That debugging work was performed by
the AI agent, not by Furkan personally.

## 4. Testing and Verification

### a. What was tested

The AI-generated suite contains 47 passing cases covering the core objects,
sorting, filters, recurrence, conflicts, budgets, invalid inputs, and Streamlit
forms. Calendar boundaries and double completion matter because recurrence must
create exactly one valid next occurrence. Cross-pet overlap tests matter because
the owner cannot perform two care activities simultaneously. UI tests check that
backend correctness is actually connected to the forms and survives reruns.

The README contains captured CLI and pytest output. Verification was run by
Codex; Furkan has not reported personally running these tests.

### b. Confidence

Furkan rated his confidence **5/5**. Codex ran the tests and browser checks;
Furkan has not reported running them himself or supplied a reason for the rating.
Codex's technical assessment is 4/5 because the tested behavior works, while
timezone/DST handling and saved-data recovery remain outside the current scope.

## 5. Reflection

### a. What went well

The four-class design supports both the CLI and UI, and the priority-first rule
is explicit and testable. Furkan selected that rule and a preferred-activity
tie break; he has not identified a personal favorite part of the implementation.

### b. What would be improved

A concrete technical next step is disk persistence so a browser reload does not
lose tasks. This is a proposed improvement from Codex, not a student-selected one.

### c. Key takeaway

The lead-architect decision evidenced in this project was setting the scheduling
policy: priority first, then preferred activity type. AI generated the code and
test suite and performed the verification. The edit-to-plan integration test
caught a UI state bug after backend tests passed, illustrating why the result
needed end-to-end checks. Furkan has not supplied a personal learning statement.
