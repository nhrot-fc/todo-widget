import gi
from pathlib import Path
from src.core.config import settings
from src.core.logging import get_logger
from src.gui.components.task_list import TaskList

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio  # type: ignore

logger = get_logger(__name__)

css_provider = None
css_path = Path(__file__).parent / "styles.css"


def load_css_file(path: Path):
    global css_provider
    display = Gdk.Display.get_default()
    if not display:
        return

    if css_provider:
        Gtk.StyleContext.remove_provider_for_display(display, css_provider)

    provider = Gtk.CssProvider()
    try:
        provider.load_from_path(str(path))
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        css_provider = provider
        logger.info(f"Loaded CSS: {path}")
    except Exception as e:
        logger.error(f"Failed to load CSS {path}: {e}")


def start_css_monitor(path: Path):
    if not path.exists():
        return

    try:
        gfile = Gio.File.new_for_path(str(path))
        monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)

        def on_changed(monitor, file, other, event_type):
            if event_type in (
                Gio.FileMonitorEvent.CHANGED,
                Gio.FileMonitorEvent.CREATED,
            ):
                load_css_file(path)

        monitor.connect("changed", on_changed)
        logger.debug(f"Started CSS monitor for {path}")
    except Exception as e:
        logger.warning(f"Could not start CSS monitor: {e}")


def on_activate(app):
    logger.info("Activating application")

    if css_path.exists():
        load_css_file(css_path)
        start_css_monitor(css_path)

    win = Gtk.ApplicationWindow(application=app)
    win.set_title(settings.app_name)
    win.set_default_size(400, 600)

    task_list = TaskList()
    win.set_child(task_list)

    # Cerrar con ESC
    controller = Gtk.EventControllerKey()

    def _on_key_pressed(controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            win.close()
            return True
        return False

    controller.connect("key-pressed", _on_key_pressed)
    win.add_controller(controller)

    win.present()


def main():
    logger.info("Starting application run")
    app = Gtk.Application(application_id="com.nhrot.todowidget")
    app.connect("activate", on_activate)
    app.run(None)
