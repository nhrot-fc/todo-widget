import gi
from datetime import datetime
from src.managers.task_manager import manager
from src.core.logging import get_logger

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk  # type: ignore

logger = get_logger(__name__)

from src.gui.components.task_row import TaskRow


class TaskList(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header
        input_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_container.add_css_class("input-container")

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Add new task...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self.on_add)

        add_btn = Gtk.Button(label="")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self.on_add)

        input_container.append(self.entry)
        input_container.append(add_btn)
        self.append(input_container)

        # List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class("task-list")

        scrolled.set_child(self.listbox)
        self.append(scrolled)
        self.refresh_list()

    def refresh_list(self):
        while True:
            child = self.listbox.get_first_child()
            if not child:
                break
            self.listbox.remove(child)

        tasks = manager.get_tasks()
        sorted_tasks = sorted(
            tasks.items(), key=lambda x: (x[1].completed, x[1].due_date or datetime.max)
        )

        for t_id, t_data in sorted_tasks:
            row = TaskRow(t_id, t_data)
            row.connect("refresh", lambda w: self.refresh_list())
            self.listbox.append(row)

    def on_add(self, widget):
        text = self.entry.get_text().strip()
        if text:
            new_id, new_task = manager.add_task(text)
            manager.save_tasks()

            row = TaskRow(new_id, new_task)
            row.connect("refresh", lambda w: self.refresh_list())
            self.listbox.append(row)
            self.entry.set_text("")
            self.refresh_list()
