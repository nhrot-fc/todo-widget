import gi
from pathlib import Path
from src.core.config import settings
from src.core.logging import get_logger
from src.gui.components.task_list import TaskList

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio  # type: ignore # noqa: E402

logger = get_logger(__name__)


class TodoApp:
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.app = Gtk.Application(application_id="com.nhrot.todowidget")
        self.app.connect("activate", self.on_activate)

        self.css_provider = None
        self.css_path = Path(__file__).parent / "styles.css"
        self.window = None

    def load_css(self):
        display = Gdk.Display.get_default()
        if not display:
            return

        if self.css_provider:
            Gtk.StyleContext.remove_provider_for_display(display, self.css_provider)

        self.css_provider = Gtk.CssProvider()
        try:
            self.css_provider.load_from_path(str(self.css_path))
            Gtk.StyleContext.add_provider_for_display(
                display, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            logger.info(f"Loaded CSS: {self.css_path}")
        except Exception as e:
            logger.error(f"Failed to load CSS: {e}")

    def on_activate(self, app):
        logger.info("Activating application")

        if self.window:
            self.window.present()
            return

        if self.css_path.exists():
            self.load_css()

        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title(settings.app_name)
        self.window.set_default_size(450, 600)

        task_list = TaskList(self.task_manager)
        self.window.set_child(task_list)
        controller = Gtk.EventControllerKey()

        def _on_key_pressed(controller, keyval, keycode, state):
            if keyval == Gdk.KEY_Escape and self.window:
                self.window.close()
                return True
            return False

        controller.connect("key-pressed", _on_key_pressed)
        self.window.add_controller(controller)

        self.window.present()

    def run(self):
        self.app.run(None)
