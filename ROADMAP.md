# Development roadmap

Initial owner feedback has been received. The owner requested an agenda, approaching-deadline alerts, explicit completion percentages and project descriptions. An initial implementation is complete and awaits owner acceptance. The remaining estimates below are provisional: 26–38 hours.

| Task | Execution steps | Acceptance criteria | Estimate |
|---|---|---|---|
| Follow-up real-use validation | Test the requested features; record friction; prioritize changes | Actual owner feedback informs the workflow | 1–2 h |
| Project archiving | Define behavior; migrate storage; implement archive/restore; test | Archived projects retain tasks and can be restored; name/description editing is already implemented | 2–3 h |
| Search and filters | Define status/deadline filters; implement controls; test combinations | Find tasks without changing data or mixing projects | 3–4 h |
| Backup and restore | Create consistent copies; validate format; protect original data; test failures | Restore projects and tasks; reject invalid files | 4–6 h |
| Export and import | Define versioned JSON; validate input; handle conflicts; test round trips | Preserve content, relationships and statuses | 4–6 h |
| Checklists and dependencies | Define subtasks and blockers; reject cycles; build controls; test chains | Dependencies are visible and cycles are rejected | 5–7 h |
| Accessibility and interface | Review keyboard, focus, contrast and resizing; fix issues; validate | Core workflows work with keyboard and varied window sizes | 3–4 h |
| Packaging and release | Package for Windows; test clean installation; document upgrades | Reproducible distributable with verified instructions | 4–6 h |

## Current next step

Follow [the user acceptance checklist](docs/USER_ACCEPTANCE.md). Record actual observations before marking items complete. Select the next implementation priority from that feedback.

Implemented from feedback: chronological agenda, in-app date-based alerts, numeric progress and editable multiline descriptions. Possible follow-up, not included in estimates: time-of-day reminders and native Windows notifications while the application is closed. Confirm the need before selecting a background scheduling design.

## Submission preparation

1. Personally review the prototype and confirm interest in continued development.
2. Confirm personal ownership and absence of employer, client, university or company claims.
3. Publish the original repository with README and LICENSE, preserving real history.
4. Record genuine use and fixes over time. The program specifies no minimum project age.
5. Review files and history for secrets and personal data before publication and submission.
6. Update this roadmap to reflect genuinely desired work, with at least 20 hours remaining at submission.
7. Prepare the form using verifiable facts and disclose the early development stage.

The project has not been approved by the program. Compatible purpose and licensing do not guarantee selection.
