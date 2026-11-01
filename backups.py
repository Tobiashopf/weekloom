"""Versioned data-only backups and transactional restore of trusted schema."""
from datetime import date, datetime
import json
import math
import os
from pathlib import Path
import tempfile
from uuid import uuid4

TABLES = {
    "projects": ("id", "name", "description"),
    "tasks": ("id", "project_id", "title", "due", "status", "estimate_hours", "planned_for", "depends_on", "reminder_at"),
    "weekly_capacity": ("week", "hours"),
    "checklist": ("id", "task_id", "title", "done"),
    "notification_log": ("event_key", "sent_at"),
}


def snapshot(store):
    return {"application": "Weekloom", "backup_version": 1,
            "created_at": datetime.now().isoformat(),
            "tables": {table: [dict(zip(columns, row)) for row in store.db.execute(
                f"SELECT {','.join(columns)} FROM {table}")]
                       for table, columns in TABLES.items()}}


def write_file(path, payload):
    """Publish a complete file atomically, never leave a partial backup."""
    path = Path(path).resolve()
    descriptor, temporary = tempfile.mkstemp(prefix=".plano-backup-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def create_backup(store, destination):
    path = Path(destination).resolve()
    if path == store.path or (path.exists() and os.path.samefile(path, store.path)):
        raise ValueError("Escolha outro arquivo; o banco de dados em uso não pode ser sobrescrito.")
    if path.suffix != ".plano-backup":
        raise ValueError("Use a extensão .plano-backup para o arquivo de backup.")
    store.db.execute("BEGIN")
    try:
        payload = snapshot(store)
    finally:
        store.db.rollback()
    return write_file(path, payload)


def reject():
    raise ValueError("Backup inválido ou incompatível. Os dados atuais não foram alterados.")


def valid_date(value):
    if value is None:
        return
    if not isinstance(value, str):
        reject()
    try:
        if date.fromisoformat(value).isoformat() != value:
            reject()
    except ValueError:
        reject()


def validate(payload):
    """Validate types, relationships and domain invariants before touching live data."""
    if not isinstance(payload, dict) or payload.get("application") not in ("Weekloom", "Plano Local") or type(payload.get("backup_version")) is not int or payload["backup_version"] != 1:
        reject()
    tables = payload.get("tables")
    if not isinstance(tables, dict) or set(tables) != set(TABLES):
        reject()
    for table, columns in TABLES.items():
        rows = tables[table]
        if not isinstance(rows, list):
            reject()
        for row in rows:
            if not isinstance(row, dict) or set(row) != set(columns):
                reject()
            for key, value in row.items():
                if key in ("id", "project_id", "task_id", "depends_on"):
                    if key == "depends_on" and value is None:
                        continue
                    if type(value) is not int or value <= 0:
                        reject()
                elif key in ("estimate_hours", "hours"):
                    if key == "estimate_hours" and value is None:
                        continue
                    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= (168 if key == "hours" else 10000):
                        reject()
                elif key == "done":
                    if type(value) is not int or value not in (0, 1):
                        reject()
                elif key in ("due", "planned_for", "reminder_at") and value is None:
                    continue
                elif not isinstance(value, str):
                    reject()
            if table in ("tasks", "projects", "checklist"):
                if not row["name" if table == "projects" else "title"].strip():
                    reject()
    projects = {row["id"] for row in tables["projects"]}
    tasks = {row["id"]: row for row in tables["tasks"]}
    if len(projects) != len(tables["projects"]) or len(tasks) != len(tables["tasks"]):
        reject()
    for task in tasks.values():
        if task["project_id"] not in projects or task["status"] not in ("A fazer", "Em andamento", "Concluída"):
            reject()
        valid_date(task["due"])
        valid_date(task["planned_for"])
        if task["reminder_at"] is not None:
            try:
                if datetime.strptime(task["reminder_at"], "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M") != task["reminder_at"]:
                    reject()
            except ValueError:
                reject()
        parent = task["depends_on"]
        if parent is not None:
            if parent not in tasks or tasks[parent]["project_id"] != task["project_id"]:
                reject()
            if task["status"] != "A fazer" and tasks[parent]["status"] != "Concluída":
                reject()
        seen = set()
        current = task["id"]
        while current is not None:
            if current in seen or current not in tasks:
                reject()
            seen.add(current)
            current = tasks[current]["depends_on"]
    for item in tables["checklist"]:
        if item["task_id"] not in tasks or (tasks[item["task_id"]]["status"] == "Concluída" and not item["done"]):
            reject()
    for capacity in tables["weekly_capacity"]:
        valid_date(capacity["week"])
        if date.fromisoformat(capacity["week"]).weekday() != 0:
            reject()
    for record in tables["notification_log"]:
        try:
            datetime.fromisoformat(record["sent_at"])
        except ValueError:
            reject()
    for table, key in (("checklist", "id"), ("weekly_capacity", "week"), ("notification_log", "event_key")):
        if len({r[key] for r in tables[table]}) != len(tables[table]):
            reject()
    return payload


def read_backup(source):
    try:
        with open(source, encoding="utf-8") as stream:
            return validate(json.load(stream))
    except (json.JSONDecodeError, UnicodeError, TypeError, KeyError, OverflowError):
        reject()


def replace_rows(connection, payload):
    connection.execute("PRAGMA defer_foreign_keys = ON")
    for table in reversed(TABLES):
        connection.execute(f"DELETE FROM {table}")
    for table, columns in TABLES.items():
        connection.executemany(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [tuple(row[column] for column in columns) for row in payload["tables"][table]],
        )
    if connection.execute("PRAGMA foreign_key_check").fetchone():
        reject()


def restore_backup(store, source, expected=None):
    payload = read_backup(source)
    if expected is not None and payload != expected:
        raise ValueError("O backup mudou depois da conferência. Selecione o arquivo novamente.")
    safety = store.path.with_name(store.path.stem + ".before-restore-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:8] + ".plano-backup")
    store.db.execute("BEGIN IMMEDIATE")
    try:
        write_file(safety, snapshot(store))
        replace_rows(store.db, payload)
        store.db.commit()
    except Exception:
        store.db.rollback()
        raise
    return safety
