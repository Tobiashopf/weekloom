# Windows reminder integration

## Status

The owner confirmed that the test notification appeared and **Consultar estado** showed an active schedule without errors in the normal Windows session. This is owner-reported verification, not a direct observation by the assistant. The assistant environment still cannot access the native notification area or scheduler. Timed delivery with the application closed, sleep/battery behavior and deactivation have not been separately confirmed.

## Setup in a normal Windows session

1. Close earlier application windows so the latest version is used.
2. Launch the application directly on Windows. On the development computer, double-click the separate `Launch-PlanoLocal.cmd` file. On other computers, follow the README Python instructions.
3. Open **Notificações do Windows** and choose **Testar aviso**.
4. Confirm whether the notification appeared. An accepted API request alone is not evidence of visible delivery; Windows may suppress it.
5. Choose **Ativar** and then **Consultar estado**. Registration must succeed before closed-app reminders are expected to work. If Windows reports an error, preserve the message for diagnosis; do not change system security settings to suppress it.
6. Select a pending task, choose **Lembrete**, and set a time several minutes ahead using local time.
7. Close the application and remain signed in with the computer awake. Allow the five-minute checking interval, plus normal operating-system scheduling delays.
8. Confirm one notification arrives. Reopening the app should preserve the configured reminder and its delivery record.
9. Choose **Desativar** to remove this database's scheduled task when no longer wanted.

## Behavior

- A custom timestamp overrides the default background reminder for that task and is delivered once. A changed timestamp creates a new event.
- Without a custom timestamp, unfinished tasks with deadlines today, tomorrow or earlier qualify once per local day after 09:00.
- Missed custom times are considered on the next successful check. The computer is not awakened, and no notification can appear while it is off or the user is signed out.
- Completed tasks are excluded. Reopening a task does not resend an already recorded custom event unless its reminder timestamp changes.
- Clearing a custom reminder restores the daily rule. The in-app deadline banner remains independent of custom background reminder times.
- The notification contains a count and a generic prompt, not project names or task details. It has no click-to-open action yet.
- Delivery records are stored only after Windows accepts the notification request. Failures remain retryable. Windows acceptance does not prove the user saw the notification; a crash between delivery and recording may also allow a retry.
- Notification records are local SQLite data. No account, network service or third-party package is used.

## Implementation

- `notifications.py` performs one check and exits. A missing database is rejected rather than silently created.
- `windows_notify.py` calls the native Windows notification-area API through Python's standard-library ctypes. A temporary hidden window pumps messages while the notification is active; its icon is removed afterward.
- `reminder_setup.py` registers an interactive, least-privilege task via Windows Task Scheduler. Its name is derived from the database path, keeping schedules for different databases separate.
- XML registration avoids the short command-length limit of the `schtasks /TR` option. XML escapes paths as data, and subprocess calls do not invoke a command shell.
- The task uses `pythonw.exe`, runs at five-minute intervals, permits battery operation and ignores overlapping scheduled invocations. It does not request stored credentials or change PowerShell execution policy.
- Existing databases with tasks receive a pre-reminder migration copy before the reminder column is added. Checklist and notification tables are additive.

## Verification evidence

Automated checks cover checklist state rules, reminder time validation, daily cutoff, custom scheduling, rescheduling, completion exclusion, persistent deduplication, retry after failed delivery, missing database handling and XML task definition properties. GUI smoke checks cover checklist actions and saving a custom timestamp.

Owner-confirmed: test popup visibility and active schedule status. Still required: timed closed-app execution, battery/sleep behavior, removal verification and an installed release test. These are not replaced by unit tests.

## Platform references

- [Microsoft: NOTIFYICONDATAW](https://learn.microsoft.com/windows/win32/api/shellapi/ns-shellapi-notifyicondataw)
- [Microsoft: scheduled task XML example](https://learn.microsoft.com/en-us/windows/win32/taskschd/daily-trigger-example--xml-)
