# Backup and recovery

## Included data

Backup version 1 includes every project, task, checklist item, weekly capacity and reminder-delivery record. Task fields include status, final deadline, execution day, estimate, prerequisite and custom reminder time. IDs and relationships are preserved.

The Windows scheduled-task registration, Python installation and application files are not included. Restore into this compatible application version; configuring Windows reminders on another computer is a separate step.

## Creating a backup

1. Choose **Criar backup**.
2. Select a location and a name ending in `.plano-backup`.
3. Wait for the success message before moving or copying the file.

The application takes a consistent SQLite read snapshot. It writes a temporary file in the destination directory, flushes the file, and atomically publishes the completed backup. If publication fails, an existing destination backup is retained and the temporary file is removed. Choosing the live database or an unsupported extension is rejected.

Backups are ordinary unencrypted JSON files. Store them in a location appropriate for the contents. They are excluded from version control. A copy on the same disk helps with mistakes but does not protect against loss of that disk; the user may copy the finished file to their own backup storage.

## Restoring a backup

1. Close other Plano Local windows to avoid editing from stale views.
2. Choose **Restaurar** and select the file.
3. Review the project and task counts. Restoration replaces all existing application data; it does not merge data.
4. Confirm only if this is the intended snapshot.
5. Save the location of the automatic recovery copy shown after completion.

The application validates the format version, table/field structure, data types, dates, numeric ranges, IDs, relationships, dependency cycles, task states and checklist consistency before changing the live database. It loads only known table data through parameterized inserts, never a database schema or SQL script supplied by the backup.

After acquiring a write lock, it saves the current state to `planner.before-restore-<timestamp>-<id>.plano-backup` next to the database, then replaces the data in one transaction. If creating the recovery copy or writing the restored data fails, current database records remain intact. If the selected file changes after the preview, the operation is rejected. Open detail windows are closed after a successful restore and the main view is refreshed.

## Undoing a restore

Choose **Restaurar** again and select the automatic `before-restore` copy. Review its counts and confirm. This operation also creates a new recovery copy of the state it replaces.

## Reminder implications

The notification ledger is part of the restored snapshot. If an older snapshot predates a delivered reminder, that reminder may qualify again. The existing Windows schedule continues to reference the same database path and is not modified by restore. A reminder already being processed by a background worker may finish independently of a restore.

## Validation evidence

Automated tests cover full-table round trips and persistence after reopening, recovery-copy contents, invalid/corrupt files, unknown format versions, bad references, cycles, invalid dates and estimates, duplicate IDs, simulated mid-restore failure, unavailable recovery storage, source-file changes and failed backup publication. GUI checks cover creating a file, cancelling a restore and confirming a restore.

The owner reported that the proposed backup/restore exercise was completed successfully. This is owner-reported acceptance of the basic flow, not independent verification of every field or failure scenario. No restoration of the owner's real data was performed by the assistant during development tests.

## Acceptance exercise

1. Create a backup of the current data.
2. Add a temporary project named **Backup test** with no important content.
3. Restore the backup after reviewing the confirmation.
4. Verify that **Backup test** disappears and the earlier projects, tasks and checklists remain.
5. Locate the automatic recovery copy. Optionally restore it to verify that **Backup test** returns.
