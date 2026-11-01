# Weekloom

Previously named Plano Local. The rename preserves existing project data, backups and reminder schedules. Compatibility paths and identifiers (`PlanoLocal`, `PlanoLocal-Reminders-*` and `.plano-backup`) remain supported; new backups identify the application as Weekloom and old backups can still be restored.

A desktop planner for personal projects, written in Python with Tkinter and SQLite. Create projects, break them into tasks, set optional deadlines and track completion without an account or external service.

The project is evolving into a weekly execution planner: assign work to a day, estimate effort, identify prerequisite tasks and compare the week's planned workload with available hours.

## Current status

Initial working prototype, started November 1, 2026. No established user base or long-term usage is claimed. The interface is in Brazilian Portuguese.

Implemented: project creation and editing, multiline descriptions, tasks and checklists, deadlines, percentage progress, effort estimates, dependencies, weekly planning, in-app alerts, optional Windows reminders, local storage and versioned backup/restore. Project archiving, project deletion and selective import/export are not implemented yet.

## Run

Install Python 3.10 or newer including Tcl/Tk (included in the standard Windows Python installer), then run from this folder:

```sh
python app.py
```

No third-party Python packages, API keys or internet connection are required. On Windows the default database is `%LOCALAPPDATA%/PlanoLocal/planner.sqlite3`; on other systems it is `~/.local/share/PlanoLocal/planner.sqlite3`.

To choose a different database:

```sh
python app.py --data ./work/demo.sqlite3
```

Choose **Novo projeto**, enter a name and objective, then choose **Nova tarefa**. Deadlines use `YYYY-MM-DD`. Double-click a task to edit its name, deadline or status. Completed tasks appear after pending tasks.

Choose **Editar projeto / descrição** to update a project's name and multiline description. Existing objectives are preserved as descriptions.

Choose **Agenda e alertas** to see unfinished tasks with deadlines across all projects. In-app alerts include overdue tasks and deadlines today or tomorrow, using the computer's local date. A banner and system bell signal these deadlines at startup and while the application is open; checks run every minute and after saves. Sound depends on system settings. Optional closed-app Windows reminders are described below; they are not enabled automatically on startup.

Project completion is completed tasks divided by all tasks, shown as a rounded whole percentage. All tasks have equal weight; in-progress tasks do not receive partial credit. Empty projects show 0%. Adding or reopening tasks can reduce the percentage.

## Weekly execution planning

1. Select a task and choose **Planejar tarefa**.
2. Enter optional estimated hours (for example `1.5` or `1,5`) and an execution date (`YYYY-MM-DD`). This is separate from the delivery deadline.
3. Optionally select one prerequisite task from the same project. A blocked task cannot start or complete until its prerequisite is complete. Cycles are rejected.
4. Open **Planejar semana** and enter the total hours available across projects for the selected Monday–Sunday week.
5. Review the workload, missing estimates, blocked tasks and execution dates after deadlines. Navigate between weeks or double-click a row to replan it.

The capacity comparison includes estimated hours for both completed and pending tasks in the selected week. Completed hours are estimates, not measured time. Tasks without estimates make the workload incomplete; unscheduled work is counted separately. Capacity is a weekly total, not automatically prorated by remaining days.

The project view also shows effort-weighted completion once every task has an estimate. For example, completing a 1-hour task while a 3-hour task remains gives 25% by effort and 50% by task count. No partial credit is assigned to in-progress work.

See [weekly planning rules and acceptance steps](docs/WEEKLY_PLANNING.md). When upgrading a database containing existing tasks, the application saves a `*.pre-planning-*.sqlite3` copy next to it before adding planning fields. The copy is a migration safeguard, not a user-facing backup/restore feature. Existing tasks start with no estimate, execution date or prerequisite.

## Subtask checklists

Select a task and choose **Subtarefas**. Add steps, mark/unmark them, or remove an item after confirmation. All remaining items must be checked before the parent task can be completed. A finished parent must be reopened before adding an unchecked item or unchecking an existing item. Blocked tasks cannot execute checklist steps. Checking all items does not automatically complete the parent. Checklist items do not add separate weight to project progress or weekly effort.

## Optional Windows background reminders

Select a task and choose **Lembrete** to enter a local date and time (`YYYY-MM-DD HH:MM`). A custom reminder is sent once when that time is reached. Clearing it restores the default daily rule: after 09:00, unfinished tasks due by tomorrow qualify for a reminder. Completed tasks do not qualify.

Open **Notificações do Windows** to activate, deactivate, query the schedule or request a test notification. The background worker checks every five minutes while the user is signed in, even when the application window is closed. Windows notification settings may suppress visible popups. No administrator account or password is requested. Paths to Python, the project and the database must remain available.

**Integration status:** the owner confirmed that the test notification appeared and the scheduler status was active without errors in the normal Windows session. This is owner-reported verification; the assistant's execution environment could not access these Windows services. Timed closed-app delivery and sleep/battery behavior have not been separately confirmed. For this development computer, `Launch-Weekloom.cmd` is supplied outside the repository. See [setup, limitations and verification](docs/WINDOWS_REMINDERS.md).

## Backup and restore

Choose **Criar backup** to save a `.plano-backup` file containing projects, tasks, checklists, planning fields, weekly capacities and the reminder delivery ledger. The file is a versioned, data-only JSON snapshot and is not encrypted.

Choose **Restaurar** to inspect and restore a supported backup. The confirmation shows project/task counts and explains that this replaces all current data. Before replacement, the app saves a uniquely named `*.before-restore-*.plano-backup` recovery copy next to the live database. Invalid backups are rejected; write failures roll back the database transaction. A changed source file after preview is rejected too.

Restoring does not merge projects or install the Windows schedule. Restoring an older reminder ledger may make old reminders eligible again. Close other application windows before restoring. See [backup rules and recovery steps](docs/BACKUPS.md).

## Automated checks

```sh
python -m unittest discover -s tests -v
```

Tests cover persistence, validation, project isolation, foreign keys, ordering and rejected edits. GUI smoke checks do not replace manual accessibility and usability testing.

Tests also cover agenda filtering, reminder cutoff dates, progress recalculation and persisted project descriptions. With a working Tk display, run `python tests/gui_smoke.py` to check the agenda, alert deduplication, description editing and percentage display.

## Data boundaries

This prototype is for personal project planning. Do not enter third-party personal information, customer records, health records, financial records or credentials. The database is local and unencrypted; it is excluded from version control. No analytics or model integration is implemented.

## Development

All project documentation and development records are maintained in English. The application interface remains in Brazilian Portuguese.

Start with the [user acceptance checklist](docs/USER_ACCEPTANCE.md) to try the prototype and record feedback. See the [development log](docs/DEVELOPMENT_LOG.md) for completed checks and outstanding validation.

See [ROADMAP.md](ROADMAP.md) for proposed future work. Estimates are preliminary engineering estimates, not a commitment of paid hours. Git history should record actual work as it occurs, without backdating or manufacturing activity.

Developed with substantial AI assistance. Tobias Hopf selected the project direction, tested the application and supplied feature feedback. Code and documentation were produced with an AI coding assistant. Owner-reported checks include weekly planning, backup/restore, Windows test notification visibility and active scheduler status. Sustained use, clean-machine installation and broader usability validation remain future work.

License: MIT, see [LICENSE](LICENSE).
