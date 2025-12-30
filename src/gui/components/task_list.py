import gi

from src.managers.task_manager import manager
from src.core.logging import get_logger

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # type: ignore # noqa: E402


logger = get_logger(__name__)


class TaskRow(Gtk.ListBoxRow):
    def __init__(self, task_id: int, task):
        super().__init__()
        self.task_id = task_id
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.set_child(hbox)

        title = getattr(task, "title", str(task))
        self.title_label = Gtk.Label(label=title)
        self.title_label.set_hexpand(True)
        hbox.append(self.title_label)

        completed = bool(getattr(task, "completed", False))
        self.toggle_btn = Gtk.CheckButton(active=completed)
        self.toggle_btn.connect("toggled", self.on_toggled)
        hbox.append(self.toggle_btn)

        remove_btn = Gtk.Button(label="Remove")
        remove_btn.connect("clicked", self.on_remove)
        hbox.append(remove_btn)

    def on_toggled(self, widget):
        try:
            manager.toggle_task_completion(self.task_id)
            logger.info("Toggled task %s", self.task_id)
        except Exception as e:
            logger.exception("Failed toggling task %s: %s", self.task_id, e)

    def on_remove(self, widget):
        try:
            manager.remove_task(self.task_id)
            parent = self.get_parent()
            if parent:
                parent.remove(self)
            logger.info("Removed task %s", self.task_id)
        except Exception as e:
            logger.exception("Failed removing task %s: %s", self.task_id, e)


class TaskList(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        controls = Gtk.Box(spacing=6)
        self.append(controls)

        self.entry = Gtk.Entry(placeholder_text="New task title")
        controls.append(self.entry)

        add_btn = Gtk.Button(label="Add")
        add_btn.connect("clicked", self.on_add)
        controls.append(add_btn)

        self.listbox = Gtk.ListBox()
        self.append(self.listbox)

        # Load persisted tasks (if any) then populate the UI
        try:
            manager.load_tasks()
        except Exception:
            logger.debug("No tasks loaded or failed to load")

        self.refresh()

    def refresh(self):
        # Recreate the ListBox to avoid relying on get_children() API
        try:
            self.remove(self.listbox)
        except Exception:
            pass
        self.listbox = Gtk.ListBox()
        self.append(self.listbox)

        tasks = manager.get_tasks()
        for task_id in sorted(tasks.keys()):
            task = tasks[task_id]
            row = TaskRow(task_id, task)
            self.listbox.append(row)

    def on_add(self, widget):
        title = (self.entry.get_text() or "").strip()
        if not title:
            return
        try:
            task = manager.add_task(title)
            # Add new row to UI
            new_id = max(manager.get_tasks().keys())
            row = TaskRow(new_id, task)
            self.listbox.append(row)
            self.entry.set_text("")
            logger.info("Added task %s", title)
        except Exception as e:
            logger.exception("Failed adding task: %s", e)
