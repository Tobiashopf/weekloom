"""Local persistence for a personal project planner. Standard library only."""
from datetime import date, datetime, timedelta
from pathlib import Path
import sqlite3
import math
from uuid import uuid4
from contextlib import closing

STATUSES = ("A fazer", "Em andamento", "Concluída")


class Planner:
    def __init__(self, path):
        path = Path(path)
        self.path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id),
                title TEXT NOT NULL, due TEXT,
                status TEXT NOT NULL DEFAULT 'A fazer'
                    CHECK(status IN ('A fazer', 'Em andamento', 'Concluída'))
            );
        """)
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(tasks)")}
        if "estimate_hours" not in columns:
            if self.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]:
                backup = path.with_name(path.stem + ".pre-planning-" + uuid4().hex[:8] + ".sqlite3")
                with closing(sqlite3.connect(backup)) as target:
                    self.db.backup(target)
            with self.db:
                self.db.execute("BEGIN")
                self.db.execute("ALTER TABLE tasks ADD COLUMN estimate_hours REAL")
                self.db.execute("ALTER TABLE tasks ADD COLUMN planned_for TEXT")
                self.db.execute("ALTER TABLE tasks ADD COLUMN depends_on INTEGER REFERENCES tasks(id)")
        self.db.execute("CREATE TABLE IF NOT EXISTS weekly_capacity (week TEXT PRIMARY KEY, hours REAL NOT NULL)")
        self.db.commit()
        if "reminder_at" not in {r["name"] for r in self.db.execute("PRAGMA table_info(tasks)")}:
            if self.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]:
                with closing(sqlite3.connect(path.with_name(path.stem + ".pre-reminders-" + uuid4().hex[:8] + ".sqlite3"))) as target:
                    self.db.backup(target)
            with self.db:
                self.db.execute("BEGIN")
                self.db.execute("ALTER TABLE tasks ADD COLUMN reminder_at TEXT")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS checklist (
                id INTEGER PRIMARY KEY, task_id INTEGER NOT NULL REFERENCES tasks(id),
                title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS notification_log (
                event_key TEXT PRIMARY KEY, sent_at TEXT NOT NULL
            );
        """)

    @staticmethod
    def required(text):
        text = text.strip()
        if not text:
            raise ValueError("Preencha o nome ou título.")
        return text

    @staticmethod
    def deadline(value):
        value = value.strip()
        if not value:
            return None
        try:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError()
            return value
        except ValueError:
            raise ValueError("Use uma data válida no formato AAAA-MM-DD.") from None

    def add_project(self, name, description=""):
        with self.db:
            return self.db.execute(
                "INSERT INTO projects(name, description) VALUES (?, ?)",
                (self.required(name), description.strip()),
            ).lastrowid

    def projects(self):
        return self.db.execute("""
            SELECT p.*, COUNT(t.id) AS total,
                   COALESCE(SUM(t.status = 'Concluída'), 0) AS done
            FROM projects p LEFT JOIN tasks t ON t.project_id = p.id
            GROUP BY p.id ORDER BY p.id DESC
        """).fetchall()

    def update_project(self, project_id, name, description):
        with self.db:
            cursor = self.db.execute(
                "UPDATE projects SET name = ?, description = ? WHERE id = ?",
                (self.required(name), description.strip(), project_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Projeto não encontrado.")

    @staticmethod
    def completion(project):
        return 100 * project["done"] / project["total"] if project["total"] else 0

    def agenda(self):
        """Return all dated, unfinished tasks across projects, earliest first."""
        return self.db.execute("""
            SELECT t.*, p.name AS project_name FROM tasks t
            JOIN projects p ON p.id = t.project_id
            WHERE t.due IS NOT NULL AND t.status != 'Concluída'
            ORDER BY t.due, t.id
        """).fetchall()

    def due_soon(self, today=None):
        """Include overdue tasks and deadlines through tomorrow, inclusive."""
        today = today or date.today()
        cutoff = (today + timedelta(days=1)).isoformat()
        return [task for task in self.agenda() if task["due"] <= cutoff]

    def add_task(self, project_id, title, due=""):
        with self.db:
            return self.db.execute(
                "INSERT INTO tasks(project_id, title, due) VALUES (?, ?, ?)",
                (project_id, self.required(title), self.deadline(due)),
            ).lastrowid

    def tasks(self, project_id):
        return self.db.execute("""
            SELECT * FROM tasks WHERE project_id = ?
            ORDER BY status = 'Concluída', due IS NULL, due, id
        """, (project_id,)).fetchall()

    @staticmethod
    def hours(value):
        if value is None or str(value).strip() == "":
            return None
        try:
            result = float(str(value).replace(",", "."))
        except (ValueError, TypeError):
            raise ValueError("Informe horas como um número positivo, por exemplo 1,5.") from None
        if not math.isfinite(result) or not 0 < result <= 10000:
            raise ValueError("As horas devem ser maiores que zero e no máximo 10000.")
        return result

    def blockers(self, task_id):
        return self.db.execute("""
            SELECT parent.id, parent.title FROM tasks child
            JOIN tasks parent ON parent.id = child.depends_on
            WHERE child.id = ? AND parent.status != 'Concluída'
        """, (task_id,)).fetchall()

    def save_plan(self, task_id, estimate, planned_for, depends_on):
        """Save planning fields atomically; reject cross-project links and cycles."""
        estimate = self.hours(estimate)
        planned_for = self.deadline(planned_for)
        task = self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if task is None:
            raise ValueError("Tarefa não encontrada.")
        if depends_on is not None:
            parent = self.db.execute("SELECT * FROM tasks WHERE id = ?", (depends_on,)).fetchone()
            if parent is None or parent["project_id"] != task["project_id"]:
                raise ValueError("A dependência precisa ser uma tarefa deste projeto.")
            visited = {task_id}
            node = parent
            while node is not None:
                if node["id"] in visited:
                    raise ValueError("Essa dependência criaria um ciclo entre tarefas.")
                visited.add(node["id"])
                node = self.db.execute("SELECT * FROM tasks WHERE id = ?", (node["depends_on"],)).fetchone()
            if task["status"] != "A fazer" and parent["status"] != "Concluída":
                raise ValueError("Volte a tarefa para A fazer antes de adicionar uma dependência pendente.")
        with self.db:
            self.db.execute("UPDATE tasks SET estimate_hours = ?, planned_for = ?, depends_on = ? WHERE id = ?",
                            (estimate, planned_for, depends_on, task_id))

    @staticmethod
    def week_start(day):
        return day - timedelta(days=day.weekday())

    def set_capacity(self, day, hours):
        hours = self.hours(hours)
        if hours is None or hours > 168:
            raise ValueError("Informe uma capacidade semanal maior que zero e no máximo 168 horas.")
        with self.db:
            self.db.execute("INSERT INTO weekly_capacity(week, hours) VALUES (?, ?) ON CONFLICT(week) DO UPDATE SET hours = excluded.hours",
                            (self.week_start(day).isoformat(), hours))

    def week_plan(self, day):
        start = self.week_start(day)
        end = start + timedelta(days=6)
        tasks = self.db.execute("""
            SELECT t.*, p.name AS project_name, parent.title AS prerequisite,
                   CASE WHEN parent.id IS NOT NULL AND parent.status != 'Concluída' THEN 1 ELSE 0 END AS blocked
            FROM tasks t JOIN projects p ON p.id = t.project_id
            LEFT JOIN tasks parent ON parent.id = t.depends_on
            WHERE t.planned_for BETWEEN ? AND ? ORDER BY t.planned_for, t.id
        """, (start.isoformat(), end.isoformat())).fetchall()
        capacity = self.db.execute("SELECT hours FROM weekly_capacity WHERE week = ?", (start.isoformat(),)).fetchone()
        pending = [t for t in tasks if t["status"] != "Concluída"]
        return dict(start=start, end=end, tasks=tasks,
                    capacity=capacity[0] if capacity else None,
                    pending_hours=sum(t["estimate_hours"] or 0 for t in pending),
                    missing_estimates=sum(t["estimate_hours"] is None for t in tasks),
                    completed_hours=sum(t["estimate_hours"] or 0 for t in tasks if t["status"] == "Concluída"),
                    blocked=sum(t["blocked"] for t in pending),
                    late_plans=sum(bool(t["due"] and t["planned_for"] > t["due"]) for t in pending),
                    unscheduled=self.db.execute("SELECT COUNT(*) FROM tasks WHERE planned_for IS NULL AND status != 'Concluída'").fetchone()[0])

    def effort_progress(self, project_id):
        tasks = self.tasks(project_id)
        if not tasks or any(t["estimate_hours"] is None for t in tasks):
            return None
        total = sum(t["estimate_hours"] for t in tasks)
        return 100 * sum(t["estimate_hours"] for t in tasks if t["status"] == "Concluída") / total

    def update_task(self, task_id, title, due, status):
        if status not in STATUSES:
            raise ValueError("Status inválido.")
        if status == "Concluída" and any(not item["done"] for item in self.checklist(task_id)):
            raise ValueError("Conclua todas as subtarefas antes de concluir a tarefa.")
        if status != "A fazer" and self.blockers(task_id):
            raise ValueError("Conclua a tarefa anterior antes de iniciar ou concluir esta tarefa.")
        if status != "Concluída" and self.db.execute(
                "SELECT 1 FROM tasks WHERE depends_on = ? AND status != 'A fazer'", (task_id,)).fetchone():
            raise ValueError("Volte as tarefas dependentes para A fazer antes de reabrir esta tarefa.")
        with self.db:
            cursor = self.db.execute(
                "UPDATE tasks SET title = ?, due = ?, status = ? WHERE id = ?",
                (self.required(title), self.deadline(due), status, task_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Tarefa não encontrada.")

    def checklist(self, task_id):
        return self.db.execute("SELECT * FROM checklist WHERE task_id = ? ORDER BY id", (task_id,)).fetchall()

    def add_checklist_item(self, task_id, title):
        task = self.db.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if task is None or task["status"] == "Concluída":
            raise ValueError("Selecione uma tarefa pendente; reabra tarefas concluídas antes de adicionar subtarefas.")
        with self.db:
            return self.db.execute("INSERT INTO checklist(task_id, title) VALUES (?, ?)", (task_id, self.required(title))).lastrowid

    def set_checklist_item(self, item_id, done):
        item = self.db.execute("SELECT c.*, t.status FROM checklist c JOIN tasks t ON t.id = c.task_id WHERE c.id = ?", (item_id,)).fetchone()
        if item is None:
            raise ValueError("Subtarefa não encontrada.")
        if not done and item["status"] == "Concluída":
            raise ValueError("Reabra a tarefa antes de desmarcar uma subtarefa.")
        if done and self.blockers(item["task_id"]):
            raise ValueError("Conclua a dependência antes de executar esta subtarefa.")
        with self.db:
            self.db.execute("UPDATE checklist SET done = ? WHERE id = ?", (int(bool(done)), item_id))

    def delete_checklist_item(self, item_id):
        with self.db:
            self.db.execute("DELETE FROM checklist WHERE id = ?", (item_id,))

    def set_reminder(self, task_id, value):
        value = value.strip()
        if value:
            try:
                parsed = datetime.strptime(value, "%Y-%m-%d %H:%M")
                if parsed.strftime("%Y-%m-%d %H:%M") != value:
                    raise ValueError()
            except ValueError:
                raise ValueError("Use uma data e hora válidas: AAAA-MM-DD HH:MM.") from None
        with self.db:
            cursor = self.db.execute("UPDATE tasks SET reminder_at = ? WHERE id = ?", (value or None, task_id))
            if cursor.rowcount != 1:
                raise ValueError("Tarefa não encontrada.")

    def pending_notifications(self, now=None):
        """Return unsent local-time events; custom reminders fire once, defaults daily after 09:00."""
        now = now or datetime.now()
        sent = {row[0] for row in self.db.execute("SELECT event_key FROM notification_log")}
        events = []
        for task in self.db.execute("SELECT * FROM tasks WHERE status != 'Concluída'"):
            if task["reminder_at"]:
                if datetime.strptime(task["reminder_at"], "%Y-%m-%d %H:%M") > now:
                    continue
                key = f'{task["id"]}:custom:{task["reminder_at"]}'
            else:
                if now.hour < 9 or not task["due"] or task["due"] > (now.date() + timedelta(days=1)).isoformat():
                    continue
                key = f'{task["id"]}:due:{task["due"]}:{now.date().isoformat()}'
            if key not in sent:
                events.append(key)
        return events

    def record_notifications(self, events, now=None):
        with self.db:
            self.db.executemany("INSERT OR IGNORE INTO notification_log VALUES (?, ?)",
                                [(key, (now or datetime.now()).isoformat()) for key in events])

    def close(self):
        self.db.close()
