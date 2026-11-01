"""Run with Python 3.10+ (including Tk): python app.py."""
import argparse
from datetime import date, timedelta
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
        self.week_window = None
        self.week_day = date.today()
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
        ttk.Button(reminder_bar, text="Planejar semana", command=self.open_week).pack(side="right", padx=8)
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
        self.effort_summary = ttk.Label(right, text="", wraplength=600)
        self.effort_summary.pack(anchor="w", pady=(0, 8))
        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 10))
        self.add = ttk.Button(toolbar, text="+ Nova tarefa", command=self.new_task, state="disabled")
        self.add.pack(side="left")
        ttk.Button(toolbar, text="Editar tarefa", command=self.edit_task).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Planejar tarefa", command=self.plan_task).pack(side="left")
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
        if self.week_window is not None and self.week_window.winfo_exists():
            self.refresh_week()

    def open_week(self):
        if self.week_window is not None and self.week_window.winfo_exists():
            self.week_window.lift()
            return
        window = self.week_window = tk.Toplevel(self.root)
        window.title("Planejamento semanal")
        window.geometry("1000x560")
        window.minsize(850, 460)
        body = ttk.Frame(window, padding=20)
        body.pack(fill="both", expand=True)
        navigation = ttk.Frame(body)
        navigation.pack(fill="x")
        ttk.Button(navigation, text="← Anterior", command=lambda: self.move_week(-7)).pack(side="left")
        ttk.Button(navigation, text="Esta semana", command=lambda: self.move_week(None)).pack(side="left", padx=6)
        ttk.Button(navigation, text="Próxima →", command=lambda: self.move_week(7)).pack(side="left")
        self.week_heading = ttk.Label(body, text="", font=("Segoe UI", 15, "bold"))
        self.week_heading.pack(anchor="w", pady=(12, 8))
        capacity_bar = ttk.Frame(body)
        capacity_bar.pack(fill="x")
        ttk.Label(capacity_bar, text="Horas disponíveis nesta semana:").pack(side="left")
        self.capacity_var = tk.StringVar()
        ttk.Entry(capacity_bar, textvariable=self.capacity_var, width=8).pack(side="left", padx=8)
        ttk.Button(capacity_bar, text="Salvar capacidade", command=self.save_capacity).pack(side="left")
        self.week_summary = ttk.Label(body, text="", wraplength=900)
        self.week_summary.pack(anchor="w", pady=10)
        frame = ttk.Frame(body)
        frame.pack(fill="both", expand=True)
        self.week_tree = ttk.Treeview(frame, columns=("day", "project", "task", "hours", "state"), show="headings")
        for key, label, width in (("day", "Execução", 100), ("project", "Projeto", 150), ("task", "Tarefa", 250), ("hours", "Horas", 70), ("state", "Situação", 220)):
            self.week_tree.heading(key, text=label)
            self.week_tree.column(key, width=width, minwidth=60)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.week_tree.yview)
        self.week_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.week_tree.pack(fill="both", expand=True)
        self.week_tree.tag_configure("risk", foreground="#a52b24")
        self.week_tree.bind("<Double-1>", self.plan_week_task)
        ttk.Label(body, text="Use Planejar tarefa para definir o dia de execução, as horas e uma dependência.\nClique duas vezes em uma linha para replanejar. As horas são estimativas, não tempo medido.", wraplength=900).pack(anchor="w", pady=(10, 0))
        self.load_capacity()
        self.refresh_week()

    def load_capacity(self):
        value = self.store.week_plan(self.week_day)["capacity"]
        self.capacity_var.set("" if value is None else f"{value:g}")

    def move_week(self, days):
        self.week_day = date.today() if days is None else self.week_day + timedelta(days=days)
        self.load_capacity()
        self.refresh_week()

    def save_capacity(self):
        try:
            self.store.set_capacity(self.week_day, self.capacity_var.get())
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Capacidade semanal", str(error), parent=self.week_window)
            return
        self.refresh_week()

    def refresh_week(self):
        plan = self.store.week_plan(self.week_day)
        self.week_heading.configure(text=f'{plan["start"]:%d/%m} a {plan["end"]:%d/%m/%Y}')
        load = plan["pending_hours"] + plan["completed_hours"]
        capacity = plan["capacity"]
        capacity_text = "Defina sua capacidade semanal." if capacity is None else f"Capacidade: {capacity:g} h."
        overload = capacity is not None and load > capacity
        if overload:
            capacity_text += f" Excesso estimado: {load - capacity:g} h. Replaneje entregas."
        text = (f'{plan["pending_hours"]:g} h pendentes · {plan["completed_hours"]:g} h estimadas concluídas. {capacity_text}\n'
                f'{plan["missing_estimates"]} tarefa(s) sem estimativa · {plan["blocked"]} bloqueada(s) · '
                f'{plan["late_plans"]} planejada(s) após o prazo · {plan["unscheduled"]} sem dia de execução (todos os projetos).')
        self.week_summary.configure(text=text, foreground="#a52b24" if overload or plan["blocked"] or plan["late_plans"] else "#263442")
        self.week_tree.delete(*self.week_tree.get_children())
        for task in plan["tasks"]:
            state = "Bloqueada: " + task["prerequisite"] if task["blocked"] else task["status"]
            late_plan = task["status"] != "Concluída" and task["due"] and task["planned_for"] > task["due"]
            if late_plan:
                state += " · após prazo"
            self.week_tree.insert("", "end", iid=str(task["id"]), values=(task["planned_for"], task["project_name"], task["title"], "—" if task["estimate_hours"] is None else f'{task["estimate_hours"]:g}', state), tags=("risk",) if task["blocked"] or late_plan else ())

    def plan_week_task(self, event=None):
        selected = self.week_tree.selection()
        if not selected:
            return
        task = next(t for t in self.store.week_plan(self.week_day)["tasks"] if str(t["id"]) == selected[0])
        self.project_id = task["project_id"]
        self.reload_projects()
        self.refresh_tasks()
        self.tasks.selection_set(selected[0])
        self.plan_task()

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
            blocked = self.store.blockers(task["id"])
            self.tasks.insert("", "end", iid=str(task["id"]), values=(task["title"], task["due"] or "Sem prazo", "Bloqueada" if blocked else task["status"]), tags=("late",) if late or blocked else ())
        percent = self.store.completion(project)
        self.progress["value"] = percent
        self.summary.configure(text=f'{percent:.0f}% concluído · {project["done"]} de {project["total"]} tarefas · {overdue} atrasada(s)')
        effort = self.store.effort_progress(self.project_id)
        self.effort_summary.configure(text="Progresso por esforço: estime as horas de todas as tarefas para calcular." if effort is None else f"Progresso por esforço estimado: {effort:.0f}%")

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

    def plan_task(self):
        selected = self.tasks.selection()
        if not selected:
            messagebox.showinfo("Planejar tarefa", "Selecione uma tarefa primeiro.", parent=self.root)
            return
        tasks = self.store.tasks(self.project_id)
        task = next(t for t in tasks if str(t["id"]) == selected[0])
        choices = {"Nenhuma": None}
        choices.update({f'{t["id"]} · {t["title"]}': t["id"] for t in tasks if t["id"] != task["id"]})
        current = next(label for label, key in choices.items() if key == task["depends_on"])
        self.dialog("Planejar tarefa", [
            ("Esforço estimado em horas (opcional; exemplo: 1,5)", "" if task["estimate_hours"] is None else str(task["estimate_hours"]), None),
            ("Dia de execução (opcional; AAAA-MM-DD)", task["planned_for"] or "", None),
            ("Depende da conclusão de", current, tuple(choices)),
        ], lambda hours, day, dependency: self.store.save_plan(task["id"], hours, day, choices[dependency]))

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
