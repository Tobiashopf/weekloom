"""Backup round trips, validation failures and restore rollback guarantees."""
import copy
from datetime import date
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from planner import Planner
from backups import create_backup, read_backup, restore_backup, snapshot


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.store = Planner(self.folder / "live.sqlite3")
        self.project = self.store.add_project("Personal project", "Two lines\nwith Unicode: ação")
        self.first = self.store.add_task(self.project, "First", "2026-11-03")
        self.second = self.store.add_task(self.project, "Second", "2026-11-04")
        self.store.save_plan(self.second, "2,5", "2026-11-03", self.first)
        self.store.add_checklist_item(self.second, "Step")
        self.store.set_capacity(date(2026, 11, 2), "8")
        self.store.set_reminder(self.second, "2026-11-03 10:00")
        self.store.record_notifications(["test-event"])
        self.backup = self.folder / "saved.plano-backup"

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def tables(self):
        return snapshot(self.store)["tables"]

    def test_roundtrip_restores_every_table_and_saves_previous_state(self):
        original = self.tables()
        create_backup(self.store, self.backup)
        self.store.add_project("Added afterward")
        previous = self.tables()
        safety = restore_backup(self.store, self.backup)
        self.assertEqual(self.tables(), original)
        self.assertEqual(read_backup(safety)["tables"], previous)
        self.store.close()
        self.store = Planner(self.folder / "live.sqlite3")
        self.assertEqual(self.tables(), original)
        self.assertEqual(self.store.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_invalid_files_and_invariants_preserve_live_data(self):
        create_backup(self.store, self.backup)
        payload = read_backup(self.backup)
        original = self.tables()
        variants = []
        for change in (
            lambda p: p.update(backup_version=999),
            lambda p: p["tables"]["tasks"][0].update(project_id=999),
            lambda p: p["tables"]["tasks"][0].update(due="2026-02-30"),
            lambda p: p["tables"]["tasks"][0].update(depends_on=self.second),
            lambda p: p["tables"]["tasks"][1].update(status="Concluída"),
            lambda p: p["tables"]["tasks"][0].update(estimate_hours=float("inf")),
            lambda p: p["tables"]["projects"].append(p["tables"]["projects"][0].copy()),
        ):
            variant = copy.deepcopy(payload)
            change(variant)
            variants.append(json.dumps(variant))
        variants.extend(["not a backup", "{", "[]"])
        for content in variants:
            self.backup.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                restore_backup(self.store, self.backup)
            self.assertEqual(self.tables(), original)
        self.assertEqual(list(self.folder.glob("*.before-restore-*")), [])

    def test_failure_mid_restore_rolls_back_and_preserves_safety_copy(self):
        create_backup(self.store, self.backup)
        self.store.add_project("Keep on failure")
        before = self.tables()
        def fail(connection, payload):
            connection.execute("DELETE FROM notification_log")
            raise sqlite3.OperationalError("Simulated write failure")
        with patch("backups.replace_rows", side_effect=fail):
            with self.assertRaises(sqlite3.OperationalError):
                restore_backup(self.store, self.backup)
        self.assertEqual(self.tables(), before)
        safety = list(self.folder.glob("*.before-restore-*.plano-backup"))
        self.assertEqual(len(safety), 1)
        self.assertEqual(read_backup(safety[0])["tables"], before)

    def test_unwritable_safety_copy_prevents_restore(self):
        create_backup(self.store, self.backup)
        self.store.add_project("Must stay")
        before = self.tables()
        with patch("backups.write_file", side_effect=OSError("Disk full")):
            with self.assertRaises(OSError):
                restore_backup(self.store, self.backup)
        self.assertEqual(self.tables(), before)

    def test_backup_refuses_live_database_and_wrong_extension(self):
        for path in (self.store.path, self.folder / "notes.txt"):
            with self.assertRaises(ValueError):
                create_backup(self.store, path)
        self.assertEqual(len(self.store.projects()), 1)

    def test_changed_file_after_confirmation_is_rejected(self):
        create_backup(self.store, self.backup)
        expected = read_backup(self.backup)
        self.store.add_project("New state")
        create_backup(self.store, self.backup)
        before = self.tables()
        with self.assertRaises(ValueError):
            restore_backup(self.store, self.backup, expected=expected)
        self.assertEqual(self.tables(), before)

    def test_atomic_backup_keeps_previous_file_when_publication_fails(self):
        create_backup(self.store, self.backup)
        previous = self.backup.read_bytes()
        self.store.add_project("Extra")
        with patch("backups.os.replace", side_effect=OSError("Publication failed")):
            with self.assertRaises(OSError):
                create_backup(self.store, self.backup)
        self.assertEqual(self.backup.read_bytes(), previous)
        self.assertEqual(list(self.folder.glob(".plano-backup-*")), [])


if __name__ == "__main__":
    unittest.main()
