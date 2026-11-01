"""One-shot background reminder worker for Windows Task Scheduler."""
import argparse
from pathlib import Path
import sys
from planner import Planner


def notify(count):
    from windows_notify import show_notification
    show_notification(count)


def run(path, sender=notify):
    if not Path(path).is_file():
        raise ValueError("The planner database does not exist; open the application first.")
    store = Planner(path)
    try:
        events = store.pending_notifications()
        if events:
            sender(len(events))
            store.record_notifications(events)
        return len(events)
    finally:
        store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    try:
        if args.test:
            notify(0)
            print("Test notification requested. Visibility depends on Windows settings.")
        elif args.data:
            print(f"Notification events processed: {run(args.data)}")
        else:
            parser.error("--data or --test is required")
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
