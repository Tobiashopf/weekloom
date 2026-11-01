# Development roadmap

Initial owner feedback has been received. The owner reported the agenda/progress/description iteration worked and agreed to develop a weekly execution planner. Effort estimates, execution dates, single-prerequisite dependencies and weekly capacity are now implemented and await owner acceptance. Remaining estimates below are provisional: 24–36 hours. They are planning estimates, not measured or billable hours.

| Task | Execution steps | Acceptance criteria | Estimate |
|---|---|---|---|
| Follow-up real-use validation | Test the requested features; record friction; prioritize changes | Actual owner feedback informs the workflow | 1–2 h |
| Project archiving | Define behavior; migrate storage; implement archive/restore; test | Archived projects retain tasks and can be restored; name/description editing is already implemented | 2–3 h |
| Search and filters | Define status/deadline filters; implement controls; test combinations | Find tasks without changing data or mixing projects | 3–4 h |
| Backup and restore | Create consistent copies; validate format; protect original data; test failures | Restore projects and tasks; reject invalid files | 4–6 h |
| Export and import | Define versioned JSON; validate input; handle conflicts; test round trips | Preserve content, relationships and statuses | 4–6 h |
| Subtask checklists and multiple prerequisites | Define checklist semantics; extend the dependency model and editor; test combinations | Checklist completion is useful and multiple prerequisites preserve cycle protection; single-prerequisite support is already implemented | 3–5 h |
| Accessibility and interface | Review keyboard, focus, contrast and resizing; fix issues; validate | Core workflows work with keyboard and varied window sizes | 3–4 h |
| Packaging and release | Package for Windows; test clean installation; document upgrades | Reproducible distributable with verified instructions | 4–6 h |

## Current next step

Follow [the user acceptance checklist](docs/USER_ACCEPTANCE.md). Record actual observations before marking items complete. Select the next implementation priority from that feedback.

Implemented from feedback: chronological agenda, in-app date-based alerts, numeric progress, editable multiline descriptions, effort estimates, execution dates, single prerequisites, weekly capacity and effort-weighted progress. Follow-up not yet estimated: time-of-day reminders and native Windows notifications while the application is closed. A scheduling design and operating-system validation are still needed.

## Submission preparation

1. Personally review the prototype and confirm interest in continued development.
2. Confirm personal ownership and absence of employer, client, university or company claims.
3. Publish the original repository with README and LICENSE, preserving real history.
4. Record genuine use and fixes over time. The program specifies no minimum project age.
5. Review files and history for secrets and personal data before publication and submission.
6. Update this roadmap to reflect genuinely desired work, with at least 20 hours remaining at submission.
7. Prepare the form using verifiable facts and disclose the early development stage.

The project has not been approved by the program. Compatible purpose and licensing do not guarantee selection.
