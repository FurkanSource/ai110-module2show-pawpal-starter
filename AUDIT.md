# Two-pass project review

Requested by Furkan on October 23, 2026: “go over everything twice”.
This records checks performed by Codex; it is not a student learning reflection.

## Pass 1: requirements, source and evidence

The official CodePath Project 2 rubric was reread in the browser. Every source,
test, diagram, configuration and documentation file was reviewed against it.

| Required area | Evidence | Result |
| --- | --- | --- |
| UML: four classes, attributes, methods, relationships | `diagrams/uml_draft.mmd`, `diagrams/uml_final.mmd`; final diagram embedded in README | Present; final source matches code |
| Core OOP implementation | `Task`, `Pet`, `Owner`, `Scheduler` in `pawpal_system.py` | Present; logic independent of UI |
| Multiple algorithmic features across pets | Time sorting, combined filters, conflicts, recurrence, budgeted priority plan | Present and tested |
| End-to-end CLI | `main.py`: one owner, two pets, five tasks, formatted output | Runs; output matches saved evidence |
| Pytest | Domain and Streamlit AppTest suites | Original 41 cases passed before new audit fixes |
| README | Setup, classes, algorithm/method mapping, walkthrough, CLI and test output | Present; walkthrough clarified for edited sample data |
| AI reflection | `reflection.md`, `ai_interactions.md` | Technical details, confirmed student design choice and 5/5 confidence rating present; no personal learning claim invented |
| UI instructions | Owner/pet/task forms, editing, completion, sorting, filters, warnings, state, plan explanations | Present and exercised by UI tests |
| Repository preparation | Public fork, phased commits, required source files | Verified; no CodePath submission performed |

Initial Ruff check passed. Mypy found no issues in the backend and CLI.
The repository contains no starter placeholder UML or tracked Python bytecode.

## Pass 2: independent review and edge-case verification

A focused Python review agent reread the current project independently.
The following findings were reproduced and corrected:

1. **Pet-filter collision:** a valid pet named `All pets` duplicated the special
   filter choice. Individual choices now use `Pet: <name>` and map explicitly
   to domain names; the all-pets option maps to `None`.
2. **Date overflow:** a task at 9999-12-31 23:59 could be accepted even if its
   duration crossed Python's maximum datetime. Task validation now rejects an
   unrepresentable end before insertion, editing, or recurrence changes state.
   Separate tests verify creation, failed-edit atomicity, and failed-recurrence
   atomicity. These tests failed on the old implementation before the fix.
3. **Date-picker reachability:** Streamlit's default date window could hide a
   future recurring occurrence. Add, edit, schedule and plan pickers now use
   explicit calendar limits. A UI test completes a 2040 task and finds its next
   occurrence in both the schedule and the generated plan.

The final suite has **47 passing cases**. One case checks **200 seeded random
households** against an independent integer-minute conflict oracle, and also
checks chronological plans, budget limits, no overlaps and no task mutation.
The independent reviewer found no further concrete code blockers after the fixes.

Ruff and Mypy were rerun after the fixes and passed. The CLI output was compared
with the committed text and README, and the final UML source was compared with
the README's embedded diagram; all matched. A fresh live-browser session added
a pet named `All pets`, scheduled a task on 2040-01-01 and successfully selected
`Pet: All pets` to show that task. See `evidence/browser-audit.png`.

## Student input and limits

Furkan selected priority-first scheduling with a preferred-activity tie break,
provided a 5/5 confidence rating and estimated one hour of personal time.
He has not reported a personal code review, test run or learning takeaway; none
is attributed to him. This audit does not predict or guarantee a grade.

Optional disk persistence and a two-model/prompt comparison were not implemented
and are not claimed.
