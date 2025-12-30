from datetime import datetime
from pydantic import BaseModel


class Task(BaseModel):
    title: str
    completed: bool = False
    due_date: datetime | None = None
