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

Owner feedback, visual/accessibility review, clean-machine installation, ownership certification, full secret/history review, GitHub publication and program submission remain pending.
