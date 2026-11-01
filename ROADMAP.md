# Development roadmap

Plano Local helps me turn personal projects into achievable weekly work. The current prototype supports tasks, checklists, dependencies, effort estimates, weekly capacity, reminders and backup/restore. I intend to continue using and improving it independently of any external program.

The owner has reported successful checks of weekly planning and backup/restore, as well as Windows test notification visibility and active scheduler status. Sustained use, timed closed-app delivery and clean-machine installation still need further evidence.

## Planned work

These are prospective engineering estimates, not measured or billable hours. The planning estimate is **24 hours**, with an uncertainty range of **19–29 hours**. Estimates may change after implementation and real use; completed work must be removed from the remaining total.

| Task | Execution steps | Acceptance criteria | Planning estimate | Range |
|---|---|---|---|---|
| Real-use validation | Use the planner for a personal project; record friction; turn observations into actionable fixes | Feedback is documented and prioritized without claiming unobserved outcomes | 1.5 h | 1–2 h |
| Project archiving | Define archive behavior; migrate storage; implement archive/restore; exclude archived projects from active views and alerts; test migration | Archived projects retain their data, disappear from active planning and can be restored | 2.5 h | 2–3 h |
| Search and filters | Add title search and status/deadline filters; combine filters; handle empty results and project switching | Users can find tasks without modifying data or mixing projects | 3.5 h | 3–4 h |
| Selective export and import | Select projects to export; define a versioned interchange format; remap IDs and dependencies on import; handle conflicts; verify round trips | Import merges selected projects without replacing unrelated data, unlike full backup restoration | 5 h | 4–6 h |
| Multiple prerequisites | Migrate single links to a relation table; update editor and blocked-state logic; test cycles and upgrade behavior | Tasks can depend on multiple tasks and unlock only when all prerequisites are complete | 3 h | 2–4 h |
| Accessibility and interface | Review keyboard focus, scaling, contrast, resizing and long text; fix issues; validate core flows | Core workflows work by keyboard and at documented window/scaling settings | 3.5 h | 3–4 h |
| Windows packaging and release | Produce a reproducible package; test clean installation and upgrades; verify reminder paths after installation; document known limits | A Windows distributable works without the development computer's runtime paths | 5 h | 4–6 h |

## Current milestone

The first functional prototype and its basic owner acceptance checks are complete. The next milestone is a public repository with reproducible instructions, an honest account of testing and preserved development history.

Optional follow-up, not included in the estimate: measured time versus estimates, richer execution history and expanded reminder behavior. Add these only when actual usage justifies them.
