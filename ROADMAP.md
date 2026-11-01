# Development roadmap

The owner reported that weekly execution planning was checked and confirmed Windows test notification visibility and active scheduler status. Checklists, reminder rules and backup/restore are implemented; backup acceptance and further platform validation remain pending. Remaining estimates below are provisional: 19–29 hours, excluding further Windows integration validation whose scope is not yet known. These are planning estimates, not measured or billable hours. The lower bound is below the program's 20-hour requirement; a submission must be based on a concrete, honestly scoped remaining plan rather than assuming the threshold is met.

| Task | Execution steps | Acceptance criteria | Estimate |
|---|---|---|---|
| Follow-up real-use validation | Test the requested features; record friction; prioritize changes | Actual owner feedback informs the workflow | 1–2 h |
| Project archiving | Define behavior; migrate storage; implement archive/restore; test | Archived projects retain tasks and can be restored; name/description editing is already implemented | 2–3 h |
| Search and filters | Define status/deadline filters; implement controls; test combinations | Find tasks without changing data or mixing projects | 3–4 h |
| Export and import | Define versioned JSON; validate input; handle conflicts; test round trips | Preserve content, relationships and statuses | 4–6 h |
| Multiple prerequisites | Extend the dependency model and editor; test combinations and migration | Multiple prerequisites preserve cycle protection; checklist and single-prerequisite support are already implemented | 2–4 h |
| Accessibility and interface | Review keyboard, focus, contrast and resizing; fix issues; validate | Core workflows work with keyboard and varied window sizes | 3–4 h |
| Packaging and release | Package for Windows; test clean installation; document upgrades | Reproducible distributable with verified instructions | 4–6 h |

## Current next step

Follow [the user acceptance checklist](docs/USER_ACCEPTANCE.md). Record actual observations before marking items complete. Select the next implementation priority from that feedback.

Implemented from feedback: chronological agenda, in-app alerts, numeric progress, descriptions, effort estimates, execution dates, single prerequisites, weekly capacity, effort-weighted progress, checklists, reminder timestamps and backup/restore. Immediate validation: owner acceptance of backup/restore and timed Windows notifications with the app closed. Basic Windows notification visibility and schedule activation are owner-confirmed.

## Submission preparation

1. Personally review the prototype and confirm interest in continued development.
2. Confirm personal ownership and absence of employer, client, university or company claims.
3. Publish the original repository with README and LICENSE, preserving real history.
4. Record genuine use and fixes over time. The program specifies no minimum project age.
5. Review files and history for secrets and personal data before publication and submission.
6. Update this roadmap to reflect genuinely desired work, with at least 20 hours remaining at submission.
7. Prepare the form using verifiable facts and disclose the early development stage.

The project has not been approved by the program. Compatible purpose and licensing do not guarantee selection.
