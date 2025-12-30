from datetime import datetime
import json
from pathlib import Path

from src.schemas.task import Task
from src.core.config import settings
from src.core.logging import get_logger


logger = get_logger(__name__)


class TaskManager:
    def __init__(self):
        self.tasks: dict[int, Task] = {}
        self.file_path = Path(settings.storage_path)

    def _next_id(self) -> int:
        if not self.tasks:
            return 1
        return max(self.tasks.keys()) + 1

    def add_task(self, title: str, due_date: datetime | None = None) -> Task:
        task_id = self._next_id()
        task = Task(title=title, due_date=due_date)
        self.tasks[task_id] = task
        logger.info(f"Added task: {task}")
        return task

    def remove_task(self, task_id: int) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Removed task with ID: {task_id}")
            return True
        logger.warning(f"Attempted to remove non-existent task with ID: {task_id}")
        return False

    def toggle_task_completion(self, task_id: int) -> bool:
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.completed = not task.completed
            logger.info(f"Toggled completion for task ID {task_id} to {task.completed}")
            return True
        logger.warning(f"Attempted to toggle non-existent task with ID: {task_id}")
        return False

    def get_tasks(self) -> dict[int, Task]:
        return self.tasks

    def save_tasks(self) -> None:
        data = {task_id: task.model_dump_json() for task_id, task in self.tasks.items()}
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved {len(self.tasks)} tasks to {self.file_path}")

    def load_tasks(self) -> None:
        if not self.file_path.exists():
            logger.info(f"No existing task file found at {self.file_path}.")
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for id, task_data in data.items():
                task_id = int(id)
                self.tasks[task_id] = Task.model_validate_json(task_data)
        logger.info(f"Loaded {len(self.tasks)} tasks from {self.file_path}")


manager = TaskManager()
