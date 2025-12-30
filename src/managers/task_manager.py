import json
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from src.core.logging import get_logger
from src.schemas.task import Task

logger = get_logger(__name__)


class TaskManager:
    def __init__(self, storage_path: str):
        self.tasks: dict[int, Task] = {}
        self.file_path = Path(storage_path)
        self._next_id_counter = 1
        self._lock = threading.Lock()
        self.load_tasks()

    def _update_next_id_counter(self):
        if self.tasks:
            self._next_id_counter = max(self.tasks.keys()) + 1
        else:
            self._next_id_counter = 1

    def _get_next_id(self) -> int:
        with self._lock:
            tid = self._next_id_counter
            self._next_id_counter += 1
            return tid

    def add_task(
        self, title: str, due_date: datetime | None = None
    ) -> tuple[int, Task]:
        task_id = self._get_next_id()
        task = Task(title=title, due_date=due_date)
        self.tasks[task_id] = task
        self._auto_save()
        logger.info(f"Added task: {task_id}")
        return task_id, task

    def update_task_title(self, task_id: int, new_title: str) -> bool:
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].title = new_title
        self._auto_save()
        return True

    def update_task_due_date(self, task_id: int, new_date: datetime | None) -> bool:
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].due_date = new_date
        self._auto_save()
        return True

    def remove_task(self, task_id: int) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._auto_save()
            logger.info(f"Removed task: {task_id}")
            return True
        return False

    def toggle_task(self, task_id: int) -> bool:
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.completed = not task.completed
            self._auto_save()
            return task.completed
        return False

    def get_tasks(self) -> dict[int, Task]:
        return self.tasks

    def get_stats(self) -> dict[str, int]:
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.completed)

        now = datetime.now()
        expired = sum(
            1
            for t in self.tasks.values()
            if t.due_date and not t.completed and t.due_date < now
        )

        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "expired": expired,
        }

    def _auto_save(self):
        self.save_tasks()

    def save_tasks(self) -> None:
        data = {str(tid): task.model_dump() for tid, task in self.tasks.items()}
        try:
            with tempfile.NamedTemporaryFile(
                "w", delete=False, encoding="utf-8"
            ) as tmp:
                json.dump(data, tmp, indent=2, default=str)
                tmp_path = Path(tmp.name)

            shutil.move(tmp_path, self.file_path)
            logger.debug(f"Saved tasks to {self.file_path}")
        except OSError as e:
            logger.error(f"IO Error saving tasks: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error saving tasks: {e}")

    def load_tasks(self) -> None:
        if not self.file_path.exists():
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return
                data = json.loads(content)

            loaded_tasks = {}
            for tid, task_data in data.items():
                try:
                    loaded_tasks[int(tid)] = Task.model_validate(task_data)
                except ValueError:
                    logger.warning(f"Skipping invalid task ID or data: {tid}")

            self.tasks = loaded_tasks
            self._update_next_id_counter()
            logger.info(f"Loaded {len(self.tasks)} tasks.")

        except json.JSONDecodeError:
            logger.error(f"Corrupt JSON file: {self.file_path}. Starting clean.")
        except Exception as e:
            logger.exception(f"Error loading tasks: {e}")
