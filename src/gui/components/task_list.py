import gi
from datetime import datetime
from src.core.logging import get_logger
from src.gui.components.task_row import TaskRow

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GObject  # type: ignore # noqa: E402

logger = get_logger(__name__)


class TaskObject(GObject.Object):
    def __init__(self, task_id, task_data):
        super().__init__()
        self.task_id = task_id
        self.task = task_data


class TaskList(Gtk.Box):
    def __init__(self, task_manager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.manager = task_manager

        input_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_container.add_css_class("input-container")

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Add new task...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self._on_add_task)

        add_btn = Gtk.Button(label="")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_task)

        input_container.append(self.entry)
        input_container.append(add_btn)
        self.append(input_container)

        self.store = Gio.ListStore(item_type=TaskObject)
        self.selection_model = Gtk.NoSelection(model=self.store)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        self.list_view = Gtk.ListView(model=self.selection_model, factory=factory)
        self.list_view.add_css_class("task-list")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.list_view)
        self.append(scrolled)

        self.reload_tasks()

    def reload_tasks(self):
        self.store.remove_all()
        tasks = self.manager.get_tasks()

        sorted_items = sorted(
            tasks.items(), key=lambda x: (x[1].completed, x[1].due_date or datetime.max)
        )

        for tid, tdata in sorted_items:
            self.store.append(TaskObject(tid, tdata))

    def _on_add_task(self, widget):
        text = self.entry.get_text().strip()
        if text:
            self.manager.add_task(text)
            self.entry.set_text("")
            self.reload_tasks()

    def _on_factory_setup(self, factory, list_item):
        row = TaskRow()
        row.connect("task-toggled", self._handle_toggle)
        row.connect("task-deleted", self._handle_delete)
        row.connect("task-updated", self._handle_update)
        row.connect("date-changed", self._handle_date)
        list_item.set_child(row)

    def _on_factory_bind(self, factory, list_item):
        row = list_item.get_child()
        task_obj = list_item.get_item()
        row.bind(task_obj.task_id, task_obj.task)

    def _handle_toggle(self, widget, task_id):
        self.manager.toggle_task(task_id)
        self.reload_tasks()

    def _handle_delete(self, widget, task_id):
        self.manager.remove_task(task_id)
        self.reload_tasks()

    def _handle_update(self, widget, task_id, new_title):
        self.manager.update_task_title(task_id, new_title)
        self.reload_tasks()

    def _handle_date(self, widget, task_id, new_date):
        self.manager.update_task_due_date(task_id, new_date)
        self.reload_tasks()
