import gi

from src.core.config import settings
from src.core.logging import get_logger
from src.gui.components.task_list import TaskList

from pathlib import Path

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Gio  # type: ignore # noqa: E402

css_provider = None
css_monitor = None
css_path = Path(__file__).parent / "styles.css"


def load_css_file(path: Path):
    global css_provider
    display = Gdk.Display.get_default()
    if css_provider:
        try:
            Gtk.StyleContext.remove_provider_for_display(display, css_provider)
        except Exception:
            pass
    provider = Gtk.CssProvider()
    try:
        provider.load_from_path(str(path))
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        css_provider = provider
        logger.info("Loaded CSS: %s", path)
    except Exception:
        logger.exception("Failed to load CSS: %s", path)


def start_css_monitor(path: Path):
    global css_monitor
    try:
        file = Gio.File.new_for_path(str(path))
        monitor = file.monitor_file(Gio.FileMonitorFlags.NONE, None)

        def on_changed(monitor, file, other, event_type):
            if event_type in (
                Gio.FileMonitorEvent.CHANGED,
                Gio.FileMonitorEvent.CHANGES_DONE_HINT,
                Gio.FileMonitorEvent.CREATED,
            ):
                load_css_file(path)

        monitor.connect("changed", on_changed)
        css_monitor = monitor
        logger.debug("Started CSS monitor for %s", path)
    except Exception:
        logger.exception("Could not start CSS monitor for %s", path)


logger = get_logger(__name__)


def on_activate(app):
    logger.info("Activating application")
    logger.debug("Settings: app_name=%s", settings.app_name)

    try:
        if css_path.exists():
            load_css_file(css_path)
            start_css_monitor(css_path)
        else:
            logger.debug("CSS path not found: %s", css_path)
    except Exception:
        logger.exception("Error initializing CSS monitor")

    win = Gtk.ApplicationWindow(application=app)
    win.set_title(settings.app_name)
    win.set_default_size(300, 200)

    # Use TaskList component as main UI
    task_list = TaskList()
    win.set_child(task_list)

    logger.info("Presenting window")
    win.present()


def main():
    logger.info("Starting application run")
    app = Gtk.Application()
    app.connect("activate", on_activate)
    app.run(None)
