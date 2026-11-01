"""Run explicitly on a computer with a working Tk display: python tests/gui_smoke.py."""
from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile
import tkinter as tk
from unittest.mock import patch
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import App
from planner import Planner


with tempfile.TemporaryDirectory() as temp:
    store = Planner(Path(temp) / "test.sqlite3")
    root = tk.Tk()
    root.withdraw()
    try:
        project = store.add_project("Example", "Original")
        task = store.add_task(project, "Due tomorrow", (date.today() + timedelta(days=1)).isoformat())
        store.add_task(project, "No deadline")
        bells = []
        root.bell = lambda: bells.append(True)
        app = App(root, store)
        app.projects.selection_set(str(project))
        app.select_project()
        root.update()
        assert "0%" in app.summary.cget("text")
        assert len(bells) == 1
        app.check_reminders()
        assert len(bells) == 1, "Repeated polling must not repeat the same alert"
        app.open_agenda()
        root.update()
        assert len(app.agenda_tree.get_children()) == 1
        app.edit_project()
        root.update()
        dialog = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel) and w != app.agenda_window][0]
        body = dialog.winfo_children()[0]
        description = next(w for w in body.winfo_children() if isinstance(w, tk.Text))
        description.delete("1.0", "end")
        description.insert("1.0", "Updated description\nSecond line")
        next(w for w in body.winfo_children() if isinstance(w, ttk.Button)).invoke()
        root.update()
        assert "Updated description" in app.description.cget("text")
        store.update_task(task, "Due tomorrow", (date.today() + timedelta(days=1)).isoformat(), "Concluída")
        app.refresh_tasks()
        app.check_reminders()
        assert "50%" in app.summary.cget("text")
        assert len(app.agenda_tree.get_children()) == 0
        assert "Nenhum prazo" in app.reminder.cget("text")
        app.tasks.selection_set(str(task))
        app.plan_task()
        root.update()
        dialog = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel) and w != app.agenda_window][0]
        body = dialog.winfo_children()[0]
        entries = [w for w in body.winfo_children() if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
        entries[0].insert(0, "3")
        entries[1].insert(0, date.today().isoformat())
        next(w for w in body.winfo_children() if isinstance(w, ttk.Button)).invoke()
        root.update()
        app.open_week()
        app.capacity_var.set("2")
        app.save_capacity()
        root.update()
        assert len(app.week_tree.get_children()) == 1
        assert "Excesso estimado: 1 h" in app.week_summary.cget("text")
        app.move_week(7)
        assert len(app.week_tree.get_children()) == 0
        app.move_week(None)
        assert len(app.week_tree.get_children()) == 1
        assert app.capacity_var.get() == "2"
        checklist_task = store.add_task(project, "Checklist task")
        app.refresh_tasks()
        app.tasks.selection_set(str(checklist_task))
        app.open_checklist()
        root.update()
        checklist_window = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel) and w.title() == "Subtarefas")
        body = checklist_window.winfo_children()[0]
        entry = next(w for w in body.winfo_children() if isinstance(w, ttk.Entry))
        entry.insert(0, "Example step")
        controls = next(w for w in body.winfo_children() if isinstance(w, ttk.Frame))
        next(w for w in controls.winfo_children() if w.cget("text") == "Adicionar").invoke()
        tree = next(w for w in body.winfo_children() if isinstance(w, ttk.Treeview))
        assert len(tree.get_children()) == 1
        tree.selection_set(tree.get_children()[0])
        next(w for w in controls.winfo_children() if w.cget("text") == "Marcar / desmarcar").invoke()
        assert store.checklist(checklist_task)[0]["done"] == 1
        checklist_window.destroy()
        app.configure_reminder()
        root.update()
        dialog = next(w for w in root.winfo_children() if isinstance(w, tk.Toplevel) and w.title() == "Lembrete personalizado")
        body = dialog.winfo_children()[0]
        next(w for w in body.winfo_children() if isinstance(w, ttk.Entry)).insert(0, "2030-01-01 10:30")
        next(w for w in body.winfo_children() if isinstance(w, ttk.Button)).invoke()
        assert next(t for t in store.tasks(project) if t["id"] == checklist_task)["reminder_at"] == "2030-01-01 10:30"
        backup = Path(temp) / "gui.plano-backup"
        with patch("app.filedialog.asksaveasfilename", return_value=str(backup)), patch("app.messagebox.showinfo"):
            app.create_backup()
        assert backup.exists()
        store.add_project("Temporary extra project")
        with patch("app.filedialog.askopenfilename", return_value=str(backup)), patch("app.messagebox.askyesno", return_value=False):
            app.restore_backup()
        assert len(store.projects()) == 2
        with patch("app.filedialog.askopenfilename", return_value=str(backup)), patch("app.messagebox.askyesno", return_value=True), patch("app.messagebox.showinfo"):
            app.restore_backup()
        assert len(store.projects()) == 1
        assert "Example" in app.heading.cget("text")
        root.after_cancel(app.reminder_timer)
        print("GUI smoke check passed: planning, checklists, reminders, backup creation, cancelled restore and confirmed restore.")
    finally:
        root.destroy()
        store.close()
