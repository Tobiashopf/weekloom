"""Behavioral checks for planning, dependencies and legacy data upgrades."""
from datetime import date
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing
from planner import Planner


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "planner.sqlite3"
        self.store = Planner(self.path)
        self.project = self.store.add_project("Personal project", "Keep this description")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def task(self, title="Task"):
        return self.store.add_task(self.project, title)

    def test_dependency_blocks_start_and_completion_then_unlocks(self):
        first, second = self.task("First"), self.task("Second")
        self.store.save_plan(second, "2", "2026-11-02", first)
        for status in ("Em andamento", "Concluída"):
            with self.assertRaises(ValueError):
                self.store.update_task(second, "Second", "", status)
        self.store.update_task(first, "First", "", "Concluída")
        self.store.update_task(second, "Second", "", "Em andamento")
        with self.assertRaises(ValueError):
            self.store.update_task(first, "First", "", "A fazer")
        self.store.update_task(second, "Second", "", "A fazer")
        self.store.update_task(first, "First", "", "A fazer")
        self.assertEqual(len(self.store.blockers(second)), 1)

    def test_cycles_and_cross_project_links_are_rejected_without_partial_save(self):
        a, b, c = self.task("A"), self.task("B"), self.task("C")
        self.store.save_plan(b, "1", "", a)
        self.store.save_plan(c, "1", "", b)
        other = self.store.add_task(self.store.add_project("Other"), "External")
        for dependency in (a, c, other, 9999):
            with self.assertRaises(ValueError):
                self.store.save_plan(a, "99", "2026-11-03", dependency)
        row = next(t for t in self.store.tasks(self.project) if t["id"] == a)
        self.assertIsNone(row["estimate_hours"])
        self.assertIsNone(row["depends_on"])

    def test_invalid_estimates_and_dates_preserve_existing_plan(self):
        task = self.task()
        self.store.save_plan(task, "1,5", "2026-11-02", None)
        for invalid in ("-1", "0", "nan", "inf", "10001", "abc"):
            with self.assertRaises(ValueError):
                self.store.save_plan(task, invalid, "", None)
        with self.assertRaises(ValueError):
            self.store.save_plan(task, "2", "2026-02-30", None)
        self.assertEqual(self.store.tasks(self.project)[0]["estimate_hours"], 1.5)

    def test_week_boundaries_capacity_and_unknown_work(self):
        sunday, monday, next_week, unknown, blocked = [self.task(str(i)) for i in range(5)]
        self.store.save_plan(sunday, "2", "2026-11-01", None)
        self.store.save_plan(monday, "3", "2026-11-02", None)
        self.store.save_plan(next_week, "4", "2026-11-09", None)
        self.store.save_plan(unknown, "", "2026-11-08", None)
        self.store.save_plan(blocked, "2", "2026-11-03", monday)
        self.store.update_task(blocked, "Risk", "2026-11-02", "A fazer")
        self.task("Unscheduled")
        self.store.set_capacity(date(2026, 11, 8), "4")
        plan = self.store.week_plan(date(2026, 11, 4))
        self.assertEqual((plan["start"], plan["end"]), (date(2026, 11, 2), date(2026, 11, 8)))
        self.assertEqual(len(plan["tasks"]), 3)
        self.assertEqual((plan["capacity"], plan["pending_hours"], plan["missing_estimates"]), (4, 5, 1))
        self.assertEqual((plan["blocked"], plan["late_plans"], plan["unscheduled"]), (1, 1, 1))
        self.assertIsNone(self.store.week_plan(date(2026, 11, 9))["capacity"])
        self.store.update_task(monday, "Done", "", "Concluída")
        plan = self.store.week_plan(date(2026, 11, 4))
        self.assertEqual((plan["completed_hours"], plan["pending_hours"], plan["blocked"]), (3, 2, 0))

    def test_effort_progress_requires_complete_estimates(self):
        a, b = self.task("A"), self.task("B")
        self.store.save_plan(a, "1", "", None)
        self.store.update_task(a, "A", "", "Concluída")
        self.assertIsNone(self.store.effort_progress(self.project))
        self.store.save_plan(b, "3", "", None)
        self.assertEqual(self.store.effort_progress(self.project), 25)
        self.assertEqual(self.store.completion(self.store.projects()[0]), 50)

    def test_plan_and_capacity_survive_reopening(self):
        a, b = self.task("A"), self.task("B")
        self.store.save_plan(b, "2", "2026-11-02", a)
        self.store.set_capacity(date(2026, 11, 2), "10")
        self.store.close()
        self.store = Planner(self.path)
        plan = self.store.week_plan(date(2026, 11, 2))
        self.assertEqual((plan["capacity"], plan["blocked"], plan["pending_hours"]), (10, 1, 2))

    def test_legacy_database_is_preserved_and_backed_up_once(self):
        legacy = Path(self.temp.name) / "legacy.sqlite3"
        with closing(sqlite3.connect(legacy)) as connection:
            connection.executescript("""
                CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '');
                CREATE TABLE tasks (id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id), title TEXT NOT NULL, due TEXT, status TEXT NOT NULL DEFAULT 'A fazer');
                INSERT INTO projects VALUES (1, 'Existing', 'Original description');
                INSERT INTO tasks VALUES (1, 1, 'Existing task', '2026-12-01', 'Concluída');
            """)
        upgraded = Planner(legacy)
        try:
            self.assertEqual(upgraded.projects()[0]["description"], "Original description")
            self.assertEqual(upgraded.tasks(1)[0]["status"], "Concluída")
            self.assertIsNone(upgraded.tasks(1)[0]["estimate_hours"])
        finally:
            upgraded.close()
        reopened = Planner(legacy)
        reopened.close()
        backups = list(Path(self.temp.name).glob("legacy.pre-planning-*.sqlite3"))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as connection:
            self.assertEqual(connection.execute("SELECT title FROM tasks").fetchone()[0], "Existing task")
            self.assertNotIn("estimate_hours", [r[1] for r in connection.execute("PRAGMA table_info(tasks)")])


if __name__ == "__main__":
    unittest.main()
