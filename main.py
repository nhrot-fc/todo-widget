import sys
from src.core.logging import setup_logging, get_logger
from src.core.config import settings
from src.managers.task_manager import TaskManager
from src.gui.TodoApp import TodoApp

setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)


def print_help():
    help_text = """
    Todo Application Help:
    --help          Show this help message
    --app           Show application GUI
    (no args)       Print task statistics
    """
    print(help_text)


if __name__ == "__main__":
    manager = TaskManager(settings.storage_path)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--help":
            print_help()
        elif arg == "--app":
            try:
                gui = TodoApp(task_manager=manager)
                gui.run()
            except KeyboardInterrupt:
                logger.info("Application stopped by user")
    else:
        stats = manager.get_stats()
        print(stats)
