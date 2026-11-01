from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
