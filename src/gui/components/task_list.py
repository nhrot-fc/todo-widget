import gi

from src.managers.task_manager import manager
from src.core.logging import get_logger
from src.schemas.task import Task

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk  # type: ignore # noqa: E402

logger = get_logger(__name__)


class TaskRow(Gtk.ListBoxRow):
    def __init__(self, task_id, task_data: Task):
        super().__init__()
        self.task_id = task_id
        self.add_css_class("task-row")

        # Layout horizontal
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.set_child(hbox)

        # 1. Label
        self.label = Gtk.Label(label=task_data.title, xalign=0)
        self.label.add_css_class("task-label")
        self.label.set_hexpand(True)

        if task_data.completed:
            self.label.add_css_class("completed")

        hbox.append(self.label)

        # 2. Controles
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        # Botón Check
        is_done = task_data.completed
        icon_check = "" if is_done else ""
        self.check_btn = Gtk.Button(label=icon_check)
        self.check_btn.add_css_class("check-btn")
        if is_done:
            self.check_btn.add_css_class("checked")
        self.check_btn.set_has_frame(False)
        self.check_btn.connect("clicked", self.on_toggle)

        # Botón Borrar
        del_btn = Gtk.Button(label="")
        del_btn.add_css_class("delete-btn")
        del_btn.set_has_frame(False)
        del_btn.connect("clicked", self.on_delete)

        controls_box.append(self.check_btn)
        controls_box.append(del_btn)
        hbox.append(controls_box)

    def on_toggle(self, widget):
        new_state = manager.toggle_task(self.task_id)
        if new_state:
            self.label.add_css_class("completed")
            self.check_btn.add_css_class("checked")
            self.check_btn.set_label("")
        else:
            self.label.remove_css_class("completed")
            self.check_btn.remove_css_class("checked")
            self.check_btn.set_label("")
        try:
            manager.save_tasks()
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")

    def on_delete(self, widget):
        manager.remove_task(self.task_id)
        listbox = self.get_parent()
        listbox.remove(self)
        try:
            manager.save_tasks()
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")


class TaskList(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # --- Header con Input ---
        input_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_container.add_css_class("input-container")

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Add new task...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self.on_add)

        # Botón '+' Minimalista
        add_btn = Gtk.Button(label="")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self.on_add)

        input_container.append(self.entry)
        input_container.append(add_btn)
        self.append(input_container)

        # --- Lista de Tareas ---
        # ScrolledWindow permite scroll si hay muchas tareas
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)  # Ocupar resto de altura

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(
            Gtk.SelectionMode.NONE
        )  # Desactivar selección azul fea
        self.listbox.add_css_class("task-list")

        scrolled.set_child(self.listbox)
        self.append(scrolled)

        self.refresh_list()

    def refresh_list(self):
        child = self.listbox.get_first_child()
        while child:
            self.listbox.remove(child)
            child = self.listbox.get_first_child()

        tasks = manager.get_tasks()
        for t_id, t_data in tasks.items():
            row = TaskRow(t_id, t_data)
            self.listbox.append(row)

    def on_add(self, widget):
        text = self.entry.get_text().strip()
        if text:
            new_id, new_task = manager.add_task(text)
            row = TaskRow(new_id, new_task)
            self.listbox.append(row)
            self.entry.set_text("")
        try:
            manager.save_tasks()
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
