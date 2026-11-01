"""Run with Python 3.10+ (including Tk): python app.py."""
import argparse
from datetime import date
import os
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from planner import Planner, STATUSES


class App:
    def __init__(self, root, store):
        self.root, self.store = root, store
        self.project_id = None
        self.notified = set()
        self.agenda_window = None
        root.title("Plano Local — seus projetos pessoais")
        root.geometry("1060x680")
        root.minsize(820, 540)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=32, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", padding=7, font=("Segoe UI", 10))
        style.configure("Heading.TLabel", font=("Segoe UI", 22, "bold"))
        outer = ttk.Frame(root, padding=24)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Plano Local", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Uma próxima ação para cada projeto. Tudo salvo neste computador.").pack(anchor="w", pady=(4, 20))
        reminder_bar = ttk.Frame(outer)
        reminder_bar.pack(fill="x", pady=(0, 12))
        self.reminder = ttk.Label(reminder_bar, text="", wraplength=680)
        self.reminder.pack(side="left", fill="x", expand=True)
        ttk.Button(reminder_bar, text="Agenda e alertas", command=self.open_agenda).pack(side="right")
        columns = ttk.Panedwindow(outer, orient="horizontal")
        columns.pack(fill="both", expand=True)
        left, right = ttk.Frame(columns), ttk.Frame(columns, padding=(20, 0, 0, 0))
        columns.add(left, weight=1)
        columns.add(right, weight=3)
        ttk.Button(left, text="+ Novo projeto", command=self.new_project).pack(fill="x", pady=(0, 10))
        self.edit_project_button = ttk.Button(left, text="Editar projeto / descrição", command=self.edit_project, state="disabled")
        self.edit_project_button.pack(fill="x", pady=(0, 10))
        self.projects = ttk.Treeview(left, show="tree", selectmode="browse", height=10)
        self.projects.column("#0", width=230, minwidth=150)
        self.projects.pack(fill="both", expand=True)
        self.projects.bind("<<TreeviewSelect>>", self.select_project)
        self.heading = ttk.Label(right, text="Crie seu primeiro projeto", font=("Segoe UI", 15, "bold"))
        self.heading.pack(anchor="w")
        self.description = ttk.Label(right, text="", wraplength=540)
        self.description.pack(anchor="w", pady=(5, 8))
        self.progress = ttk.Progressbar(right, maximum=100)
        self.progress.pack(fill="x")
        self.summary = ttk.Label(right, text="Nenhuma tarefa ainda.")
        self.summary.pack(anchor="w", pady=(5, 12))
        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 10))
        self.add = ttk.Button(toolbar, text="+ Nova tarefa", command=self.new_task, state="disabled")
        self.add.pack(side="left")
        ttk.Button(toolbar, text="Editar tarefa", command=self.edit_task).pack(side="left", padx=8)
        frame = ttk.Frame(right)
        frame.pack(fill="both", expand=True)
        self.tasks = ttk.Treeview(frame, columns=("title", "due", "status"), show="headings", selectmode="browse")
        for key, label, width in (("title", "Tarefa", 290), ("due", "Prazo", 100), ("status", "Status", 125)):
            self.tasks.heading(key, text=label)
            self.tasks.column(key, width=width, minwidth=80)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tasks.yview)
        self.tasks.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tasks.pack(fill="both", expand=True)
        self.tasks.tag_configure("late", foreground="#a52b24")
        self.tasks.bind("<Double-1>", lambda event: self.edit_task())
        ttk.Label(outer, text="Prazos vencidos aparecem em vermelho. Clique duas vezes em uma tarefa para editar.").pack(anchor="w", pady=(16, 0))
        self.reload_projects()
        self.check_reminders()
        self.reminder_timer = root.after(60000, self.poll_reminders)

    def check_reminders(self):
        tasks = self.store.due_soon()
        today = date.today().isoformat()
        overdue = sum(task["due"] < today for task in tasks)
        upcoming = len(tasks) - overdue
        self.reminder.configure(
            text=f"Alertas: {overdue} atrasada(s) · {upcoming} vencendo hoje ou amanhã."
                 if tasks else "Nenhum prazo pendente até amanhã.",
            foreground="#a52b24" if tasks else "#266346",
        )
        keys = {(task["id"], task["due"], today) for task in tasks}
        if keys - self.notified:
            self.root.bell()
        self.notified = keys
        if self.agenda_window is not None and self.agenda_window.winfo_exists():
            self.refresh_agenda()

    def poll_reminders(self):
        self.check_reminders()
        if self.project_id is not None:
            self.refresh_tasks()
        self.reminder_timer = self.root.after(60000, self.poll_reminders)

    def open_agenda(self):
        if self.agenda_window is not None and self.agenda_window.winfo_exists():
            self.agenda_window.lift()
            return
        window = self.agenda_window = tk.Toplevel(self.root)
        window.title("Agenda — todos os projetos")
        window.geometry("850x450")
        window.minsize(650, 350)
        body = ttk.Frame(window, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Tarefas pendentes por prazo", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(body, text="Alertas visuais e som ao abrir e durante o uso. O aplicativo precisa estar aberto.", wraplength=740).pack(anchor="w", pady=(8, 12))
        frame = ttk.Frame(body)
        frame.pack(fill="both", expand=True)
        self.agenda_tree = ttk.Treeview(frame, columns=("due", "when", "project", "title"), show="headings")
        for key, label, width in (("due", "Prazo", 100), ("when", "Quando", 100), ("project", "Projeto", 180), ("title", "Tarefa", 300)):
            self.agenda_tree.heading(key, text=label)
            self.agenda_tree.column(key, width=width, minwidth=80)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.agenda_tree.yview)
        self.agenda_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.agenda_tree.pack(fill="both", expand=True)
        self.agenda_tree.tag_configure("urgent", foreground="#a52b24")
        self.agenda_empty = ttk.Label(body, text="")
        self.agenda_empty.pack(anchor="w", pady=(8, 0))
        self.refresh_agenda()

    def refresh_agenda(self):
        self.agenda_tree.delete(*self.agenda_tree.get_children())
        tasks = self.store.agenda()
        for task in tasks:
            days = (date.fromisoformat(task["due"]) - date.today()).days
            when = "Atrasada" if days < 0 else "Hoje" if days == 0 else "Amanhã" if days == 1 else f"Em {days} dias"
            self.agenda_tree.insert("", "end", values=(task["due"], when, task["project_name"], task["title"]), tags=("urgent",) if days <= 1 else ())
        self.agenda_empty.configure(text="Nenhuma tarefa pendente com prazo definido." if not tasks else f"{len(tasks)} tarefa(s) com prazo. Concluídas e sem prazo não aparecem aqui.")

    def reload_projects(self):
        self.projects.delete(*self.projects.get_children())
        for project in self.store.projects():
            self.projects.insert("", "end", iid=str(project["id"]), text=f'{project["name"]}  ·  {self.store.completion(project):.0f}%')
        if self.project_id is not None:
            self.projects.selection_set(str(self.project_id))

    def select_project(self, event=None):
        selected = self.projects.selection()
        if not selected:
            return
        self.project_id = int(selected[0])
        self.refresh_tasks()

    def refresh_tasks(self):
        project = next(p for p in self.store.projects() if p["id"] == self.project_id)
        self.heading.configure(text=project["name"])
        self.description.configure(text="Descrição: " + (project["description"] or "Adicione uma descrição em Editar projeto / descrição."))
        self.edit_project_button.configure(state="normal")
        self.add.configure(state="normal")
        self.tasks.delete(*self.tasks.get_children())
        rows = self.store.tasks(self.project_id)
        overdue = 0
        for task in rows:
            late = bool(task["due"] and task["due"] < date.today().isoformat() and task["status"] != "Concluída")
            overdue += late
            self.tasks.insert("", "end", iid=str(task["id"]), values=(task["title"], task["due"] or "Sem prazo", task["status"]), tags=("late",) if late else ())
        percent = self.store.completion(project)
        self.progress["value"] = percent
        self.summary.configure(text=f'{percent:.0f}% concluído · {project["done"]} de {project["total"]} tarefas · {overdue} atrasada(s)')

    def dialog(self, title, fields, save):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.transient(self.root)
        window.grab_set()
        window.resizable(False, False)
        body = ttk.Frame(window, padding=24)
        body.pack(fill="both", expand=True)
        variables = []
        first = None
        for label, value, options in fields:
            ttk.Label(body, text=label).pack(anchor="w", pady=(8, 3))
            variable = tk.StringVar(value=value)
            if options == "multiline":
                widget = tk.Text(body, width=51, height=5, wrap="word", font=("Segoe UI", 10))
                widget.insert("1.0", value)
                variables.append(lambda widget=widget: widget.get("1.0", "end-1c"))
            else:
                widget = ttk.Combobox(body, textvariable=variable, values=options, state="readonly", width=48) if options else ttk.Entry(body, textvariable=variable, width=51)
                variables.append(variable.get)
            widget.pack(fill="x")
            first = first or widget
        def submit():
            try:
                save(*(getter() for getter in variables))
            except (ValueError, OSError, sqlite3.Error) as error:
                messagebox.showerror("Não foi possível salvar", str(error), parent=window)
                return
            window.destroy()
            self.reload_projects()
            if self.project_id is not None:
                self.refresh_tasks()
            self.check_reminders()
        ttk.Button(body, text="Salvar", command=submit).pack(anchor="e", pady=(20, 0))
        window.bind("<Escape>", lambda event: window.destroy())
        window.bind("<Return>", lambda event: None if isinstance(event.widget, tk.Text) else submit())
        first.focus_set()

    def new_project(self):
        def save(name, description):
            self.project_id = self.store.add_project(name, description)
        self.dialog("Novo projeto", [("Nome", "", None), ("Descrição do projeto", "", "multiline")], save)

    def edit_project(self):
        if self.project_id is None:
            return
        project = next(p for p in self.store.projects() if p["id"] == self.project_id)
        self.dialog("Editar projeto", [("Nome", project["name"], None), ("Descrição do projeto", project["description"], "multiline")], lambda name, description: self.store.update_project(self.project_id, name, description))

    def new_task(self):
        if self.project_id is not None:
            self.dialog("Nova tarefa", [("Título", "", None), ("Prazo opcional (AAAA-MM-DD)", "", None)], lambda title, due: self.store.add_task(self.project_id, title, due))

    def edit_task(self):
        selected = self.tasks.selection()
        if not selected:
            messagebox.showinfo("Editar tarefa", "Selecione uma tarefa primeiro.", parent=self.root)
            return
        task = next(t for t in self.store.tasks(self.project_id) if str(t["id"]) == selected[0])
        self.dialog("Editar tarefa", [("Título", task["title"], None), ("Prazo opcional (AAAA-MM-DD)", task["due"] or "", None), ("Status", task["status"], STATUSES)], lambda title, due, status: self.store.update_task(task["id"], title, due, status))


def main():
    parser = argparse.ArgumentParser(description="Planejador local de projetos pessoais")
    default = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "share"))) / "PlanoLocal" / "planner.sqlite3"
    parser.add_argument("--data", type=Path, default=default)
    args = parser.parse_args()
    store = Planner(args.data)
    try:
        root = tk.Tk()
        App(root, store)
        root.mainloop()
    finally:
        store.close()


if __name__ == "__main__":
    main()
