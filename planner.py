"""Local persistence for a personal project planner. Standard library only."""
from datetime import date
from pathlib import Path
import sqlite3

STATUSES = ("A fazer", "Em andamento", "Concluída")


class Planner:
    def __init__(self, path):
        path = Path(path)
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

    def update_task(self, task_id, title, due, status):
        if status not in STATUSES:
            raise ValueError("Status inválido.")
        with self.db:
            cursor = self.db.execute(
                "UPDATE tasks SET title = ?, due = ?, status = ? WHERE id = ?",
                (self.required(title), self.deadline(due), status, task_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Tarefa não encontrada.")

    def close(self):
        self.db.close()
