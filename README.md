# Plano Local

A desktop planner for personal projects, written in Python with Tkinter and SQLite. Create projects, break them into tasks, set optional deadlines and track completion without an account or external service.

## Current status

Initial working prototype, started November 1, 2026. No established user base or long-term usage is claimed. The interface is in Brazilian Portuguese.

Implemented: project creation, task creation and editing, three task statuses, deadlines, overdue highlighting, per-project progress and persistent local storage. Project editing, deletion, backups and export are not implemented yet.

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

## Verify

```sh
python -m unittest discover -s tests -v
```

Tests cover persistence, validation, project isolation, foreign keys, ordering and rejected edits. GUI smoke checks do not replace manual accessibility and usability testing.

## Data boundaries

This prototype is for personal project planning. Do not enter third-party personal information, customer records, health records, financial records or credentials. The database is local and unencrypted; it is excluded from version control. No analytics or model integration is implemented.

## Development

All project documentation and development records are maintained in English. The application interface remains in Brazilian Portuguese.

Start with the [user acceptance checklist](docs/USER_ACCEPTANCE.md) to try the prototype and record feedback. See the [development log](docs/DEVELOPMENT_LOG.md) for completed checks and outstanding validation.

See [ROADMAP.md](ROADMAP.md) for proposed future work. Estimates are preliminary engineering estimates, not a commitment of paid hours. Git history should record actual work as it occurs, without backdating or manufacturing activity.

Developed with substantial AI assistance. The project direction was selected by Tobias Hopf; implementation and documentation were produced with an AI coding assistant. Owner review and real-use validation remain pending.

License: MIT, see [LICENSE](LICENSE).
