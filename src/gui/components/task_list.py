import gi
from datetime import datetime
from src.managers.task_manager import manager
from src.core.logging import get_logger
from src.schemas.task import Task

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk  # type: ignore

logger = get_logger(__name__)


class TaskRow(Gtk.ListBoxRow):
    def __init__(self, task_id: int, task_data: Task):
        super().__init__()
        self.task_id = task_id
        self.add_css_class("task-row")

        # Contenedor principal
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.set_child(self.hbox)

        # 1. Label
        self.label = Gtk.Label(label=task_data.title, xalign=0)
        self.label.add_css_class("task-label")
        self.label.set_hexpand(True)
        self.hbox.append(self.label)

        # 2. Controles
        self.controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        # Botón Fecha
        self.date_btn = Gtk.Button()
        self.date_btn.add_css_class("date-btn")
        self.date_btn.set_has_frame(False)
        self.date_btn.connect("clicked", self.on_set_date)

        # Botón Check
        self.check_btn = Gtk.Button()
        self.check_btn.add_css_class("check-btn")
        self.check_btn.set_has_frame(False)
        self.check_btn.connect("clicked", self.on_toggle)

        # Botón Borrar
        del_btn = Gtk.Button(label="")
        del_btn.add_css_class("delete-btn")
        del_btn.set_has_frame(False)
        del_btn.connect("clicked", self.on_delete)

        self.controls_box.append(self.date_btn)
        self.controls_box.append(self.check_btn)
        self.controls_box.append(del_btn)
        self.hbox.append(self.controls_box)

        # Doble clic para editar
        click = Gtk.GestureClick()
        click.connect("pressed", self.on_label_pressed)
        self.label.add_controller(click)

        # Estado inicial
        self.update_ui_state(task_data)

    def update_ui_state(self, task: Task | None = None):
        """Actualiza todos los estilos visuales (completado, expirado, fecha)."""
        if task is None:
            task = manager.get_tasks().get(self.task_id)

        if not task:
            return

        # 1. Estado Completado
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

        # 2. Fecha
        date_label = task.due_date.strftime("%Y-%m-%d") if task.due_date else ""
        self.date_btn.set_label(date_label)

        # 3. Estado Expirado
        is_expired = False
        if task.due_date and not task.completed:
            if task.due_date < datetime.now():
                is_expired = True

        if is_expired:
            self.add_css_class("expired")
        else:
            self.remove_css_class("expired")

    def on_toggle(self, widget):
        manager.toggle_task(self.task_id)
        self.update_ui_state()
        manager.save_tasks()

    def on_delete(self, widget):
        manager.remove_task(self.task_id)
        # Eliminarse del padre (ListBox)
        parent = self.get_parent()
        if parent:
            parent.remove(self)
        manager.save_tasks()

    def on_label_pressed(self, gesture, n_press, x, y):
        if n_press == 2:  # Doble clic
            self.start_edit()

    def start_edit(self):
        # Ocultar la etiqueta pero mantenerla en el contenedor
        self.label.set_visible(False)

        self.edit_entry = Gtk.Entry()
        self.edit_entry.set_text(self.label.get_text())
        self.edit_entry.set_hexpand(True)
        self.edit_entry.connect("activate", self.finish_edit)

        # Detectar pérdida de foco para guardar también
        focus_ctl = Gtk.EventControllerFocus()
        focus_ctl.connect("leave", lambda ctl: self.finish_edit(self.edit_entry))
        self.edit_entry.add_controller(focus_ctl)

        # Insertar la entrada después de la etiqueta (API de Gtk.Box)
        self.hbox.insert_child_after(self.edit_entry, self.label)
        self.edit_entry.grab_focus()

    def finish_edit(self, widget, *args):
        try:
            new_text = self.edit_entry.get_text().strip()
        except Exception:
            # Si el widget ya fue destruido
            return

        if new_text and new_text != self.label.get_text():
            manager.edit_task_title(self.task_id, new_text)
            manager.save_tasks()
            self.label.set_text(new_text)

        self.hbox.remove(self.edit_entry)
        self.label.set_visible(True)

    def on_set_date(self, widget):
        dialog = Gtk.Dialog(title="Select date")
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "OK", Gtk.ResponseType.OK)

        root = self.get_root()
        if isinstance(root, Gtk.Window):
            dialog.set_transient_for(root)

        content = dialog.get_content_area()
        cal = Gtk.Calendar()
        content.append(cal)

        def _on_response(dlg, response_id):
            if response_id == Gtk.ResponseType.OK:
                # Gtk4 Calendar get_date retorna un GLib.DateTime
                g_date = cal.get_date()
                new_due = datetime(
                    g_date.get_year(), g_date.get_month(), g_date.get_day_of_month()
                )

                manager.edit_task_due_date(self.task_id, new_due)
                manager.save_tasks()
                self.update_ui_state()
            dlg.destroy()

        dialog.connect("response", _on_response)
        dialog.present()


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
            self.listbox.append(row)

    def on_add(self, widget):
        text = self.entry.get_text().strip()
        if text:
            new_id, new_task = manager.add_task(text)
            manager.save_tasks()

            row = TaskRow(new_id, new_task)
            self.listbox.append(row)
            self.entry.set_text("")
