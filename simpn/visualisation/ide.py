import pygame
import threading
import os
import sys
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter, QColor, QMouseEvent, QWheelEvent
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QDockWidget, QToolBar, QSizePolicy, QApplication
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from simpn.simulator import Describable

from simpn.visualisation import ModelPanel
from simpn.visualisation.modules.base import ModuleInterface
from simpn.visualisation.events import NODE_CLICKED, SELECTION_CLEAR, check_event


class PygameWidget(QLabel):
    """Widget that renders pygame surface as a QLabel"""
    
    # Signal to emit when mouse is clicked
    mouse_clicked = pyqtSignal(int, int)
    # Signal to emit when mouse is pressed (for dragging)
    mouse_pressed = pyqtSignal(int, int, int)  # x, y, button
    # Signal to emit when mouse is released
    mouse_released = pyqtSignal(int, int, int)  # x, y, button
    # Signal to emit when mouse is moved
    mouse_moved = pyqtSignal(int, int)  # x, y
    
    def __init__(self, width=640, height=480, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        pygame.init()
        pygame.font.init()
        self.surface = pygame.Surface((width, height))
        self.setMinimumSize(width, height)
        self._viz = None  # Will hold the Visualisation instance
        
    def set_visualisation(self, viz):
        """Set the visualisation to render."""
        self._viz = viz

    def get_visualisation(self):
        """Get the current visualisation."""
        return self._viz
        
    def update_display(self):
        """Convert pygame surface to QPixmap and display it"""
        # If we have a visualisation, render it first
        if self._viz is not None:
            self._viz.render(self.surface)
        
        # Get the pygame surface as a string buffer
        data = pygame.image.tostring(self.surface, 'RGB')
        # Create QImage from the data
        image = QImage(data, self.width, self.height, self.width * 3, QImage.Format.Format_RGB888)
        # Convert to QPixmap and display
        self.setPixmap(QPixmap.fromImage(image))
    
    def resizeEvent(self, event):
        """Handle resize events"""
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
            self.surface = pygame.Surface((self.width, self.height))
            # Update the display immediately
            self.update_display()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the click position
            x = int(event.position().x())
            y = int(event.position().y())
            # Emit signals
            self.mouse_clicked.emit(x, y)
            self.mouse_pressed.emit(x, y, 1)
            
            # If we have a visualisation, let it handle the event
            if self._viz is not None:
                node = self._viz.handle_mouse_press((x, y), 1)
                if node is not None:
                    # Update display to show any selection changes
                    self.update_display()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            x = int(event.position().x())
            y = int(event.position().y())
            self.mouse_released.emit(x, y, 1)
            
            # If we have a visualisation, let it handle the event
            if self._viz is not None:
                self._viz.handle_mouse_release((x, y), 1)
                self.update_display()
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        x = int(event.position().x())
        y = int(event.position().y())
        self.mouse_moved.emit(x, y)
        
        # If we have a visualisation, let it handle dragging
        if self._viz is not None:
            self._viz.handle_mouse_motion((x, y))
            self.update_display()
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for zooming"""
        if self._viz is not None:
            # Get the angle delta (positive = scroll up = zoom in)
            delta = event.angleDelta().y()
            
            if delta > 0:
                self._viz.zoom("increase")
            else:
                self._viz.zoom("decrease")
            
            # Update display to show zoom change
            self.update_display()
        
        super().wheelEvent(event)


class DebugPanel(QWidget, ModuleInterface):
    """Debug panel for textual debugging information"""

    # Signals for communication with the UI thread
    text_signal = pyqtSignal(str)
    

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._selected = None
        self._description = None

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setLayout(layout)
        
        # Text area for debug messages
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Debug messages will appear here...")
        layout.addWidget(self.text_edit)

        self.send_text = self.text_signal.connect(self.write_warning)
        
        self.setMinimumHeight(100)
    
    def write_text(self, text):
        """Write text to the debug panel"""
        self.text_edit.append(text)
    
    def write_error(self, text):
        """Write error text (in red) to the debug panel"""
        self.text_edit.append(f'<span style="color: red;">{text}</span>')
    
    def write_warning(self, text):
        """Write warning text (in orange) to the debug panel"""
        self.text_edit.append(f'<span style="color: orange;">{text}</span>')
    
    def write_success(self, text):
        """Write success text (in green) to the debug panel"""
        self.text_edit.append(f'<span style="color: green;">{text}</span>')
    
    def clear_text(self):
        """Clear all text from the debug panel"""
        self.text_edit.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle a pygame event (part of ModuleInterface).
        
        :param event: The pygame event to handle
        """
        event_text = str(event).replace('<', '&lt;').replace('>', '&gt;')
        self.text_signal.emit(
            f"DebugPanel received event: {event_text}"
        )


class AttributePanel(QWidget,ModuleInterface):
    """Attribute panel for displaying node/object attributes"""
    
    # Signals for communication with the UI thread
    description_update_signal = pyqtSignal(list)
    description_update_selected = pyqtSignal(object)
    update_signal = pyqtSignal()
    clear_signal = pyqtSignal()
    
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

        # Connect signals to slots (this ensures UI updates happen on the main thread)
        self.description_update_signal.connect(self._update_description_ui)
        self.description_update_selected.connect(self._update_selected)
        self.clear_signal.connect(self._clear_attributes_ui)
        self.update_signal.connect(self._refresh)
    
    def set_attributes(self, attributes_dict):
        """
        Set attributes from a dictionary
        
        :param attributes_dict: Dictionary of attribute names and values
        """
        text = ""
        for key, value in attributes_dict.items():
            text += f"<b>{key}:</b> {value}<br>"
        self.text_edit.setHtml(text)

    def _clear_attributes_ui(self):
        """
        Clears the text in the attribute panel.
        """
        self.text_edit.clear()

    def set_selected(self, selected: 'Describable'):
        """
        Emits signal to update selected node for the attribute panel.

        :param selected: The selected model node from the simulation
        """
        self.description_update_selected.emit(selected)

    def _update_selected(self, selected: 'Describable'):
        """
        Update selected node for the attribute panel.

        :param selected: The selected model node from the simulation
        """
        self._selected = selected

    def _refresh(self):
        """
        Updates the attribute panel based on the selected object.
        """
        if self._selected is not None:
            des = self._selected._model_node.get_description()
            self._update_description_ui(des)

    def refresh(self):
        """
        Emits a signal to refresh the attribute panel.
        """
        self.update_signal.emit()

    def set_description(self, 
            description: List[Tuple[str, 'Describable.Style']]):
        """Triggers an update of the description.

        :param description: List of sections to add as html
        """
        self.description_update_signal.emit(description)

    def _update_description_ui(self, 
            description: List[Tuple[str, 'Describable.Style']]):
        """
        Set attributes from a description
        
        :param description: List of sections to add as html
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

    def clear_attributes(self):
        """Clear all attributes (thread-safe)"""
        # Emit signal instead of directly updating UI
        self.clear_signal.emit()
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle a pygame event (part of ModuleInterface).
        
        :param event: The pygame event to handle
        """
        if check_event(event, NODE_CLICKED):
            self._selected = event.node
            self._description = event.node._model_node.get_description()
            self.set_selected(self._selected)
            self.set_description(self._description)
        elif check_event(event, SELECTION_CLEAR):
            self.set_selected(None)
            self.set_description([])
            self.clear_attributes()

    def firing(self, *args, **kwargs):
        """
        Called after a binding is fired in the simulation.
        """
        self.refresh()

class MainWindow(QMainWindow):
    def __init__(self, as_application=False):
        """
        Main window for the simulation. The main window can be created from code or by calling the main function below.
        If it is created from code, it is expected to set a simulation using set_simulation().
        If it is created as an application, the load button is visible to load a BPMN file, instead.

        :param as_application: If True, the window will be treated as a main application.
        """
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Pygame and PyQt Example")
        self.setGeometry(100, 100, 800, 600)

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
        main_toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 3px;
                border: none;
            }
            QToolButton {
                padding: 3px;
                margin: 1px;
            }
        """)
        
        # Add open button to the toolbar
        if as_application:
            open_action = main_toolbar.addAction("Open")
            open_action.setToolTip("Open a BPMN file")
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'open.png')
            open_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
            open_action.triggered.connect(self.open_bpmn_file)

            # Add separator
            main_toolbar.addSeparator()

        # Add Step button to toolbar
        step_action = main_toolbar.addAction("Step")        
        step_action.setToolTip("Execute one simulation step")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'ide_step.png')
        step_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        step_action.triggered.connect(self.step_simulation)
        step_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.step_action = step_action  # Store reference to enable/disable later
        
        # Add Play button to toolbar
        play_action = main_toolbar.addAction("Play")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'ide_play.png')
        play_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        play_action.setToolTip("Start continuous simulation")
        play_action.triggered.connect(self.play_simulation)
        play_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.play_action = play_action
        
        # Add Stop button to toolbar
        stop_action = main_toolbar.addAction("Stop")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'ide_stop.png')
        stop_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        stop_action.setToolTip("Stop continuous simulation")
        stop_action.triggered.connect(self.stop_simulation)
        stop_action.setEnabled(False)  # Disabled until playing
        self.stop_action = stop_action
        
        # Add separator
        main_toolbar.addSeparator()
        
        # Add Faster button to toolbar
        faster_action = main_toolbar.addAction("Faster")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'ide_faster.png')
        faster_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        faster_action.setToolTip("Increase simulation speed")
        faster_action.triggered.connect(self.faster_simulation)
        faster_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.faster_action = faster_action
        
        # Add Slower button to toolbar
        slower_action = main_toolbar.addAction("Slower")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'ide_slower.png')
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
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'zoom-in.png')
        zoom_in_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_in_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.zoom_in_action = zoom_in_action
        
        # Add Zoom Out button to toolbar
        zoom_out_action = main_toolbar.addAction("Zoom Out")
        # load the icon from assets/img/zoom-out.png
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'zoom-out.png')
        zoom_out_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        zoom_out_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.zoom_out_action = zoom_out_action
        
        # Add Zoom Reset button to toolbar
        zoom_reset_action = main_toolbar.addAction("Zoom 100%")
        # load the icon from assets/img/zoom-reset.png
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'zoom-reset.png')
        zoom_reset_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        zoom_reset_action.setToolTip("Reset zoom to 100% (Ctrl+0)")
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self.zoom_reset)
        zoom_reset_action.setEnabled(False)  # Disabled until a simulation is loaded
        self.zoom_reset_action = zoom_reset_action
        
        # Add toolbar to main window
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, main_toolbar)
        
        # Initialize simulation control variables
        self._playing = False
        self._play_step_delay = 500  # milliseconds between steps
        self._pthread = None
        self._thread_running = False  # Flag to control the thread loop
        
        # Create debug panel as a dock widget
        self.debug_dock = QDockWidget("Debug Console", self)
        self.debug_panel = DebugPanel()
        self.debug_dock.setWidget(self.debug_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.debug_dock)
        
        # Create toolbar for the debug dock
        debug_toolbar = QToolBar("Debug Toolbar")
        debug_toolbar.setMovable(False)
        debug_toolbar.setStyleSheet("""
            QToolBar {
                spacing: 3px;
                padding: 2px;
                border: none;
            }
            QToolButton {
                padding: 2px;
                margin: 0px;
            }
        """)
        
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
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'clear.png')
        clear_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        clear_action.setToolTip("Clear debug console")
        clear_action.triggered.connect(self.debug_panel.clear_text)
        
        # Close button with icon
        close_action = debug_toolbar.addAction("Close")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'close.png')
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
        attr_toolbar.setStyleSheet("""
            QToolBar {
                spacing: 3px;
                padding: 2px;
                border: none;
            }
            QToolButton {
                padding: 2px;
                margin: 0px;
            }
        """)
        
        # Add title label to attribute toolbar
        attr_title_label = QLabel("  Attributes")
        attr_title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        attr_toolbar.addWidget(attr_title_label)
        
        # Add spacer to push close button to the right
        attr_spacer = QWidget()
        attr_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        attr_toolbar.addWidget(attr_spacer)
        
        # Close button with icon
        attr_close_action = attr_toolbar.addAction("Close")
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img', 'close.png')
        attr_close_action.setIcon(self.create_monochrome_icon_from_file(icon_path))
        attr_close_action.setToolTip("Close attribute panel")
        attr_close_action.triggered.connect(self.attribute_dock.hide)
        
        self.attribute_dock.setTitleBarWidget(attr_toolbar)
                
        # Create menu bar
        self.create_menus()
    
    def create_monochrome_icon(self, standard_pixmap):
        """Create a monochrome version of a standard icon"""
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
        """Create a monochrome version of an icon from a PNG file"""
        if not os.path.exists(file_path):
            # Return empty icon if file doesn't exist
            return QIcon()
        
        # Load the pixmap from file
        pixmap = QPixmap(file_path)
        
        # Resize to standard icon size if needed
        if pixmap.width() != 16 or pixmap.height() != 16:
            pixmap = pixmap.scaled(QSize(16, 16), Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
        
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
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # Window menu
        window_menu = menubar.addMenu("Window")
        
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
        self.debug_dock.visibilityChanged.connect(self.on_debug_panel_visibility_changed)
        self.attribute_dock.visibilityChanged.connect(self.on_attribute_panel_visibility_changed)
    
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
    
    def on_pygame_mouse_click(self, x, y):
        """Handle mouse clicks on the pygame widget"""
        # Display coordinates in attribute panel
        attrs = {
            'Click Position': '',
            'X': x,
            'Y': y
        }
        
        # If we have a visualisation and a node was clicked, show node info
        viz = self.pygame_widget.get_visualisation()
        if viz is not None:
            node = viz._get_node_at((x, y))
            if node is not None:
                attrs['Node ID'] = node.get_id()
                attrs['Node Type'] = type(node).__name__
                if hasattr(node, '_model_node') and node._model_node is not None:
                    model_node = node._model_node
                    if hasattr(model_node, 'marking'):
                        attrs['Token Count'] = len(model_node.marking)
        
        self.attribute_panel.set_attributes(attrs)
    
    def open_bpmn_file(self):
        # open a file dialog to select a BPMN file
        from PyQt6.QtWidgets import QFileDialog
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("BPMN Files (*.bpmn);;All Files (*)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                bpmn_file = selected_files[0]
                self.debug_panel.write_text(f"Selected BPMN file: {bpmn_file}")
                from simpn.bpmn_parser import BPMNParser
                parser = BPMNParser()
                parser.parse_file(bpmn_file)
                simproblem = parser.transform()
                model_panel = ModelPanel(simproblem)
                self.set_simulation(model_panel)

    def set_simulation(self, model_panel: ModelPanel):
        """
        Load a simulation problem into the IDE.
        
        :param sim_problem: The simulation problem to visualize
        :param layout_file: Optional layout file path
        """
        try:            
            # Create the visualisation
            viz = model_panel

            viz.add_ui_module(self.debug_panel)
            viz.add_ui_module(self.attribute_panel)
            
            # Set it in the pygame widget
            self.pygame_widget.set_visualisation(viz)
            
            # Enable simulation controls
            self.step_action.setEnabled(True)
            self.play_action.setEnabled(True)
            self.faster_action.setEnabled(True)
            self.slower_action.setEnabled(True)
            self.zoom_in_action.setEnabled(True)
            self.zoom_out_action.setEnabled(True)
            self.zoom_reset_action.setEnabled(True)
            
            # Update the display
            self.pygame_widget.update_display()

            # Start the background thread for continuous updates
            self._thread_running = True
            self._pthread = threading.Thread(target=self._play_loop, daemon=True)
            self._pthread.start()
                        
        except Exception as e:
            self.debug_panel.write_error(f"Failed to load simulation: {str(e)}")
            import traceback
            self.debug_panel.write_error(traceback.format_exc())
    
    def step_simulation(self):
        """Execute one step of the simulation."""
        viz = self.pygame_widget.get_visualisation()
        if viz is not None:
            viz.step()
            self.pygame_widget.update_display()
    
    def play_simulation(self):
        """Start continuous simulation playback."""
        if not self._playing:
            self._playing = True
            self.play_action.setEnabled(False)
            self.step_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            
    
    def _play_loop(self):
        """The main play loop that runs in a separate thread."""
        import time
        now = time.time()
        last_tick = now
        while self._thread_running:
            now = time.time()
            viz = self.pygame_widget.get_visualisation()
            if viz is not None:
                # Don't call pygame.event.get() here - it causes threading issues on macOS
                # PyQt6 handles all events through its own event system
                if self._playing and last_tick + (self._play_step_delay / 1000.0) < now:
                        viz.step()
                        
                        last_tick = now
                self.pygame_widget.update_display()
            time.sleep(0.033)  # Sleep for ~30 FPS instead of using pygame clock
    
    def stop_simulation(self):
        """Stop continuous simulation playback."""
        self._playing = False
        self.play_action.setEnabled(True)
        self.step_action.setEnabled(True)
        self.stop_action.setEnabled(False)
    
    def faster_simulation(self):
        """Increase simulation speed by decreasing delay."""
        self._play_step_delay = max(100, self._play_step_delay - 100)
        self.debug_panel.write_text(f"Simulation speed: {1000/self._play_step_delay:.1f} steps/second")
    
    def slower_simulation(self):
        """Decrease simulation speed by increasing delay."""
        self._play_step_delay = min(1000, self._play_step_delay + 100)
        self.debug_panel.write_text(f"Simulation speed: {1000/self._play_step_delay:.1f} steps/second")
    
    def zoom_in(self):
        """Zoom in on the visualization."""
        viz = self.pygame_widget.get_visualisation()
        if viz is not None:
            viz.zoom("increase")
            zoom_level = viz.get_zoom_level()
            self.debug_panel.write_text(f"Zoom: {zoom_level*100:.0f}%")
            self.pygame_widget.update_display()
    
    def zoom_out(self):
        """Zoom out on the visualization."""
        viz = self.pygame_widget.get_visualisation()
        if viz is not None:
            viz.zoom("decrease")
            zoom_level = viz.get_zoom_level()
            self.debug_panel.write_text(f"Zoom: {zoom_level*100:.0f}%")
            self.pygame_widget.update_display()
    
    def zoom_reset(self):
        """Reset zoom to 100%."""
        viz = self.pygame_widget.get_visualisation()
        if viz is not None:
            viz.zoom("reset")
            self.debug_panel.write_text(f"Zoom: 100%")
            self.pygame_widget.update_display()
    
    def closeEvent(self, event):
        """Handle window close event - stop the background thread cleanly."""
        # Stop the background thread
        self._thread_running = False
        self._playing = False
        
        # Wait for thread to finish (with timeout)
        if self._pthread is not None and self._pthread.is_alive():
            self._pthread.join(timeout=1.0)
        
        # Accept the close event
        event.accept()


class Visualisation:
    def __init__(self, sim_problem=None, 
                 layout_file=None, 
                 grid_spacing=50, 
                 node_spacing=100, 
                 layout_algorithm="sugiyama",
                 extra_modules:List=None):
        self.sim_problem = sim_problem
        self.layout_file = layout_file
        self.grid_spacing = grid_spacing
        self.node_spacing = node_spacing
        self.layout_algorithm = layout_algorithm
        self.extra_modules = extra_modules if extra_modules is not None else []

        self.app = QApplication(sys.argv)

        if sim_problem is None:
            self.main_window = MainWindow(as_application=True)
        else:
            self.main_window = MainWindow(as_application=False)
            model_panel = ModelPanel(
                sim_problem,
                layout_file=layout_file,
                grid_spacing=grid_spacing,
                node_spacing=node_spacing,
                layout_algorithm=layout_algorithm,
                extra_modules=extra_modules
            )
            self.main_window.set_simulation(model_panel)            

    def show(self):
        self.main_window.show()
        self.app.exec()
    
    def save_layout(self, layout_file: str):
        """Save the current layout to a file."""
        viz = self.main_window.pygame_widget.get_visualisation()
        if viz is not None:
            viz.save_layout(layout_file)


if __name__ == "__main__":
    visualisation = Visualisation()
    visualisation.show()