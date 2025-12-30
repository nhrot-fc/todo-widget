import gi

from src.core.config import settings
from src.core.logging import get_logger
from src.gui.components.task_list import TaskList


gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk # type: ignore # noqa: E402


logger = get_logger(__name__)


def on_activate(app):
    logger.info("Activating application")
    logger.debug(
        "Settings: app_name=%s, opacity=%s, transparent_background=%s, decorated=%s",
        settings.app_name,
        settings.opacity,
        settings.transparent_background,
        settings.decorated,
    )

    win = Gtk.ApplicationWindow(application=app)
    win.set_title(settings.app_name)
    win.set_default_size(300, 200)
    win.set_decorated(bool(settings.decorated))
    win.set_opacity(float(settings.opacity))

    # If requested, attempt to make the background transparent via CSS
    if settings.transparent_background:
        try:
            css = b"window { background-color: rgba(0,0,0,0); }"
            provider = Gtk.CssProvider()
            provider.load_from_data(css)
            display = Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            logger.debug("Applied transparent background CSS")
        except Exception:
            logger.warning("Could not apply transparent background CSS")

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
