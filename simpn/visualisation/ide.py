import sys
import pygame
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter, QColor, QMouseEvent
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QHBoxLayout, QLabel, QTextEdit, QDockWidget, QToolBar, QSizePolicy, QStyle)


class PygameWidget(QLabel):
    """Widget that renders pygame surface as a QLabel"""
    
    # Signal to emit when mouse is clicked
    mouse_clicked = pyqtSignal(int, int)
    
    def __init__(self, width=640, height=480, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        pygame.init()
        self.surface = pygame.Surface((width, height))
        self.setMinimumSize(width, height)
        
    def update_display(self):
        """Convert pygame surface to QPixmap and display it"""
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
            x = event.position().x()
            y = event.position().y()
            # Emit signal with coordinates
            self.mouse_clicked.emit(int(x), int(y))
        super().mousePressEvent(event)


class DebugPanel(QWidget):
    """Debug panel for textual debugging information"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.setLayout(layout)
        
        # Text area for debug messages
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Debug messages will appear here...")
        layout.addWidget(self.text_edit)
        
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


class AttributePanel(QWidget):
    """Attribute panel for displaying node/object attributes"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        """Set attributes from a dictionary"""
        text = ""
        for key, value in attributes_dict.items():
            text += f"<b>{key}:</b> {value}<br>"
        self.text_edit.setHtml(text)
    
    def clear_attributes(self):
        """Clear all attributes"""
        self.text_edit.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Pygame and PyQt Example")
        self.setGeometry(100, 100, 800, 600)

        # Create pygame widget
        self.pygame_widget = PygameWidget(640, 480)

        # Add the Pygame widget to the main window
        layout = QVBoxLayout()
        layout.addWidget(self.pygame_widget)

        # Add the start and stop buttons to the main window
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Animation", self)
        self.start_button.clicked.connect(self.start_animation)
        button_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop Animation", self)
        self.stop_button.clicked.connect(self.stop_animation)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Create debug panel as a dock widget
        self.debug_dock = QDockWidget("Debug Console", self)
        self.debug_panel = DebugPanel()
        self.debug_dock.setWidget(self.debug_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.debug_dock)
        
        # Create toolbar for the debug dock
        debug_toolbar = QToolBar("Debug Toolbar")
        debug_toolbar.setMovable(False)
        debug_toolbar.setIconSize(QSize(18, 18))  # Smaller icons
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
        clear_action.setIcon(self.create_monochrome_icon(QStyle.StandardPixmap.SP_DialogResetButton))
        clear_action.setToolTip("Clear debug console")
        clear_action.triggered.connect(self.debug_panel.clear_text)
        
        # Close button with icon
        close_action = debug_toolbar.addAction("Close")
        close_action.setIcon(self.create_monochrome_icon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
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
        attr_toolbar.setIconSize(QSize(18, 18))
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
        attr_close_action.setIcon(self.create_monochrome_icon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
        attr_close_action.setToolTip("Close attribute panel")
        attr_close_action.triggered.connect(self.attribute_dock.hide)
        
        self.attribute_dock.setTitleBarWidget(attr_toolbar)
        
        # Connect pygame mouse clicks to attribute panel
        self.pygame_widget.mouse_clicked.connect(self.on_pygame_mouse_click)
        
        # Create menu bar
        self.create_menus()

        # Set up the animation
        self.x = 320  # Initial x position of the moving object
        self.dx = 1  # Speed of the moving object
        self.animation_timer = QTimer(self)  # Create a timer to control the animation
        self.animation_timer.timeout.connect(self.update_animation)  # Connect the timeout signal of the timer to the
        # update_animation method
    
    def create_monochrome_icon(self, standard_pixmap):
        """Create a monochrome version of a standard icon"""
        # Get the original icon
        original_icon = self.style().standardIcon(standard_pixmap)
        pixmap = original_icon.pixmap(QSize(18, 18))
        
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
        self.attribute_panel.set_attributes({
            'Click Position': '',
            'X': x,
            'Y': y
        })
        # Also log to debug console
        self.debug_panel.write_text(f"Mouse clicked at ({x}, {y})")

    def start_animation(self):
        # Start or resume the animation
        if not self.animation_timer.isActive():
            # Start the animation
            self.animation_timer.start(
                1000 // 60)  # Start the timer with an interval of 1000 / 60 milliseconds to update the Pygame surface at 60 FPS
            self.debug_panel.write_success("Animation started")
        else:
            # Resume the animation
            self.animation_timer.start()
            self.debug_panel.write_text("Animation resumed")

    def stop_animation(self):
        # Pause the animation
        self.animation_timer.stop()
        self.debug_panel.write_warning("Animation stopped")

    def update_animation(self):
        # Update the Pygame surface
        self.pygame_widget.surface.fill((220, 220, 220))  # Clear the surface

        # Get current surface dimensions
        width = self.pygame_widget.width
        height = self.pygame_widget.height
        
        # Draw the moving object (centered vertically)
        y_center = height // 2
        pygame.draw.circle(self.pygame_widget.surface, (0, 0, 0), (self.x, y_center), 30)  # Draw a black circle at the current position
        self.x += self.dx  # Update the position of the moving object
        
        # Check if the moving object has reached the edge of the surface (with current width)
        if self.x + 30 > width or self.x - 30 < 0:
            self.dx = -self.dx  # Reverse the direction of the moving object
        
        # Keep x within bounds if window was resized smaller
        self.x = max(30, min(self.x, width - 30))

        # Update the display
        self.pygame_widget.update_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())