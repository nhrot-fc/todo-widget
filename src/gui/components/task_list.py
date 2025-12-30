import gi

from src.managers.task_manager import manager
from src.core.logging import get_logger
from src.schemas.task import Task
from datetime import datetime

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk  # type: ignore # noqa: E402, E501

logger = get_logger(__name__)


class TaskRow(Gtk.ListBoxRow):
    def __init__(self, task_id, task_data: Task):
        super().__init__()
        self.task_id = task_id
        self.add_css_class("task-row")

        # Layout horizontal
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.set_child(hbox)
        self.hbox = hbox

        # 1. Label
        self.label = Gtk.Label(label=task_data.title, xalign=0)
        self.label.add_css_class("task-label")
        self.label.set_hexpand(True)

        if task_data.completed:
            self.label.add_css_class("completed")

        hbox.append(self.label)

        # 2. Controles
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.controls_box = controls_box

        # Botón Fecha
        date_label = (
            task_data.due_date.strftime("%Y-%m-%d") if task_data.due_date else ""
        )
        self.date_btn = Gtk.Button(label=date_label)
        self.date_btn.add_css_class("date-btn")
        self.date_btn.set_has_frame(False)
        self.date_btn.connect("clicked", self.on_set_date)

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
        controls_box.append(self.date_btn)
        controls_box.append(del_btn)
        hbox.append(controls_box)

        # Enable double-click to edit title (in-place)
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_label_pressed)
        self.label.add_controller(click)

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

    def on_label_pressed(self, gesture, n_press, x, y):
        if n_press == 2:
            self.start_edit()

    def start_edit(self):
        # Replace label with Entry for in-place edit
        try:
            self.hbox.remove(self.label)
        except Exception:
            pass
        self.edit_entry = Gtk.Entry()
        self.edit_entry.set_text(self.label.get_text())
        self.edit_entry.set_hexpand(True)
        self.edit_entry.connect("activate", self.finish_edit)
        # Use EventControllerFocus to detect leaving the entry (GTK4)
        try:
            focus_ctl = Gtk.EventControllerFocus()
            focus_ctl.connect("leave", lambda ctl: self.finish_edit(self.edit_entry))
            self.edit_entry.add_controller(focus_ctl)
        except Exception:
            pass
        self.hbox.insert_child_before(self.edit_entry, self.controls_box)
        self.edit_entry.grab_focus()

    def finish_edit(self, widget, *args):
        # widget may be Entry or event args; read text from entry
        try:
            new_text = self.edit_entry.get_text().strip()
        except Exception:
            return
        if new_text and len(new_text) > 0 and new_text != self.label.get_text():
            manager.edit_task_title(self.task_id, new_text)
            try:
                manager.save_tasks()
            except Exception as e:
                logger.error(f"Error saving tasks: {e}")
        # restore label
        try:
            self.hbox.remove(self.edit_entry)
        except Exception:
            pass
        self.label.set_text(new_text or self.label.get_text())
        self.hbox.insert_child_before(self.label, self.controls_box)

    def on_set_date(self, widget):
        # Open a simple dialog with Gtk.Calendar to pick a date
        try:
            dialog = Gtk.Dialog(title="Select date")
            dialog.add_buttons(
                "Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK
            )
            # Try to set transient parent (avoid mapping warning)
            try:
                parent = self.get_ancestor(Gtk.Window)
                if parent:
                    dialog.set_transient_for(parent)
            except Exception:
                pass

            content = dialog.get_content_area()
            cal = Gtk.Calendar()
            content.append(cal)

            def _on_response(dlg, response_id):
                if response_id == Gtk.ResponseType.OK:
                    datetime_obj = cal.get_date()
                    year, month, day = (
                        datetime_obj.get_year(),
                        datetime_obj.get_month(),
                        datetime_obj.get_day_of_month(),
                    )
                    new_due = datetime(year, month, day)
                    manager.edit_task_due_date(self.task_id, new_due)
                    try:
                        manager.save_tasks()
                    except Exception as e:
                        logger.error(f"Error saving tasks: {e}")
                    self.date_btn.set_label(new_due.strftime("%Y-%m-%d"))
                dlg.destroy()

            dialog.connect("response", _on_response)
            dialog.present()
        except Exception as e:
            logger.exception("Failed to set date: %s", e)


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
