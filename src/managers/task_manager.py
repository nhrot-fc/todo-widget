import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from src.core.config import settings
from src.core.logging import get_logger
from src.schemas.task import Task

logger = get_logger(__name__)


class TaskManager:
    def __init__(self):
        self.tasks: dict[int, Task] = {}
        self.file_path = Path(settings.storage_path)
        self.load_tasks()

    def _next_id(self) -> int:
        """Calcula el siguiente ID disponible."""
        if not self.tasks:
            return 1
        return max(self.tasks.keys()) + 1

    def add_task(
        self, title: str, due_date: datetime | None = None
    ) -> tuple[int, Task]:
        task_id = self._next_id()
        task = Task(title=title, due_date=due_date)
        self.tasks[task_id] = task
        logger.info(f"Added task: {task}")
        return task_id, task

    def edit_task_title(self, task_id: int, new_title: str) -> bool:
        if task_id not in self.tasks:
            logger.warning(f"Attempted to edit non-existent task with ID: {task_id}")
            return False

        self.tasks[task_id].title = new_title
        logger.info(f"Edited title of task ID {task_id} to: {new_title}")
        return True

    def edit_task_due_date(self, task_id: int, new_due_date: datetime | None) -> bool:
        if task_id not in self.tasks:
            logger.warning(f"Attempted to edit non-existent task with ID: {task_id}")
            return False

        self.tasks[task_id].due_date = new_due_date
        logger.info(f"Edited due date of task ID {task_id} to: {new_due_date}")
        return True

    def remove_task(self, task_id: int) -> bool:
        if task_id not in self.tasks:
            logger.warning(f"Attempted to remove non-existent task with ID: {task_id}")
            return False

        del self.tasks[task_id]
        logger.info(f"Removed task with ID: {task_id}")
        return True

    def toggle_task(self, task_id: int) -> bool:
        if task_id not in self.tasks:
            logger.warning(f"Attempted to toggle non-existent task with ID: {task_id}")
            return False

        task = self.tasks[task_id]
        task.completed = not task.completed
        logger.info(f"Toggled completion for task ID {task_id} to {task.completed}")
        return task.completed

    def get_tasks(self) -> dict[int, Task]:
        return self.tasks

    def get_stats(self) -> dict[str, int]:
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.completed)
        pending_tasks = total_tasks - completed_tasks

        # Calcular expiradas
        now = datetime.now()
        expired_tasks = sum(
            1
            for t in self.tasks.values()
            if t.due_date and not t.completed and t.due_date < now
        )

        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "expired": expired_tasks,
        }

    def save_tasks(self) -> None:
        data = {str(tid): task.model_dump() for tid, task in self.tasks.items()}
        try:
            with tempfile.NamedTemporaryFile(
                "w", delete=False, encoding="utf-8"
            ) as tmp:
                json.dump(data, tmp, indent=2, default=str)
                tmp_path = Path(tmp.name)

            shutil.move(tmp_path, self.file_path)
            logger.info(f"Saved {len(self.tasks)} tasks to {self.file_path}")
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")

    def load_tasks(self) -> None:
        if not self.file_path.exists():
            logger.info(f"No existing task file found at {self.file_path}.")
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return
                data = json.loads(content)

            for tid, task_data in data.items():
                try:
                    self.tasks[int(tid)] = Task.model_validate(task_data)
                except Exception as e:
                    logger.error(f"Failed to load task {tid}: {e}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Corrupt or invalid JSON file at {self.file_path}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error loading tasks: {e}")


manager = TaskManager()
