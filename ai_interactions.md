# AI Interactions Log

## Agent Workflow

Tool: OpenAI Codex, including a focused Python review agent.

Actual student request: “go through my browser on the codepath site and figure
out what needs to be done for project 2 and complete it but dont submit it”.
Furkan confirmed he was starting fresh. When offered priority-first versus
shortest-task-first planning, he selected “Priority first, then preferred
activity type.”

The agent read all six phases and the grading rubric in the logged-in CodePath
browser, cloned the official starter, created a draft UML and class skeleton
commit, then implemented the backend before the Streamlit UI. Files added or
modified: `pawpal_system.py`, `main.py`, `app.py`, `tests/test_pawpal.py`,
`tests/test_app.py`, `diagrams/uml_draft.mmd`, `diagrams/uml_final.mmd`,
`.streamlit/config.toml`, `requirements.txt`, `DESIGN.md`, `README.md`,
`reflection.md`, and evidence files.

The advanced algorithm is `Scheduler.build_plan()`: it chooses tasks by priority,
then owner preference, avoids overlaps and enforces a time budget. It returns
reasons for inclusion and exclusion. The README contains actual CLI output
demonstrating that feature. It is a greedy algorithm, not an optimal solver.

Verification: CLI execution, 41 passing pytest cases including Streamlit AppTest,
a focused code review, and live browser checks. The review and tests identified
an edit-to-plan state failure. Explicit widget keys alone did not solve it;
updating tasks in a form callback before rendering did. A type annotation and a
check for the optional recurrence result were also added after review.

A follow-up review caught ambiguous edit labels when two tasks have identical
descriptions and times. Numbered choices now distinguish them; a regression test
verifies that editing the second leaves the first untouched. A live browser check
also confirmed that the selected plan tab remains visible after regeneration.

Manual student corrections: none reported. The priority policy is confirmed
student input. The code, test execution and debugging were AI work. No independent
student implementation, personal test run, or understanding of every line is
claimed. No CodePath submission was made.

## Prompt comparison

No two-model or two-prompt experiment was conducted; no comparison stretch credit
is claimed. Choosing between two scheduling policies is a product decision, not
a fabricated model-comparison experiment.
