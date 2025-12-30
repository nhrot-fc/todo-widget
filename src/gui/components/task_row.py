import gi
from datetime import datetime
from src.schemas.task import Task
from src.core.logging import get_logger

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject  # type: ignore # noqa: E402

logger = get_logger(__name__)


class TaskRow(Gtk.Box):
    __gsignals__ = {
        "task-toggled": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        "task-deleted": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        "task-updated": (GObject.SIGNAL_RUN_FIRST, None, (int, str)),  # id, new_title
        "date-changed": (
            GObject.SIGNAL_RUN_FIRST,
            None,
            (int, object),
        ),  # id, datetime (como object)
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add_css_class("task-row")

        # Estado actual (para saber ID al emitir señales)
        self.task_id = None
        self.task_data = None

        # -- UI Setup --
        self.label = Gtk.Label(xalign=0)
        self.label.add_css_class("task-label")
        self.label.set_hexpand(True)
        self.append(self.label)

        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        # Botón Fecha
        self.date_btn = Gtk.Button()
        self.date_btn.add_css_class("date-btn")
        self.date_btn.set_has_frame(False)
        self.date_btn.connect("clicked", self._on_date_click)

        # Botón Check
        self.check_btn = Gtk.Button()
        self.check_btn.add_css_class("check-btn")
        self.check_btn.set_has_frame(False)
        self.check_btn.connect("clicked", self._on_toggle_click)

        # Botón Borrar
        self.del_btn = Gtk.Button(label="")
        self.del_btn.add_css_class("delete-btn")
        self.del_btn.set_has_frame(False)
        self.del_btn.connect("clicked", self._on_delete_click)

        self.controls_box.append(self.date_btn)
        self.controls_box.append(self.check_btn)
        self.controls_box.append(self.del_btn)
        self.append(self.controls_box)

        # Gestos para editar título
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_label_pressed)
        self.label.add_controller(click)

    def bind(self, task_id: int, task: Task):
        self.task_id = task_id
        self.task_data = task
        self.label.set_text(task.title)

        if task.completed:
            self.label.add_css_class("completed")
            self.date_btn.add_css_class("completed")
            self.check_btn.add_css_class("checked")
            self.check_btn.set_label("")
        else:
            self.label.remove_css_class("completed")
            self.date_btn.remove_css_class("completed")
            self.check_btn.remove_css_class("checked")
            self.check_btn.set_label("")

        # Fecha
        date_str = task.due_date.strftime("%Y-%m-%d") if task.due_date else ""
        self.date_btn.set_label(date_str)
        is_expired = False
        if task.due_date and not task.completed and task.due_date < datetime.now():
            is_expired = True

        if is_expired:
            self.add_css_class("expired")
        else:
            self.remove_css_class("expired")

    def _on_toggle_click(self, btn):
        if self.task_id is not None:
            self.emit("task-toggled", self.task_id)

    def _on_delete_click(self, btn):
        if self.task_id is not None:
            self.emit("task-deleted", self.task_id)

    def _on_label_pressed(self, gesture, n_press, x, y):
        if n_press == 2:
            self._start_edit()

    def _start_edit(self):
        self.label.set_visible(False)
        self.edit_entry = Gtk.Entry()
        self.edit_entry.set_text(self.label.get_text())
        self.edit_entry.set_hexpand(True)
        self.edit_entry.connect("activate", self._finish_edit)

        focus_ctl = Gtk.EventControllerFocus()
        focus_ctl.connect("leave", lambda c: self._finish_edit(self.edit_entry))
        self.edit_entry.add_controller(focus_ctl)

        self.insert_child_after(self.edit_entry, self.label)
        self.edit_entry.grab_focus()

    def _finish_edit(self, widget):
        if not self.edit_entry:
            return

        new_text = self.edit_entry.get_text().strip()
        self.remove(self.edit_entry)
        self.edit_entry = None
        self.label.set_visible(True)

        if new_text and self.task_data and new_text != self.task_data.title:
            self.emit("task-updated", self.task_id, new_text)

    def _on_date_click(self, btn):
        dialog = Gtk.Window(title="Select Date")
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        dialog.set_child(box)

        cal = Gtk.Calendar()
        box.append(cal)

        btn_box = Gtk.Box(spacing=10, halign=Gtk.Align.CENTER)
        ok_btn = Gtk.Button(label="OK")

        def _on_ok(_):
            g_date = cal.get_date()
            dt = datetime(
                g_date.get_year(), g_date.get_month(), g_date.get_day_of_month()
            )
            self.emit("date-changed", self.task_id, dt)
            dialog.destroy()

        ok_btn.connect("clicked", _on_ok)
        btn_box.append(ok_btn)
        box.append(btn_box)

        dialog.present()
