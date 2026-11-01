"""Checklist invariants and reminder delivery behavior, without native popups."""
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from planner import Planner
from notifications import run
from reminder_setup import task_xml, task_name


class ChecklistReminderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "planner.sqlite3"
        self.store = Planner(self.path)
        self.project = self.store.add_project("Example")
        self.task = self.store.add_task(self.project, "Task", "2026-11-02")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_checklist_completion_and_reopening_rules(self):
        item = self.store.add_checklist_item(self.task, "Step one")
        with self.assertRaises(ValueError):
            self.store.update_task(self.task, "Task", "", "Concluída")
        self.store.set_checklist_item(item, True)
        self.store.update_task(self.task, "Task", "", "Concluída")
        with self.assertRaises(ValueError):
            self.store.set_checklist_item(item, False)
        with self.assertRaises(ValueError):
            self.store.add_checklist_item(self.task, "Another")
        self.store.update_task(self.task, "Task", "", "A fazer")
        self.store.set_checklist_item(item, False)
        self.store.close()
        self.store = Planner(self.path)
        self.assertEqual(self.store.checklist(self.task)[0]["done"], 0)
        self.store.delete_checklist_item(item)
        self.assertEqual(self.store.checklist(self.task), [])

    def test_blocked_task_cannot_complete_checklist(self):
        parent = self.store.add_task(self.project, "Prerequisite")
        self.store.save_plan(self.task, "", "", parent)
        item = self.store.add_checklist_item(self.task, "Step")
        with self.assertRaises(ValueError):
            self.store.set_checklist_item(item, True)

    def test_daily_cutoff_and_persistent_deduplication(self):
        self.assertEqual(self.store.pending_notifications(datetime(2026, 11, 1, 8, 59)), [])
        now = datetime(2026, 11, 1, 9)
        events = self.store.pending_notifications(now)
        self.assertEqual(len(events), 1)
        self.store.record_notifications(events, now)
        self.store.close()
        self.store = Planner(self.path)
        self.assertEqual(self.store.pending_notifications(now), [])
        self.assertEqual(len(self.store.pending_notifications(datetime(2026, 11, 2, 9))), 1)

    def test_custom_reminders_override_defaults_and_rescheduling_changes_event(self):
        self.store.set_reminder(self.task, "2026-11-01 14:30")
        self.assertEqual(self.store.pending_notifications(datetime(2026, 11, 1, 14, 29)), [])
        events = self.store.pending_notifications(datetime(2026, 11, 1, 14, 30))
        self.assertEqual(len(events), 1)
        self.store.record_notifications(events)
        self.assertEqual(self.store.pending_notifications(datetime(2026, 11, 3, 12)), [])
        self.store.set_reminder(self.task, "2026-11-02 14:30")
        self.assertEqual(len(self.store.pending_notifications(datetime(2026, 11, 3, 12))), 1)
        self.store.update_task(self.task, "Task", "2026-11-02", "Concluída")
        self.assertEqual(self.store.pending_notifications(datetime(2026, 11, 3, 12)), [])

    def test_invalid_reminder_preserves_previous_value(self):
        self.store.set_reminder(self.task, "2026-11-01 14:30")
        for value in ("2026-02-30 10:00", "2026-11-01 25:00", "tomorrow", "2026-1-1 9:00"):
            with self.assertRaises(ValueError):
                self.store.set_reminder(self.task, value)
        self.assertEqual(self.store.tasks(self.project)[0]["reminder_at"], "2026-11-01 14:30")

    def test_failed_delivery_is_retried_and_success_is_recorded(self):
        self.store.set_reminder(self.task, "2000-01-01 09:00")
        def fail(count):
            raise RuntimeError("Notification unavailable")
        with self.assertRaises(RuntimeError):
            run(self.path, fail)
        delivered = []
        self.assertEqual(run(self.path, delivered.append), 1)
        self.assertEqual(run(self.path, delivered.append), 0)
        self.assertEqual(delivered, [1])

    def test_worker_does_not_create_missing_database(self):
        missing = Path(self.temp.name) / "missing.sqlite3"
        with self.assertRaises(ValueError):
            run(missing, lambda count: None)
        self.assertFalse(missing.exists())

    def test_scheduler_xml_handles_long_paths_and_uses_interactive_low_privilege(self):
        runtime = Path(self.temp.name) / "runtime with spaces & symbols"
        runtime.mkdir()
        (runtime / "pythonw.exe").touch()
        xml = ET.fromstring(task_xml(self.path, runtime / "python.exe", "S-1-5-21-123"))
        ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
        self.assertEqual(xml.find(".//t:LogonType", ns).text, "InteractiveToken")
        self.assertEqual(xml.find(".//t:RunLevel", ns).text, "LeastPrivilege")
        self.assertEqual(xml.find(".//t:Interval", ns).text, "PT5M")
        self.assertEqual(xml.find(".//t:Command", ns).text, str((runtime / "pythonw.exe").resolve()))
        self.assertIn(str(self.path), xml.find(".//t:Arguments", ns).text)
        self.assertNotEqual(task_name(self.path), task_name(self.path.with_name("other.sqlite3")))


if __name__ == "__main__":
    unittest.main()
