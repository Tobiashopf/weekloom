from pathlib import Path
from datetime import date
import sqlite3
import tempfile
import unittest
from planner import Planner


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "planner.sqlite3"
        self.store = Planner(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_persistence_and_progress(self):
        project = self.store.add_project("Meu projeto", "Objetivo")
        task = self.store.add_task(project, "Primeiro passo")
        self.store.update_task(task, "Primeiro passo", "2026-12-01", "Concluída")
        self.store.close()
        self.store = Planner(self.path)
        row = self.store.projects()[0]
        self.assertEqual((row["total"], row["done"]), (1, 1))
        self.assertEqual(self.store.tasks(project)[0]["due"], "2026-12-01")

    def test_invalid_input_does_not_create_records(self):
        with self.assertRaises(ValueError):
            self.store.add_project("   ")
        project = self.store.add_project("Projeto")
        for invalid in ("2026-02-30", "01/12/2026", "20261201"):
            with self.assertRaises(ValueError):
                self.store.add_task(project, "Tarefa", invalid)
        self.assertEqual(len(self.store.tasks(project)), 0)

    def test_project_isolation_and_foreign_keys(self):
        first, second = self.store.add_project("A"), self.store.add_project("B")
        self.store.add_task(first, "Só no A")
        self.assertEqual(self.store.tasks(second), [])
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.add_task(99999, "Órfã")

    def test_pending_deadlines_before_done(self):
        project = self.store.add_project("A")
        done = self.store.add_task(project, "Finalizada", "2026-01-01")
        self.store.update_task(done, "Finalizada", "2026-01-01", "Concluída")
        self.store.add_task(project, "Sem prazo")
        self.store.add_task(project, "Mais tarde", "2026-12-02")
        self.store.add_task(project, "Primeira", "2026-12-01")
        self.assertEqual([t["title"] for t in self.store.tasks(project)], ["Primeira", "Mais tarde", "Sem prazo", "Finalizada"])

    def test_rejected_edit_preserves_task(self):
        project = self.store.add_project("A")
        task = self.store.add_task(project, "Original")
        with self.assertRaises(ValueError):
            self.store.update_task(task, "Mudou", "", "Inválido")
        self.assertEqual(self.store.tasks(project)[0]["title"], "Original")

    def test_agenda_and_reminders_include_only_due_pending_tasks(self):
        first = self.store.add_project("A")
        second = self.store.add_project("B")
        for title, due in (("Overdue", "2026-10-31"), ("Today", "2026-11-01"),
                           ("Tomorrow", "2026-11-02"), ("Later", "2026-11-03"),
                           ("Undated", "")):
            self.store.add_task(first, title, due)
        completed = self.store.add_task(second, "Done", "2026-10-30")
        self.store.update_task(completed, "Done", "2026-10-30", "Concluída")
        self.store.add_task(second, "Another project", "2026-11-02")
        self.assertEqual([t["title"] for t in self.store.due_soon(date(2026, 11, 1))],
                         ["Overdue", "Today", "Tomorrow", "Another project"])
        self.assertEqual(len(self.store.agenda()), 5)
        self.assertEqual(self.store.agenda()[3]["project_name"], "B")

    def test_progress_recalculates_when_tasks_reopen_or_are_added(self):
        project = self.store.add_project("A")
        self.assertEqual(self.store.completion(self.store.projects()[0]), 0)
        task = self.store.add_task(project, "First")
        self.store.update_task(task, "First", "", "Concluída")
        self.assertEqual(self.store.completion(self.store.projects()[0]), 100)
        self.store.add_task(project, "Second")
        self.assertEqual(self.store.completion(self.store.projects()[0]), 50)
        self.store.update_task(task, "First", "", "Em andamento")
        self.assertEqual(self.store.completion(self.store.projects()[0]), 0)

    def test_project_description_edit_persists_and_preserves_tasks(self):
        project = self.store.add_project("Before", "Old description")
        self.store.add_task(project, "Keep me")
        self.store.update_project(project, "After", "First line\nSecond line")
        with self.assertRaises(ValueError):
            self.store.update_project(project, "  ", "Should not save")
        self.store.close()
        self.store = Planner(self.path)
        row = self.store.projects()[0]
        self.assertEqual(row["name"], "After")
        self.assertEqual(row["description"], "First line\nSecond line")
        self.assertEqual(row["total"], 1)

    def test_reminder_cutoff_crosses_year_boundary(self):
        project = self.store.add_project("A")
        self.store.add_task(project, "New year", "2027-01-01")
        self.assertEqual(len(self.store.due_soon(date(2026, 12, 31))), 1)
        self.assertEqual(len(self.store.due_soon(date(2026, 12, 30))), 0)


if __name__ == "__main__":
    unittest.main()
