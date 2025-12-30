import sys
from datetime import datetime

from src.core.logging import setup_logging, get_logger
from src.core.config import settings

setup_logging(settings.log_level, settings.log_file)

from src.gui.TodoApp import main
from src.managers.task_manager import manager


logger = get_logger(__name__)


def print_help():
    help_text = """
    Todo Application Help:
    --help          Show this help message
    --version       Show application version
    """
    print(help_text)


def get_stats() -> dict[str, int]:
    tasks = manager.get_tasks()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks.values() if task.completed)
    pending_tasks = total_tasks - completed_tasks
    expired_tasks = sum(
        1
        for task in tasks.values()
        if task.due_date and not task.completed and task.due_date < datetime.now()
    )

    return {
        "total": total_tasks,
        "completed": completed_tasks,
        "pending": pending_tasks,
        "expired": expired_tasks,
    }


if __name__ == "__main__":
    # Get arguments from command line and start the application
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--help":
            print_help()
        elif arg == "--app":
            main()
    else:
        print(get_stats())
