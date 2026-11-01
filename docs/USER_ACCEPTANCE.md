# First user acceptance session

Status: the owner reported that the initial application worked. Individual checklist results were not supplied and remain unverified. The new agenda, alerts, percentage display and description editor await owner acceptance.

## Preparation

Allow 15–20 minutes. Start the application using the README instructions. On the current development computer, a separate Start-PlanoLocal.ps1 launcher is provided outside this repository.

Use a personal activity such as learning drawing or assembling a model kit. Do not enter information about other people or confidential work. The interface is Portuguese; project documentation is English.

## Checklist

| Step | Action | Expected result | Actual result |
|---|---|---|---|
| 1 | Choose Novo projeto; enter a name and objective; save | Project and objective appear | Pending |
| 2 | Choose Nova tarefa and create three concrete actions | Three tasks appear in the selected project | Pending |
| 3 | Set past and future deadlines; leave one blank | Overdue pending task is red; undated task shows Sem prazo | Pending |
| 4 | Double-click a task; select Em andamento | Status changes | Pending |
| 5 | Mark one task Concluída | Progress shows one of three complete; completed task appears last | Pending |
| 6 | Try the impossible date 2026-02-30 | Validation message appears; saved task remains unchanged | Pending |
| 7 | Create another project and task; switch between projects | Each project shows only its tasks | Pending |
| 8 | Close and reopen using the same data location | Projects, tasks, dates and statuses persist | Pending |
| 9 | Resize the window and navigate with Tab | Record clipped text, unreachable controls or confusing focus | Pending |

## Feedback record

Complete only after real use. Feedback may be provided in Portuguese and will be documented in English.

- Session date: pending
- Application commit: pending
- Personal activity used: pending
- Steps completed and observations: pending
- What was useful: pending
- Main difficulty: pending
- Most valuable next feature: pending
- Would the owner continue using this? Why? pending

## Completion rule

Actual owner feedback is required. Automated tests and assistant smoke checks do not count as owner acceptance. Convert failures into actionable tasks and update the roadmap before selecting the next feature.

## Owner feedback — November 1, 2026

The owner reported that the application worked and requested:

1. An agenda with alerts when a task deadline is approaching.
2. An explicit project completion percentage based on task execution.
3. A project description.

The owner did not report specific test steps or an activity name. These details must not be inferred.

## Follow-up acceptance checklist

- Open **Agenda e alertas** and verify that pending dated tasks appear across projects in deadline order.
- Create a task due tomorrow and verify the alert banner; sound may depend on system settings.
- Complete that task and verify it disappears from the agenda and reminder count.
- Complete one of two tasks and verify 50% is shown. Reopen it and verify 0%.
- Edit a project description using multiple lines, reopen the application and verify it persists.
- Confirm whether date-based, in-app alerts meet the need or whether time-of-day and closed-app Windows notifications are needed next.

Follow-up result: the owner reported that the iteration worked. Individual checklist outcomes were not supplied. The owner then requested a more substantial product direction and agreed to weekly execution planning.

The next acceptance scenario is documented in [WEEKLY_PLANNING.md](WEEKLY_PLANNING.md). Its results remain pending.

Update: the owner subsequently reported that the weekly-planning iteration was checked and requested the next stages. No individual outcomes or screenshots were supplied.

## Checklist and reminder acceptance

1. Select a pending task, open **Subtarefas**, add two steps and mark only one complete.
2. Verify the parent cannot be completed until the second step is checked.
3. Complete the parent, then verify an item cannot be unchecked until the parent is reopened.
4. Follow [Windows reminder setup and verification](WINDOWS_REMINDERS.md) from a normal Windows session.

Results for this iteration: pending. Native background reminder activation is not yet verified.

Update: the owner explicitly confirmed that the test notification appeared and scheduler status was active without errors. Record these two checks as owner-confirmed; timed delivery with the app closed remains unreported.

Next acceptance exercise: follow [backup and recovery](BACKUPS.md) using a temporary project after first creating a backup. Results remain pending.
