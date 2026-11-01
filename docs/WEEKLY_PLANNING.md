# Weekly execution planning

## Purpose

Help a person turn a project into an actionable week and identify workload or dependency problems before delivery deadlines are missed. This is a deterministic planning tool; it does not evaluate or train AI models.

## Implemented scope

- Optional effort estimate in hours, with comma or decimal-point input.
- Optional execution day distinct from the final deadline.
- One prerequisite per task, restricted to the same project.
- Monday–Sunday planning view spanning all projects, with previous/current/next-week navigation.
- Available weekly hours stored independently for each week.
- Indicators for blocked work, execution dates later than deadlines, missing estimates and unscheduled work.
- Effort-weighted completion alongside the existing task-count percentage.

## Rules and tradeoffs

1. Estimates must be finite, positive numbers up to 10,000 hours. A blank estimate is unknown, not zero effort.
2. Weekly capacity must be greater than zero and at most 168 hours. No capacity is assumed until entered.
3. The workload comparison includes completed and pending estimates: completing work consumes the week's planned budget rather than freeing it. It does not measure actual time spent.
4. In-progress tasks retain their full estimate. Remaining-effort tracking is not implemented.
5. Unscheduled tasks do not appear in the weekly list; the view displays their count across all projects.
6. The final-deadline agenda and its alerts remain independent of the execution-day view. Scheduling a task does not change its deadline.
7. A task whose prerequisite is unfinished must remain in the to-do state. A prerequisite cannot be reopened while a dependent task is in progress or complete; reset dependents first.
8. Self-dependencies, cross-project dependencies and indirect cycles are rejected without saving partial planning changes.
9. Effort-weighted project progress is available only when every task has an estimate. Task-count progress remains available regardless.
10. No background scheduling service, automatic rescheduling, critical-path solver or predicted completion date is implemented.

## Data upgrade

The existing project and task records remain intact. For an existing database with tasks, a uniquely named SQLite backup is created next to the original before the three planning columns are added in a transaction. Reopening an upgraded database does not repeat the backup. User data and backup copies remain excluded from Git.

## Suggested acceptance scenario

Use a test project with fictional task names, or a real personal project without third-party information.

1. Create **Prepare materials** and **Assemble prototype**.
2. Estimate them at 1 and 3 hours, and schedule both in the same week.
3. Make assembly depend on preparation. Verify assembly shows as blocked and cannot start yet.
4. Set weekly capacity to 3 hours. Verify the view shows an estimated 1-hour excess.
5. Complete preparation. Verify assembly unlocks and project progress shows 50% by task count and 25% by effort.
6. Schedule assembly after its final deadline and verify the warning.
7. Try making preparation depend on assembly. Verify the circular link is rejected.
8. Close and reopen the application. Verify estimates, dates, dependency and weekly capacity persist.

Owner acceptance of this iteration: pending. Automated checks are recorded in the development log.

## Follow-up work

Subtask checklists, multiple prerequisites, actual-versus-estimated time, time-of-day reminders and closed-app Windows notifications are still future work. Prioritize these using real-use feedback.
