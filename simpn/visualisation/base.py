"""
Base visualisation components for SimPN.

This module provides the core Qt-based GUI components for visualizing simulations,
including the main window, pygame integration, and various UI panels.

Classes:
    PygameWidget: Qt widget that embeds a pygame surface for rendering the simulation.
    DebugPanel: Panel for displaying debug messages and logs.
    AttributePanel: Panel for displaying properties of selected simulation elements.
    MainWindow: Main application window containing all visualization components.
    Visualisation: Main class for starting visualisations.
"""

import enum
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
import sys
from pathlib import Path
from PyQt6.QtCore import Qt, QSize, QSettings, QStandardPaths, QTimer
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QIcon,
    QPainter,
    QColor,
    QMouseEvent,
    QWheelEvent,
    QActionGroup,
)
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QDockWidget,
    QToolBar,
    QSizePolicy,
    QApplication,
    QFileDialog,
)
from simpn.visualisation.model_panel_mods import (
    ClockModule,
    FiredTrackerModule,
    NodeHighlightingModule,
)
from simpn.visualisation.model_panel import ModelPanel
from simpn.visualisation.events import (
    register_handler,
    unregister_handler,
    check_event,
    create_event,
    dispatch,
    listen_to,
    reset_dispatcher,
    EventType,
    Event,
)
from simpn.visualisation.constants import GREEN

from typing import List, Tuple, TYPE_CHECKING, Literal, Union

if TYPE_CHECKING:
    from simpn.simulator import Describable
    from simpn.visualisation.model_panel import Node


TOOLBAR_STYLESHEET = """
            QToolBar {
                spacing: 8px;
                padding: 4px;
            }
            QToolButton {
                max-width: 12px;
                max-height: 12px;
                padding: 4px;
                margin: 2px;
                opacity: 0.7;
            }
        """


def create_colored_pixmap(file_path: str, color: QColor) -> QPixmap:
    """
    Create a colored pixmap from an image file using a specific color.

    :param file_path: Path to the source image file
    :param color: QColor to apply to the icon
    :return: QPixmap with the specified color applied
    """
    if not os.path.exists(file_path):
        return QPixmap()

    original_pixmap = QPixmap(file_path)
    colored_pixmap = QPixmap(original_pixmap.size())
    colored_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(colored_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.drawPixmap(0, 0, original_pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(colored_pixmap.rect(), color)
    painter.end()

    return colored_pixmap


def create_monochrome_icon_from_file(file_path) -> QIcon:
    """
    Create a monochrome (dark gray) icon from an image file.

    :param file_path: Path to the image file
    :return: QIcon with monochrome rendering
    """
    if not os.path.exists(file_path):
        return QIcon()

    icon = QIcon()

    # Detect if we're in dark mode
    palette = QApplication.instance().palette()
    window_color = palette.color(palette.ColorRole.Window)
    is_dark_theme = window_color.lightness() < 128

    # normal state
    if is_dark_theme:
        mono_pixmap = create_colored_pixmap(file_path, QColor(255, 255, 255))
    else:
        mono_pixmap = create_colored_pixmap(file_path, QColor(10, 10, 10))
    icon.addPixmap(mono_pixmap, QIcon.Mode.Normal, QIcon.State.Off)

    # disabled state
    mono_pixmap_disabled = create_colored_pixmap(file_path, QColor(150, 150, 150))
    icon.addPixmap(mono_pixmap_disabled, QIcon.Mode.Disabled, QIcon.State.Off)

    # hovered state
    mono_pixmap_hovered = create_colored_pixmap(file_path, QColor(*GREEN))
    icon.addPixmap(mono_pixmap_hovered, QIcon.Mode.Active, QIcon.State.Off)

    return icon


def get_preferences_directory() -> Path:
    """
    Get the cross-platform preferences directory for SimPN.
    Creates the directory if it doesn't exist.

    Returns:
        Path: The preferences directory path

    The directory location depends on the platform:
    - macOS: ~/Library/Application Support/TUe/SimPN
    - Windows: C:/Users/<username>/AppData/Local/TUe/SimPN
    - Linux: ~/.local/share/TUe/SimPN
    """
    # Use QStandardPaths to get the appropriate location for the platform
    app_data_location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )

    if not app_data_location:
        # Fallback to home directory if QStandardPaths fails
        app_data_location = os.path.join(os.path.expanduser("~"), ".simpn")

    prefs_dir = Path(app_data_location)

    # Create the directory if it doesn't exist
    prefs_dir.mkdir(parents=True, exist_ok=True)

    return prefs_dir


class SimulationPanel(QWidget):
    """
    Qt widget that embeds a pygame surface for rendering simulation visualizations.

    This widget bridges pygame rendering with Qt's widget system by converting pygame
    surfaces to QPixmap images. It handles mouse events and forwards them to the
    underlying pygame ModelPanel for interaction.

    :param width: Initial width of the pygame surface (default: 640)
    :param height: Initial height of the pygame surface (default: 480)
    :param parent: Parent Qt widget (default: None)
    """

    def __init__(self, width=640, height=480, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        pygame.init()
        pygame.font.init()
        self.setMinimumSize(width, height)
        self._panel = None  # Will hold the ModelPanel instance

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Create toolbar
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)

        # Create display label for pygame surface
        self.display_label = QLabel()
        self.display_label.setMinimumSize(width, height)
        self.display_label.setMouseTracking(True)
        main_layout.addWidget(self.display_label)

        # Enable mouse tracking on the widget itself
        self.setMouseTracking(True)

        self._display_timer = QTimer(self)
        self._display_timer.timeout.connect(self.trigger_update)
        self._display_timer.start(33)  # ~30 FPS

        # Initialize simulation control variables
        self._playing = False
        self._play_step_delay = 500  # milliseconds between steps

        # Create timers for play mode and display updates
        self._play_timer = QTimer(self)
        self._play_timer.timeout.connect(self.step_simulation)
        self._play_timer.setInterval(self._play_step_delay)

        listen_to(EventType.SIM_RENDERED, self.update_display)

    def _create_toolbar(self):
        """Create and configure the toolbar with simulation controls."""
        toolbar = QToolBar("Simulation Controls")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(TOOLBAR_STYLESHEET)

        # Add Step button to toolbar
        self.step_action = toolbar.addAction("Step")
        self.step_action.setToolTip("Execute one simulation step")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_step.png"
        )
        self.step_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.step_action.triggered.connect(self.step_simulation)
        self.step_action.setEnabled(False)

        # Add Play button to toolbar
        self.play_action = toolbar.addAction("Play")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_play.png"
        )
        self.play_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.play_action.setToolTip("Start continuous simulation")
        self.play_action.triggered.connect(self.start_simulation)
        self.play_action.setEnabled(False)

        # Add Stop button to toolbar
        self.stop_action = toolbar.addAction("Stop")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_stop.png"
        )
        self.stop_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.stop_action.setToolTip("Stop continuous simulation")
        self.stop_action.triggered.connect(self.stop_simulation)
        self.stop_action.setEnabled(False)

        # Add reset to start to toolbar
        self.reset_action = toolbar.addAction("Reset to Start")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "time_back.png"
        )
        self.reset_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.reset_action.setToolTip("Reset simulation to start")
        self.reset_action.triggered.connect(self.reset_simulation)
        self.reset_action.setEnabled(False)

        # Add Faster button to toolbar
        self.faster_action = toolbar.addAction("Faster")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_faster.png"
        )
        self.faster_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.faster_action.setToolTip("Increase simulation speed")
        self.faster_action.triggered.connect(self.faster_simulation)
        self.faster_action.setEnabled(False)

        # Add Slower button to toolbar
        self.slower_action = toolbar.addAction("Slower")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_slower.png"
        )
        self.slower_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.slower_action.setToolTip("Decrease simulation speed")
        self.slower_action.triggered.connect(self.slower_simulation)
        self.slower_action.setEnabled(False)

        # Add separator
        toolbar.addSeparator()

        # Add Zoom In button to toolbar
        self.zoom_in_action = toolbar.addAction("Zoom In")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "zoom-in.png"
        )
        self.zoom_in_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_in_action.setEnabled(False)
        self.addAction(self.zoom_in_action)

        # Add Zoom Out button to toolbar
        self.zoom_out_action = toolbar.addAction("Zoom Out")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "zoom-out.png"
        )
        self.zoom_out_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.zoom_out_action.setEnabled(False)
        self.addAction(self.zoom_out_action)

        # Add Zoom Reset button to toolbar
        self.zoom_reset_action = toolbar.addAction("Zoom 100%")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "zoom-reset.png"
        )
        self.zoom_reset_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.zoom_reset_action.setToolTip("Reset zoom to 100% (Ctrl+0)")
        self.zoom_reset_action.setShortcut("Ctrl+0")
        self.zoom_reset_action.triggered.connect(self.zoom_reset)
        self.zoom_reset_action.setEnabled(False)
        self.addAction(self.zoom_reset_action)

        # Add separator
        toolbar.addSeparator()

        # Add clock precision increase button to toolbar
        self.clock_increase_action = toolbar.addAction("Clock precision +")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "plus.png"
        )
        self.clock_increase_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.clock_increase_action.setToolTip("Increase clock precision")
        self.clock_increase_action.triggered.connect(self.increase_clock_precision)
        self.clock_increase_action.setEnabled(False)

        # Add clock precision decrease button to toolbar
        self.clock_decrease_action = toolbar.addAction("Clock precision -")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "minus.png"
        )
        self.clock_decrease_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.clock_decrease_action.setToolTip("Decrease clock precision")
        self.clock_decrease_action.triggered.connect(self.decrease_clock_precision)
        self.clock_decrease_action.setEnabled(False)

        return toolbar

    def enable_controls(self, enabled=True):
        """
        Enable or disable all toolbar controls.

        :param enabled: True to enable, False to disable
        """
        self.step_action.setEnabled(enabled)
        self.play_action.setEnabled(enabled)
        self.reset_action.setEnabled(enabled)
        self.faster_action.setEnabled(enabled)
        self.slower_action.setEnabled(enabled)
        self.zoom_in_action.setEnabled(enabled)
        self.zoom_out_action.setEnabled(enabled)
        self.zoom_reset_action.setEnabled(enabled)
        self.clock_increase_action.setEnabled(enabled)
        self.clock_decrease_action.setEnabled(enabled)

    def step_simulation(self) -> bool:
        """
        Execute one step of the simulation and update the display.
        """
        dispatch(create_event(EventType.SIM_PLAY), self)
        return True

    def start_simulation(self):
        """
        Start continuous simulation playback.

        Enables the play timer which executes simulation steps at regular intervals
        determined by _play_step_delay. Updates UI button states appropriately.
        """
        if not self._playing:
            self._playing = True
            self.play_action.setEnabled(False)
            self.step_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            self.reset_action.setEnabled(False)
            self._play_timer.start()

    def stop_simulation(self):
        """
        Stop continuous simulation playback.

        Stops the play timer and re-enables step and reset buttons.
        """
        if self._playing:
            self._playing = False
            self.play_action.setEnabled(True)
            self.step_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            self.reset_action.setEnabled(True)
            self._play_timer.stop()

    def reset_simulation(self):
        """Reset the simulation to the initial state."""
        dispatch(create_event(EventType.SIM_RESET_SIM_STATE), self)

    def faster_simulation(self):
        """Increase simulation speed by decreasing delay."""
        self._play_step_delay = max(100, self._play_step_delay - 100)
        self._play_timer.setInterval(self._play_step_delay)

    def slower_simulation(self):
        """Decrease simulation speed by increasing delay."""
        self._play_step_delay = min(1000, self._play_step_delay + 100)
        self._play_timer.setInterval(self._play_step_delay)

    def zoom_in(self):
        """Zoom in on the visualization by increasing the zoom level."""
        dispatch(create_event(EventType.SIM_ZOOM, action="increase"), self)

    def zoom_out(self):
        """Zoom out on the visualization by decreasing the zoom level."""
        dispatch(create_event(EventType.SIM_ZOOM, action="decrease"), self)

    def zoom_reset(self):
        """Reset zoom level to 100% (1.0x scale)."""
        dispatch(create_event(EventType.SIM_ZOOM, action="reset"), self)

    def increase_clock_precision(self):
        """
        Increase the number of decimal places shown in the simulation clock.
        """
        dispatch(create_event(EventType.CLOCK_PREC_INC), self)

    def decrease_clock_precision(self):
        """
        Decrease the number of decimal places shown in the simulation clock.
        """
        dispatch(create_event(EventType.CLOCK_PREC_DEC), self)

    def set_panel(self, panel: ModelPanel):
        """
        Set the model panel to render in this widget.

        :param panel: The ModelPanel instance to visualize
        """
        self._panel = panel

    def get_panel(self):
        """
        Get the current model panel being rendered.

        :return: The current ModelPanel instance or None
        """
        return self._panel

    def trigger_update(self) -> bool:
        """
        Trigger to repaint the underlying pygame surface for the
        simulation.
        """
        dispatch(create_event(EventType.SIM_UPDATE), self)
        return True

    def update_display(self, event: Event):
        """
        Convert the pygame surface to QPixmap and update the display.

        If a model panel is set, it will be rendered to the pygame surface first,
        then the surface is converted to a Qt-compatible image format.
        """
        if event:
            surface = getattr(event, "window")
            # Get the pygame surface as a string buffer
            data = pygame.image.tostring(surface, "RGB")
            # Create QImage from the data
            image = QImage(
                data,
                self.width,
                self.height,
                self.width * 3,
                QImage.Format.Format_RGB888,
            )
            # Convert to QPixmap and display
            self.display_label.setPixmap(QPixmap.fromImage(image))
        return True

    def resizeEvent(self, event):
        """
        Handle widget resize events and update the pygame surface accordingly.

        :param event: Qt resize event
        """
        super().resizeEvent(event)
        # Update the surface size to match the widget size
        new_width = self.width
        new_height = self.height
        if event.size().width() > 0 and event.size().height() > 0:
            # Account for toolbar height
            toolbar_height = self.toolbar.sizeHint().height()
            new_width = event.size().width()
            new_height = event.size().height() - toolbar_height

        # Only resize if dimensions actually changed
        if new_width != self.width or new_height != self.height:
            self.width = new_width
            self.height = new_height
            # Create a new surface with the new size
            dispatch(
                create_event(
                    EventType.SIM_RESIZE, width=self.width, height=self.height
                ),
                self,
            )
            # Update the display immediately
            dispatch(create_event(EventType.SIM_UPDATE), self)

    def mousePressEvent(self, event: QMouseEvent):
        """
        Handle mouse press events and forward to the model panel.

        :param event: Qt mouse press event
        """
        # Adjust y coordinate for toolbar
        toolbar_height = self.toolbar.sizeHint().height()
        x = int(event.position().x())
        y = int(event.position().y()) - toolbar_height

        if y >= 0:  # Only process if click is below toolbar
            dispatch(
                create_event(EventType.SIM_PRESS, pos=(x, y), button=event.button()),
                self,
            )
            dispatch(
                create_event(
                    EventType.SIM_CLICK, pos={"x": x, "y": y}, button=event.button()
                ),
                self,
            )

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Handle mouse release events and forward to the model panel.

        :param event: Qt mouse release event
        """
        # Adjust y coordinate for toolbar
        toolbar_height = self.toolbar.sizeHint().height()
        x = int(event.position().x())
        y = int(event.position().y()) - toolbar_height
        
        if y >= 0:  # Only process if release is below toolbar
            dispatch(
                create_event(EventType.SIM_RELEASE, pos=(x, y), button=event.button()),
                self,
            )
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Handle mouse move events and forward to the model panel.

        :param event: Qt mouse move event
        """
        # Adjust y coordinate for toolbar
        toolbar_height = self.toolbar.sizeHint().height()
        x = int(event.position().x())
        y = int(event.position().y()) - toolbar_height
        
        if y >= 0:  # Only process if move is below toolbar
            if event.buttons():
                dispatch(
                    create_event(EventType.SIM_MOVE, pos=(x, y)),
                    self,
                )
            else:
                dispatch(
                    create_event(EventType.SIM_HOVER, pos=(x, y)),
                    self,
                )
        super().mouseMoveEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """
        Handle mouse wheel events by forwarding zoom events to the model panel.

        :param event: Qt wheel event
        """
        if self._panel is not None:
            # Get the angle delta (positive = scroll up = zoom in)
            delta = event.angleDelta().y()
            action = None

            if delta > 0:
                action = "increase"
            else:
                action = "decrease"

            dispatch(create_event(EventType.SIM_ZOOM, action=action), self)
            dispatch(create_event(EventType.SIM_UPDATE), self)

        super().wheelEvent(event)

    def closeEvent(self, event):
        self._display_timer.stop()
        self._play_timer.stop()
        event.accept()


class DebugPanel(QWidget):
    """
    Debug panel for displaying textual debugging information and logs.

    This panel provides methods to write text messages with different severity levels
    (normal, error, warning, success) and supports HTML formatting for colored output.

    :param parent: Parent Qt widget (default: None)
    """

    class DebugLevel(enum.Enum):
        INFO = 1
        WARNING = 2
        ERROR = 3

    def __init__(self, parent=None, debug_level=DebugLevel.WARNING):
        super().__init__(parent)

        self._selected = None
        self._description = None
        self._debug_level = debug_level

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setLayout(layout)

        # Create toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        # Text area for debug messages
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.setMinimumHeight(100)

    def _create_toolbar(self):
        """Create and configure the toolbar for the debug panel."""
        toolbar = QToolBar("Debug Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(TOOLBAR_STYLESHEET)

        # Add title label to toolbar
        title_label = QLabel("  Debug Console")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        toolbar.addWidget(title_label)

        # Add spacer to push buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Clear button with icon
        clear_action = toolbar.addAction("Clear")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "clear.png"
        )
        clear_action.setIcon(create_monochrome_icon_from_file(icon_path))
        clear_action.setToolTip("Clear debug console")
        clear_action.triggered.connect(self.clear_text)

        # Close button with icon
        self.close_action = toolbar.addAction("Close")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "close.png"
        )
        self.close_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.close_action.setToolTip("Close debug console")
        # Note: close action will be connected by parent to hide the dock

        return toolbar

    def write_text(self, text, color=None):
        """
        Write normal text to the debug panel.

        :param text: Text to display
        """
        html_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        if color:
            self.text_edit.append(f'<span style="color: {color};">{html_text}</span>')
        else:
            self.text_edit.append(html_text)

    def write_error(self, text):
        """
        Write error text in red to the debug panel.

        :param text: Error message to display
        """
        self.write_text(text, color="red")

    def write_warning(self, text):
        """
        Write warning text in orange to the debug panel.

        :param text: Warning message to display
        """
        if self._debug_level in [self.DebugLevel.WARNING]:
            self.write_text(text, color="orange")

    def write_info(self, text):
        """
        Write informational text in blue to the debug panel.

        :param text: Informational message to display
        """
        if self._debug_level == self.DebugLevel.INFO:
            self.write_text(text, color="black")

    def clear_text(self):
        """Clear all text from the debug panel."""
        self.text_edit.clear()

    def listen_to(self):
        """
        Specify which event types this handler listens to.

        :return: Empty list (DebugPanel doesn't listen to events by default)
        """
        return [EventType.ALL]  # DebugPanel listens to all events for logging

    def handle_event(self, event: pygame.event.Event) -> bool:
        if check_event(event, EventType.DEBUG_LEVEL):
            self._debug_level = event.level
        if not check_event(event, EventType.RENDER_UI):
            self.write_info(f"[EventQue] {str(event)}")
        return True


class AttributePanel(QWidget):
    """
    Attribute panel for displaying properties and descriptions of simulation elements.

    This panel listens to visualization events (node clicks, bindings fired) and updates
    to show the relevant information about the selected element. It displays descriptions
    using HTML formatting with support for headings, normal text, boxed content, and bold text.

    Implements the IEventHandler interface to receive visualization events.

    :param parent: Parent Qt widget (default: None)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected = None
        self._description = None

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setLayout(layout)

        # Create toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)

        # Text area for attributes
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Select an object to view attributes...")
        layout.addWidget(self.text_edit)

        self.setMinimumWidth(200)

    def _create_toolbar(self):
        """Create and configure the toolbar for the attribute panel."""
        toolbar = QToolBar("Attribute Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(TOOLBAR_STYLESHEET)

        # Add title label to attribute toolbar
        title_label = QLabel("  Attributes")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        toolbar.addWidget(title_label)

        # Add spacer to push close button to the right
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        toolbar.addWidget(spacer)

        # Close button with icon
        self.close_action = toolbar.addAction("Close")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "close.png"
        )
        self.close_action.setIcon(create_monochrome_icon_from_file(icon_path))
        self.close_action.setToolTip("Close attribute panel")
        # Note: close action will be connected by parent to hide the dock

        return toolbar

    def set_attributes(self, attributes_dict):
        """
        Set and display attributes from a dictionary.

        :param attributes_dict: Dictionary mapping attribute names to values
        """
        text = ""
        for key, value in attributes_dict.items():
            text += f"<b>{key}:</b> {value}<br>"
        self.text_edit.setHtml(text)

    def _clear_attributes_ui(self):
        """Clear the text in the attribute panel."""
        self.text_edit.clear()

    def _clear_description_ui(self):
        """Clear the description in the attribute panel."""
        self.text_edit.clear()

    def _update_selected(self, selected: "Node"):
        """
        Update the selected node for the attribute panel.

        :param selected: The selected visualization node (not the model node)
        """
        self._selected = selected
        # Immediately fetch and display the description when a node is selected
        if self._selected is not None and hasattr(self._selected, "_model_node"):
            description = self._selected._model_node.get_description()
            self._update_description_ui(description)
        else:
            self._clear_description_ui()

    def _refresh(self):
        """
        Refresh the attribute panel by updating it with the current selected object's description.
        """
        if self._selected is not None:
            des = self._selected._model_node.get_description()
            self._update_description_ui(des)

    def _update_description_ui(
        self, description: List[Tuple[str, "Describable.Style"]]
    ):
        """
        Update the UI with a formatted description using HTML.

        Formats the description according to the style specified for each section:
        - HEADING: Rendered as h2
        - NORMAL: Rendered as paragraph
        - BOXED: Rendered in a table cell with border
        - BOLD: Rendered as bold paragraph

        :param description: List of tuples containing (text, style) where style determines formatting
        """
        from simpn.simulator import Describable

        self._description = description
        panel_text = """<head>
        <style> 
        table {
            margin-left: 20px;
        }

        td {
            border: 1px solid gray;
            padding: 5px;
            margin: 5px;
        }
        </style>
        </head>
        <body>
        <main>"""

        for text, style in description:
            if style == Describable.Style.HEADING:
                panel_text += f"<h2>{text}</h2>"
            elif style == Describable.Style.NORMAL:
                panel_text += f"<p>{text}</p>"
            elif style == Describable.Style.BOXED:
                panel_text += f"""<table><tr><td>{text}</td></tr></table>"""
            elif style == Describable.Style.BOLD:
                panel_text += f"<p><b>{text}</b></p>"
            else:
                panel_text += text

        panel_text += "</main></body>"
        self.text_edit.setHtml(panel_text)

    def listen_to(self):
        """
        Specify which event types this handler listens to.

        :return: List of event types (NODE_CLICKED, BINDING_FIRED, SELECTION_CLEAR)
        """
        return [
            EventType.NODE_CLICKED,
            EventType.BINDING_FIRED,
            EventType.SELECTION_CLEAR,
            EventType.DES_POST,
        ]

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a pygame event to update the attribute panel display.

        Responds to:
        - NODE_CLICKED: Updates panel to show clicked node's attributes
        - BINDING_FIRED: Refreshes panel to reflect simulation state changes
        - SELECTION_CLEAR: Clears the attribute display

        :param event: The pygame event to handle
        :return: True to propagate event to other handlers
        """
        if check_event(event, EventType.NODE_CLICKED):
            self._update_selected(event.node)
        if check_event(event, EventType.DES_POST):
            self._update_description_ui(event.description)
        elif check_event(event, EventType.BINDING_FIRED):
            self._refresh()
        elif check_event(event, EventType.SELECTION_CLEAR):
            self._update_selected(None)
            self._clear_attributes_ui()
        return True


class MainWindow(QMainWindow):
    """
    Main application window for the SimPN visualization system.

    Provides a complete IDE-like interface for simulations with:
    - PygameWidget with embedded toolbar containing simulation controls (play, step, stop, 
      reset, speed adjustment), zoom controls, and clock precision controls
    - Dockable debug console and attribute panel
    - File menu for loading BPMN files (in application mode)
    - Qt timer-based simulation execution to avoid threading issues

    The window can operate in two modes:
    - Application mode: Includes file menu to load BPMN files
    - Embedded mode: Expects a simulation to be set programmatically
    """

    def __init__(self, as_application=False):
        """
        Initialize the main window.

        :param as_application: If True, enables application mode with file menu (default: False)
        """
        super().__init__()
        reset_dispatcher()
        self._as_application = as_application
        self._playing = False

        # Set up the main window
        self.setWindowTitle("SimPN")
        self.setGeometry(100, 100, 800, 600)

        # Set window icon
        logo_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "logo.png"
        )
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        # Create pygame widget
        self.simulation_panel = SimulationPanel(640, 480)

        # Add the Pygame widget to the main window
        self.setCentralWidget(self.simulation_panel)

        # Create debug panel as a dock widget
        self.debug_dock = QDockWidget("Debug Console", self)
        self.debug_dock.setObjectName("Debug Console")  # Required for saveState()
        self.debug_panel = DebugPanel()
        self.debug_dock.setWidget(self.debug_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.debug_dock)
        
        # Connect the close action from the debug panel's toolbar
        self.debug_panel.close_action.triggered.connect(self.debug_dock.hide)
        
        # Use the debug panel's toolbar as the title bar widget
        self.debug_dock.setTitleBarWidget(self.debug_panel.toolbar)

        # Create attribute panel as a dock widget
        self.attribute_dock = QDockWidget("Attributes", self)
        self.attribute_dock.setObjectName("Attributes")  # Required for saveState()
        self.attribute_panel = AttributePanel()
        self.attribute_dock.setWidget(self.attribute_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.attribute_dock)
        
        # Connect the close action from the attribute panel's toolbar
        self.attribute_panel.close_action.triggered.connect(self.attribute_dock.hide)
        
        # Use the attribute panel's toolbar as the title bar widget
        self.attribute_dock.setTitleBarWidget(self.attribute_panel.toolbar)

        # Create menu bar
        self.create_menus()

        # Keep settings between sessions
        self.settings = QSettings("TUe", "SimPN")
        self.last_dir = os.path.expanduser("~")  # Initialize with default value
        self.restoreSettings()
    
    def saveSettings(self):
        """
        Save the current window settings (size, position, dock states).
        """
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("lastDir", self.last_dir)
    
    def restoreSettings(self):
        """
        Restore the window settings (size, position, dock states) from previous session.
        """
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
        self.last_dir = self.settings.value("lastDir", os.path.expanduser("~"))

    def create_menus(self):
        """
        Create the menu bar with File and View menus.

        File menu (application mode only): Contains "Open BPMN File" action
        View menu: Contains toggles for debug and attribute panels, plus layout reset
        """
        menubar = self.menuBar()

        # File menu
        if self._as_application:
            file_menu = menubar.addMenu("File")
            open_action = file_menu.addAction("Open BPMN File...")
            open_action.setToolTip("Open a BPMN file")
            open_action.triggered.connect(self.open_bpmn_file)

        # Window menu
        window_menu = menubar.addMenu("View")

        # Debug View action
        self.debug_view_action = window_menu.addAction("Debug View")
        self.debug_view_action.setCheckable(True)
        self.debug_view_action.setChecked(True)  # Initially visible
        self.debug_view_action.triggered.connect(self.toggle_debug_panel)

        # Attribute View action
        self.attribute_view_action = window_menu.addAction("Attribute View")
        self.attribute_view_action.setCheckable(True)
        self.attribute_view_action.setChecked(True)  # Initially visible
        self.attribute_view_action.triggered.connect(self.toggle_attribute_panel)

        # Connect the dock widgets' visibility changed signals to update the menu checkmarks
        self.debug_dock.visibilityChanged.connect(
            self.on_debug_panel_visibility_changed
        )
        self.attribute_dock.visibilityChanged.connect(
            self.on_attribute_panel_visibility_changed
        )

        # Add a separator
        window_menu.addSeparator()

        # Layout action
        layout_action = window_menu.addAction("Reset Layout")
        layout_action.triggered.connect(self.reset_layout)

        # add help section
        help_menu = menubar.addMenu("Help")

        help_debug_menu = help_menu.addMenu("debug level")
        help_debug_group = QActionGroup(self)
        help_debug_group.setExclusive(True)
        help_debug_menu.setToolTip("Updates the debug level for the debug panel.")
        
        help_debug_low_menu = help_debug_menu.addAction("ERROR")
        help_debug_low_menu.setCheckable(True)
        help_debug_low_menu.setChecked(True)
        help_debug_low_menu.setActionGroup(help_debug_group)
        help_debug_low_menu.setData(DebugPanel.DebugLevel.ERROR)

        help_debug_med_menu = help_debug_menu.addAction("WARNING")
        help_debug_med_menu.setCheckable(True)
        help_debug_med_menu.setActionGroup(help_debug_group)
        help_debug_med_menu.setData(DebugPanel.DebugLevel.WARNING)

        help_debug_all_menu = help_debug_menu.addAction("INFO")
        help_debug_all_menu.setCheckable(True)
        help_debug_all_menu.setActionGroup(help_debug_group)
        help_debug_all_menu.setData(DebugPanel.DebugLevel.INFO)

        help_debug_group.triggered.connect(
            lambda action: dispatch(
                create_event(EventType.DEBUG_LEVEL, level=action.data()),
                self
            )
        )

    def toggle_debug_panel(self):
        """Toggle the visibility of the debug panel"""
        if self.debug_dock.isVisible():
            self.debug_dock.hide()
        else:
            self.debug_dock.show()

    def on_debug_panel_visibility_changed(self, visible):
        """Update the menu checkmark when the debug panel visibility changes"""
        self.debug_view_action.setChecked(visible)

    def toggle_attribute_panel(self):
        """Toggle the visibility of the attribute panel"""
        if self.attribute_dock.isVisible():
            self.attribute_dock.hide()
        else:
            self.attribute_dock.show()

    def on_attribute_panel_visibility_changed(self, visible):
        """Update the menu checkmark when the attribute panel visibility changes"""
        self.attribute_view_action.setChecked(visible)

    def open_bpmn_file(self):
        """Open a file dialog to select a BPMN file and remember the last directory."""
        try:
            # Open file dialog starting from the last directory
            file_dialog = QFileDialog(self)
            file_dialog.setNameFilter("BPMN Files (*.bpmn);;All Files (*)")
            file_dialog.setDirectory(self.last_dir)

            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    bpmn_file = selected_files[0]

                    # Update the last used directory in settings
                    self.last_dir = os.path.dirname(bpmn_file)
                    self.settings.setValue('lastDir', self.last_dir)

                    # Parse and load the BPMN file
                    from simpn.bpmn_parser import BPMNParser

                    parser = BPMNParser()
                    parser.parse_file(bpmn_file)
                    simproblem = parser.transform()
                    layout_file = self.get_layout(os.path.basename(bpmn_file))
                    model_panel = ModelPanel(simproblem, layout_file=layout_file)
                    model_panel.add_mod(ClockModule())
                    model_panel.add_mod(NodeHighlightingModule())
                    self.set_simulation(model_panel)
                    self._filename_open = os.path.basename(bpmn_file)
                    # Need to send a resize event to set the correct size
                    dispatch(
                        create_event(
                            EventType.SIM_RESIZE,
                            width=self.simulation_panel.width,
                            height=self.simulation_panel.height,
                        ),
                        self,
                    )
                    dispatch(create_event(EventType.SIM_UPDATE), self)
        except Exception as e:
            self.debug_panel.write_error(f"Error opening BPMN file: {str(e)}")
            return

    def set_simulation(self, model_panel: ModelPanel):
        """
        Sets a simulation into the visualization window and handles the necessary administration.

        This method:
        - Deregisters existing event handlers if another simulation model panel is already set
        - Stores an initial checkpoint of the simulation for reset functionality
        - Creates a new clock module for the module panel
        - Sets the new simulation model panel
        - Registers the model panel, attribute panel, and clock module as event handlers
        - Enables all simulation control buttons
        - Updates the display

        :param model_panel: The ModelPanel instance containing the simulation to visualize
        """
        # If there is an existing simulation, deregister event handlers
        if self.simulation_panel.get_panel() is not None:
            # Deregister event handlers
            unregister_handler(self.simulation_panel.get_panel())
            for mod in self.simulation_panel.get_panel().mods():
                unregister_handler(mod)
            unregister_handler(self.attribute_panel)

        # Store the initial state of the simulator
        model_panel._problem.store_checkpoint("INITIAL_STATE")

        # Attach event handlers
        register_handler(model_panel)
        for mod in model_panel.mods():
            register_handler(mod)
        register_handler(self.attribute_panel)
        register_handler(self.debug_panel)

        # Set it in the pygame widget
        self.simulation_panel.set_panel(model_panel)

        # Dispatch the VISUALIZATION_CREATED event
        evt = create_event(
            EventType.VISUALIZATION_CREATED, sim=model_panel.get_problem()
        )
        dispatch(evt, self)

        # Enable simulation controls
        self.simulation_panel.enable_controls(True)

        # Update the display
        dispatch(create_event(EventType.SIM_UPDATE), self)

    def save_layout(self):
        """
        Save the current node layout to a file.

        Only saves if a BPMN file is currently open. The layout file is saved in the
        platform-specific preferences directory with a .layout extension.
        """
        viz = self.simulation_panel.get_panel()
        if viz is not None and hasattr(self, "_filename_open"):
            viz.save_layout(
                get_preferences_directory() / (self._filename_open + ".layout")
            )

    def get_layout(self, filename) -> str:
        """
        Get the layout file path for a given BPMN filename.

        :param filename: Base name of the BPMN file
        :return: Full path to layout file if it exists, None otherwise
        """
        layout_file = get_preferences_directory() / (filename + ".layout")
        if layout_file.exists():
            return str(layout_file)
        return None

    def reset_layout(self):
        """
        Reset the visualization layout to default positioning.

        Uses the layout algorithm to reposition all nodes.
        """
        dispatch(create_event(EventType.SIM_RESET_LAYOUT), self)

    def closeEvent(self, event):
        """
        Handle window close event gracefully.

        Stops all timers, saves the current layout if applicable, and accepts the close event.

        :param event: Qt close event
        """
        # Stop the timers
        self._playing = False

        # Save layout and settings
        self.saveSettings()
        self.save_layout()

        # Accept the close event
        event.accept()

    def listen_to(self):
        """Specify which event types this handler listens to."""
        return []  # MainWindow doesn't listen to any events currently

    def handle_event(self, event: pygame.event.Event) -> bool:
        return True


DEFAULT_MODS = [ClockModule, FiredTrackerModule, NodeHighlightingModule]


class Visualisation:
    """
    High-level interface for creating and displaying Petri net simulation visualizations.

    This class provides the main entry point for visualizing SimPN simulations. It creates
    a Qt application, main window, and model panel with the specified layout configuration.

    The class can be used in two modes:
    1. With a simulation: Immediately loads and displays the provided simulation
    2. Without a simulation: Opens as an application allowing users to load BPMN files

    Example usage:
        ```python
        from simpn.simulator import SimProblem
        from simpn.visualisation import Visualisation

        # Create simulation
        problem = SimProblem()
        # ... define simulation ...

        # Create and show visualization
        viz = Visualisation(problem)
        viz.show()
        ```
    """

    def __init__(
        self,
        sim_problem=None,
        layout_file=None,
        grid_spacing=50,
        node_spacing=100,
        layout_algorithm: Union[
            Literal["sugiyama", "davidson_harel", "grid", "auto"], None
        ] = "sugiyama",
        extra_modules: List[object] = None,
        include_default_modules: bool = True,
    ):
        """
        Initialize the visualization.

        :param sim_problem: SimProblem instance to visualize (None for application mode)
        :param layout_file: Path to saved layout file for node positioning (optional)
        :param grid_spacing: Grid spacing for snapping nodes (default: 50)
        :param node_spacing: Spacing between nodes in auto-layout (default: 100)
        :param layout_algorithm: Algorithm for auto-layout: "sugiyama" or other (default: "sugiyama")
        :param extra_modules: List of additional modules to integrate (default: None)
        """
        self.sim_problem = sim_problem
        self.layout_file = layout_file
        self.grid_spacing = grid_spacing
        self.node_spacing = node_spacing
        self.layout_algorithm = layout_algorithm
        self.extra_modules = extra_modules if extra_modules is not None else []

        self.app = QApplication(sys.argv)

        # Set application icon for taskbar/dock
        logo_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "logo.png"
        )
        if os.path.exists(logo_path):
            self.app.setWindowIcon(QIcon(logo_path))

        # Create the main window
        if sim_problem is None:
            self.main_window = MainWindow(as_application=True)
            register_handler(self.main_window)
        else:
            self.main_window = MainWindow(as_application=False)
            register_handler(self.main_window)
            model_panel = ModelPanel(
                sim_problem,
                layout_file=layout_file,
                grid_spacing=grid_spacing,
                node_spacing=node_spacing,
                layout_algorithm=layout_algorithm,
            )

            if include_default_modules:
                for mod in DEFAULT_MODS:
                    model_panel.add_mod(mod())

            for mod in self.extra_modules:
                model_panel.add_mod(mod)

            self.main_window.set_simulation(model_panel)

    def show(self):
        """
        Display the visualization window and start the Qt event loop.

        This method blocks until the window is closed by the user.
        """
        self.main_window.show()
        self.app.exec()

    def save_layout(self, layout_file: str):
        """
        Save the current node positions to a layout file.

        :param layout_file: Path where the layout should be saved
        """
        viz = self.main_window.simulation_panel.get_panel()
        if viz is not None:
            viz.save_layout(layout_file)


if __name__ == "__main__":
    visualisation = Visualisation()
    visualisation.show()
