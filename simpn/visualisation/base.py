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

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from simpn.simulator import Describable
    from simpn.visualisation.model_panel import Node


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


class PygameWidget(QLabel):
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

        self._display_timer = QTimer(self)
        self._display_timer.timeout.connect(self.trigger_update)
        self._display_timer.start(33)  # ~30 FPS

        # Initialize simulation control variables
        self._playing = False
        self._play_step_delay = 500  # milliseconds between steps

        # Create timers for play mode and display updates
        self._play_timer = QTimer(self)
        self._play_timer.timeout.connect(self.trigger_step)
        self._play_timer.setInterval(self._play_step_delay)

        self.setMouseTracking(True)

        listen_to(EventType.SIM_RENDERED, self.update_display)
        listen_to(EventType.SIM_RUN, self.start_simulation, False)
        listen_to(EventType.SIM_STOP, self.stop_simulation, False)
        listen_to(EventType.SIM_SLOWER, self.slower, False)
        listen_to(EventType.SIM_FASTER, self.faster, False)

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

    def slower(self) -> bool:
        """
        If running the simulation continously, this will increase the time
        between steps.
        """
        self._play_step_delay = min(1000, self._play_step_delay + 100)
        self._play_timer.setInterval(self._play_step_delay)
        return True

    def faster(self) -> bool:
        """
        If running the simulation continously, this will decrease the time
        between steps.
        """
        self._play_step_delay = max(100, self._play_step_delay - 100)
        self._play_timer.setInterval(self._play_step_delay)
        return True

    def stop_simulation(self) -> bool:
        """
        Trigger the continous stepping of the simulation.
        """
        if self._playing:
            self._playing = False
            self._play_timer.stop()

        return True

    def start_simulation(self) -> bool:
        """
        Trigger the continous stepping of the simulation.
        """
        if not self._playing:
            self._playing = True
            self._play_timer.start()

        return True

    def trigger_step(self) -> bool:
        """
        Trigger to get the underlying simulation to move to the next
        step.
        """
        dispatch(create_event(EventType.SIM_PLAY), self)
        return True

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
            self.setPixmap(QPixmap.fromImage(image))
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
            new_width = event.size().width()
            new_height = event.size().height()

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
        x = int(event.position().x())
        y = int(event.position().y())

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
        x = int(event.position().x())
        y = int(event.position().y())
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
        x = int(event.position().x())
        y = int(event.position().y())
        
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

        # Text area for debug messages
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.setMinimumHeight(100)

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

        # Text area for attributes
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Select an object to view attributes...")
        layout.addWidget(self.text_edit)

        self.setMinimumWidth(200)

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
    - Toolbar with simulation controls (play, step, stop, reset, speed adjustment)
    - Zoom controls for the visualization
    - Clock precision controls
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
        self.pygame_widget = PygameWidget(640, 480)

        # Add the Pygame widget to the main window
        layout = QVBoxLayout()
        layout.addWidget(self.pygame_widget)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Create main toolbar
        main_toolbar = QToolBar("Main Toolbar")
        main_toolbar.setMovable(False)
        main_toolbar.setStyleSheet(
            """
            QToolBar {
                spacing: 5px;
                padding: 3px;
                border: none;
            }
            QToolButton {
                padding: 3px;
                margin: 1px;
            }
        """
        )

        # Add Step button to toolbar
        step_action = main_toolbar.addAction("Step")
        step_action.setToolTip("Execute one simulation step")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_step.png"
        )
        step_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        step_action.triggered.connect(self.step_simulation)
        step_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.step_action = step_action  # Store reference to enable/disable later

        # Add Play button to toolbar
        play_action = main_toolbar.addAction("Play")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_play.png"
        )
        play_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        play_action.setToolTip("Start continuous simulation")
        play_action.triggered.connect(self.play_simulation)
        play_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.play_action = play_action

        # Add Stop button to toolbar
        stop_action = main_toolbar.addAction("Stop")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_stop.png"
        )
        stop_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        stop_action.setToolTip("Stop continuous simulation")
        stop_action.triggered.connect(self.stop_simulation)
        stop_action.setEnabled(False)  # Disabled until playing
        self.stop_action = stop_action

        # Add reset to start to toolbar
        reset_action = main_toolbar.addAction("Reset to Start")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "time_back.png"
        )
        reset_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        reset_action.setToolTip("Reset simulation to start")
        reset_action.triggered.connect(self.reset_simulation)
        reset_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.reset_action = reset_action

        # Add Faster button to toolbar
        faster_action = main_toolbar.addAction("Faster")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_faster.png"
        )
        faster_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        faster_action.setToolTip("Increase simulation speed")
        faster_action.triggered.connect(self.faster_simulation)
        faster_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.faster_action = faster_action

        # Add Slower button to toolbar
        slower_action = main_toolbar.addAction("Slower")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "ide_slower.png"
        )
        slower_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        slower_action.setToolTip("Decrease simulation speed")
        slower_action.triggered.connect(self.slower_simulation)
        slower_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.slower_action = slower_action

        # Add separator
        main_toolbar.addSeparator()

        # Add Zoom In button to toolbar
        zoom_in_action = main_toolbar.addAction("Zoom In")
        # load the icon from assets/img/zoom-in.png
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "zoom-in.png"
        )
        zoom_in_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_in_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.zoom_in_action = zoom_in_action

        # Add Zoom Out button to toolbar
        zoom_out_action = main_toolbar.addAction("Zoom Out")
        # load the icon from assets/img/zoom-out.png
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "zoom-out.png"
        )
        zoom_out_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        zoom_out_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.zoom_out_action = zoom_out_action

        # Add Zoom Reset button to toolbar
        zoom_reset_action = main_toolbar.addAction("Zoom 100%")
        # load the icon from assets/img/zoom-reset.png
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "zoom-reset.png"
        )
        zoom_reset_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        zoom_reset_action.setToolTip("Reset zoom to 100% (Ctrl+0)")
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self.zoom_reset)
        zoom_reset_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.zoom_reset_action = zoom_reset_action

        # Add separator
        main_toolbar.addSeparator()

        # Add clock precision increase button to toolbar
        clock_increase_action = main_toolbar.addAction("Clock precision +")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "plus.png"
        )
        clock_increase_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        clock_increase_action.setToolTip("Increase clock precision")
        clock_increase_action.triggered.connect(self.increase_clock_precision)
        clock_increase_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.clock_increase_action = clock_increase_action

        # Add clock precision decrease button to toolbar
        clock_decrease_action = main_toolbar.addAction("Clock precision -")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "minus.png"
        )
        clock_decrease_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        clock_decrease_action.setToolTip("Decrease clock precision")
        clock_decrease_action.triggered.connect(self.decrease_clock_precision)
        clock_decrease_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.clock_decrease_action = clock_decrease_action

        # Add toolbar to main window
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, main_toolbar)

        # Create debug panel as a dock widget
        self.debug_dock = QDockWidget("Debug Console", self)
        self.debug_panel = DebugPanel()
        self.debug_dock.setWidget(self.debug_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.debug_dock)

        # Create toolbar for the debug dock
        debug_toolbar = QToolBar("Debug Toolbar")
        debug_toolbar.setMovable(False)
        debug_toolbar.setStyleSheet(
            """
            QToolBar {
                spacing: 3px;
                padding: 2px;
                border: none;
            }
            QToolButton {
                padding: 2px;
                margin: 0px;
            }
        """
        )

        # Add title label to toolbar
        title_label = QLabel("  Debug Console")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        debug_toolbar.addWidget(title_label)

        # Add spacer to push buttons to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        debug_toolbar.addWidget(spacer)

        # Clear button with icon
        clear_action = debug_toolbar.addAction("Clear")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "clear.png"
        )
        clear_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        clear_action.setToolTip("Clear debug console")
        clear_action.triggered.connect(self.debug_panel.clear_text)

        # Close button with icon
        close_action = debug_toolbar.addAction("Close")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "close.png"
        )
        close_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        close_action.setToolTip("Close debug console")
        close_action.triggered.connect(self.debug_dock.hide)

        self.debug_dock.setTitleBarWidget(debug_toolbar)

        # Create attribute panel as a dock widget
        self.attribute_dock = QDockWidget("Attributes", self)
        self.attribute_panel = AttributePanel()
        self.attribute_dock.setWidget(self.attribute_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.attribute_dock)

        # Create toolbar for the attribute dock
        attr_toolbar = QToolBar("Attribute Toolbar")
        attr_toolbar.setMovable(False)
        attr_toolbar.setStyleSheet(
            """
            QToolBar {
                spacing: 3px;
                padding: 2px;
                border: none;
            }
            QToolButton {
                padding: 2px;
                margin: 0px;
            }
        """
        )

        # Add title label to attribute toolbar
        attr_title_label = QLabel("  Attributes")
        attr_title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        attr_toolbar.addWidget(attr_title_label)

        # Add spacer to push close button to the right
        attr_spacer = QWidget()
        attr_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        attr_toolbar.addWidget(attr_spacer)

        # Close button with icon
        attr_close_action = attr_toolbar.addAction("Close")
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "img", "close.png"
        )
        attr_close_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        attr_close_action.setToolTip("Close attribute panel")
        attr_close_action.triggered.connect(self.attribute_dock.hide)

        self.attribute_dock.setTitleBarWidget(attr_toolbar)

        # Create menu bar
        self.create_menus()

    def create_monochrome_icon(self, standard_pixmap):
        """
        Create a monochrome (dark gray) version of a standard Qt icon.

        :param standard_pixmap: Qt standard pixmap enum value
        :return: QIcon with monochrome rendering
        """
        # Get the original icon
        original_icon = self.style().standardIcon(standard_pixmap)
        pixmap = original_icon.pixmap(QSize(16, 16))

        # Create a new pixmap with the same size
        mono_pixmap = QPixmap(pixmap.size())
        mono_pixmap.fill(Qt.GlobalColor.transparent)

        # Create a painter to draw the monochrome version
        painter = QPainter(mono_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(mono_pixmap.rect(), QColor(100, 100, 100))  # Dark gray
        painter.end()

        return QIcon(mono_pixmap)

    def create_monochrome_icon_from_file(self, file_path):
        """
        Create a monochrome (dark gray) version of an icon from a PNG file.

        :param file_path: Path to the PNG icon file
        :return: QIcon with monochrome rendering, or empty icon if file doesn't exist
        """
        if not os.path.exists(file_path):
            # Return empty icon if file doesn't exist
            return QIcon()

        # Load the pixmap from file
        pixmap = QPixmap(file_path)

        # Resize to standard icon size if needed
        if pixmap.width() != 16 or pixmap.height() != 16:
            pixmap = pixmap.scaled(
                QSize(16, 16),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        # Create a new pixmap with the same size
        mono_pixmap = QPixmap(pixmap.size())
        mono_pixmap.fill(Qt.GlobalColor.transparent)

        # Create a painter to draw the monochrome version
        painter = QPainter(mono_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(mono_pixmap.rect(), QColor(100, 100, 100))  # Dark gray
        painter.end()

        return QIcon(mono_pixmap)

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
            # Create QSettings instance for storing preferences
            # On macOS: ~/Library/Preferences/com.tue.SimPN.plist
            # On Windows: HKEY_CURRENT_USER\Software\TUe\SimPN
            # On Linux: ~/.config/TUe/SimPN.conf
            settings = QSettings("TUe", "SimPN")

            # Get the last used directory, default to user's home directory
            last_dir = settings.value("last_bpmn_directory", os.path.expanduser("~"))

            # Open file dialog starting from the last directory
            file_dialog = QFileDialog(self)
            file_dialog.setNameFilter("BPMN Files (*.bpmn);;All Files (*)")
            file_dialog.setDirectory(last_dir)

            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    bpmn_file = selected_files[0]

                    # Save the directory of the selected file for next time
                    file_dir = os.path.dirname(bpmn_file)
                    settings.setValue("last_bpmn_directory", file_dir)

                    # Parse and load the BPMN file
                    from simpn.bpmn_parser import BPMNParser

                    parser = BPMNParser()
                    parser.parse_file(bpmn_file)
                    simproblem = parser.transform()
                    layout_file = self.get_layout(os.path.basename(bpmn_file))
                    model_panel = ModelPanel(simproblem, layout_file=layout_file)
                    self.set_simulation(model_panel)
                    self._filename_open = os.path.basename(bpmn_file)
                    # Need to send a resize event to set the correct size
                    dispatch(
                        create_event(
                            EventType.SIM_RESIZE,
                            width=self.pygame_widget.width,
                            height=self.pygame_widget.height,
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
        if self.pygame_widget.get_panel() is not None:
            # Deregister event handlers
            unregister_handler(self.pygame_widget.get_panel())
            for mod in self.pygame_widget.get_panel().mods():
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
        self.pygame_widget.set_panel(model_panel)

        # Dispatch the VISUALIZATION_CREATED event
        evt = create_event(
            EventType.VISUALIZATION_CREATED, sim=model_panel.get_problem()
        )
        dispatch(evt, self)

        # Enable simulation controls
        self.step_action.setEnabled(True)
        self.play_action.setEnabled(True)
        self.reset_action.setEnabled(True)
        self.faster_action.setEnabled(True)
        self.slower_action.setEnabled(True)
        self.zoom_in_action.setEnabled(True)
        self.zoom_out_action.setEnabled(True)
        self.zoom_reset_action.setEnabled(True)
        self.clock_increase_action.setEnabled(True)
        self.clock_decrease_action.setEnabled(True)

        # Update the display
        dispatch(create_event(EventType.SIM_UPDATE), self)

    def step_simulation(self):
        """
        Execute one step of the simulation and update the display.
        """
        dispatch(create_event(EventType.SIM_PLAY), self)

    def play_simulation(self):
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
            dispatch(create_event(EventType.SIM_RUN), self)

    def save_layout(self):
        """
        Save the current node layout to a file.

        Only saves if a BPMN file is currently open. The layout file is saved in the
        platform-specific preferences directory with a .layout extension.
        """
        viz = self.pygame_widget.get_panel()
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

    def stop_simulation(self):
        """
        Stop continuous simulation playback.

        Stops the play timer and re-enables step and reset buttons.
        """
        self._playing = False
        self.play_action.setEnabled(True)
        self.step_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.reset_action.setEnabled(True)
        dispatch(create_event(EventType.SIM_STOP))

    def reset_simulation(self):
        """Reset the simulation to the initial state."""
        dispatch(create_event(EventType.SIM_RESET_SIM_STATE), self)

    def faster_simulation(self):
        """Increase simulation speed by decreasing delay."""
        dispatch(create_event(EventType.SIM_FASTER), self)

    def slower_simulation(self):
        """Decrease simulation speed by increasing delay."""
        dispatch(create_event(EventType.SIM_SLOWER), self)

    def zoom_in(self):
        """Zoom in on the visualization by increasing the zoom level."""
        dispatch(create_event(EventType.SIM_ZOOM, action="increase"))

    def zoom_out(self):
        """Zoom out on the visualization by decreasing the zoom level."""
        dispatch(create_event(EventType.SIM_ZOOM, action="decrease"))

    def zoom_reset(self):
        """Reset zoom level to 100% (1.0x scale)."""
        dispatch(create_event(EventType.SIM_ZOOM, action="reset"))

    def increase_clock_precision(self):
        """
        Increase the number of decimal places shown in the simulation clock.
        """
        dispatch(create_event(EventType.CLOCK_PREC_INC))

    def decrease_clock_precision(self):
        """
        Decrease the number of decimal places shown in the simulation clock.

        Minimum precision is 1 decimal place.
        """
        dispatch(create_event(EventType.CLOCK_PREC_DEC))

    def closeEvent(self, event):
        """
        Handle window close event gracefully.

        Stops all timers, saves the current layout if applicable, and accepts the close event.

        :param event: Qt close event
        """
        # Stop the timers
        self._playing = False

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
        layout_algorithm="sugiyama",
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
        viz = self.main_window.pygame_widget.get_panel()
        if viz is not None:
            viz.save_layout(layout_file)


if __name__ == "__main__":
    visualisation = Visualisation()
    visualisation.show()
