# Development log

All project documentation and future development records are maintained in English. Application text is currently Portuguese. Existing commits are preserved.

## November 1, 2026 — Initial prototype

- The owner selected a personal project planner as the project direction.
- Created the Python/Tkinter application and SQLite persistence layer.
- Implemented projects, task editing, deadlines, statuses, progress and overdue highlighting.
- Added MIT licensing, README, ignore rules and a roadmap.
- Recorded the implementation in commit 7361c70.
- All five automated tests passed: persistence/progress, rejected input, project isolation/foreign keys, task ordering, and rejected edits.
- The first GUI smoke check failed when the bundled Tcl runtime could not load its library from the installed location. Copying Tcl/Tk libraries into the development workspace and configuring TCL_LIBRARY and TK_LIBRARY resolved startup in this environment. No application change was required.
- The subsequent GUI smoke check passed: application initialization, project selection, task display, overdue count and opening the task dialog.
- These checks do not establish visual quality, accessibility, packaging readiness or owner acceptance.

## November 1, 2026 — Documentation and owner-test preparation

- Translated the roadmap into English without changing scope or estimates.
- Added an owner acceptance checklist with explicitly pending results.
- Added this development log.
- Prepared a development-computer launcher outside the repository. It uses bundled Python and workspace Tcl/Tk libraries; it is not a portable release package.
- Documentation changes do not require rerunning unchanged persistence tests.

## Outstanding evidence

Initial owner feedback has been received (see below). Feature acceptance, visual/accessibility review, clean-machine installation, ownership certification, full secret/history review, GitHub publication and program submission remain pending.

## November 1, 2026 — Owner-requested agenda, alerts and project details

- The owner said the prototype worked and requested deadline alerts, an agenda, explicit completion percentages and project descriptions.
- Added an agenda listing dated unfinished tasks across all projects in deadline order.
- Added an in-app alert banner and system bell for overdue tasks and deadlines today or tomorrow. Checks run at startup, after saves and every minute while the app is open. Repeated checks suppress sound for unchanged task/date combinations within the running session. Restarting the app or reaching a new local date can alert again.
- Displayed equal-weight completion percentages in the sidebar and project summary. In-progress tasks are not treated as complete; empty projects show 0%.
- Added project name editing and multiline description editing. Existing database fields and saved data remain compatible; no schema migration was necessary.
- All nine persistence/business-rule tests passed, including reminder boundaries across year-end and project description persistence.
- The explicit GUI smoke check passed for agenda filtering, repeated-alert suppression, description editing and displayed percentage changes.
- No background notification service was installed. Owner acceptance of these new features is pending.

## November 1, 2026 — Weekly execution planning

- The owner confirmed the previous iteration worked, questioned the project's depth and agreed to pursue a more useful weekly execution planner. This is qualitative feedback, not confirmation that every acceptance step was performed.
- Added optional effort estimates, execution dates and one same-project prerequisite per task.
- Added cycle rejection, blocked-state enforcement and protection against reopening a prerequisite while dependent work is active or complete.
- Added a Monday–Sunday cross-project view, week navigation, persisted weekly capacity and workload/risk summaries.
- Added effort-weighted progress without replacing task-count progress. Unknown estimates remain explicit.
- Added automatic pre-upgrade database backup when existing tasks are present, followed by transactional schema changes.
- The migration test initially exposed open SQLite backup handles on Windows. Explicit connection closing fixed the issue in both implementation and test fixtures.
- All 16 automated tests passed after the fix, including legacy-data preservation, backup-once behavior, planning persistence, weekly boundaries, invalid inputs, dependencies and progress calculations.
- The GUI smoke check passed, including planning dialog submission, weekly overload display, navigation and stored capacity, as well as the earlier agenda/description/progress checks.
- Documentation is in English. Owner acceptance and visual/accessibility review of this iteration remain pending.
