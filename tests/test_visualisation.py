import pytest
from time import time, sleep
from tests.utils import DummyEventHandler
from tests.dummy_problems import create_dummy_bpmn
import pygame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from simpn.visualisation import Visualisation, Node
from simpn.visualisation.events import EventType
from simpn.visualisation.base import MainWindow, ModelPanel, EventDispatcher
import sys


@pytest.fixture
def problem():
    """Create a dummy BPMN problem for testing."""
    return create_dummy_bpmn()


@pytest.fixture
def event_dispatcher():
    """Create an event dispatcher for testing."""
    return EventDispatcher()


@pytest.fixture
def main_window(qapp, problem, event_dispatcher):
    """
    Create a main window with simulation for testing.
    Uses the pytest-qt managed QApplication instead of creating a new one.
    """
    # Create main window without creating a new QApplication
    main_window = MainWindow(as_application=False)
    
    # Inject the event dispatcher  
    main_window._event_dispatcher = event_dispatcher
    
    # Create model panel
    model_panel = ModelPanel(
        problem,
        layout_file=None,
        grid_spacing=50,
        node_spacing=100,
        layout_algorithm="sugiyama"
    )
    
    main_window.set_simulation(model_panel)
    
    return main_window


def run_simulation(main_window, qtbot, duration_ms=1000):
    """
    Helper function to run simulation for a given duration.
    
    :param main_window: MainWindow instance
    :param qtbot: pytest-qt bot fixture
    :param duration_ms: Duration to run in milliseconds
    """
    panel = main_window.pygame_widget.get_panel()
    
    # Speed up simulation
    for _ in range(5):
        panel.action_faster()
    
    # Start simulation
    panel.action_play()
    
    # Show the window
    main_window.show()
    qtbot.waitExposed(main_window)
    
    # Wait for the simulation to run
    qtbot.wait(duration_ms)
    
    # Stop simulation and close
    panel.action_stop()
    main_window.close()


class TestEventDispatching:
    """
    Tests the event dispatching system functionality.
    """
    
    def test_register_single_handler(self, qtbot, main_window, event_dispatcher):
        handler = DummyEventHandler()
        qtbot.addWidget(main_window)
        event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        run_simulation(main_window, qtbot, duration_ms=1000)
        
        assert handler.render_ui_called

    def test_register_multiple_handlers(self, qtbot, main_window, event_dispatcher):
        handler1 = DummyEventHandler()
        handler2 = DummyEventHandler()
        qtbot.addWidget(main_window)
        event_dispatcher.register_handler(handler1, [EventType.RENDER_UI])
        event_dispatcher.register_handler(handler2, [EventType.RENDER_UI])
        
        run_simulation(main_window, qtbot, duration_ms=1000)
        
        assert handler1.render_ui_called
        assert handler2.render_ui_called

    def test_handler_multiple_event_types(self, qtbot, main_window, event_dispatcher):
        handler = DummyEventHandler()
        qtbot.addWidget(main_window)
        event_dispatcher.register_handler(handler, [EventType.RENDER_UI, EventType.BINDING_FIRED])
        
        run_simulation(main_window, qtbot, duration_ms=1500)
        
        assert handler.render_ui_called
        assert handler.binding_fired_called

    def test_unregister_handler(self, qtbot, main_window, event_dispatcher):
        handler = DummyEventHandler()
        qtbot.addWidget(main_window)
        event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        event_dispatcher.unregister_handler(handler)
        
        run_simulation(main_window, qtbot, duration_ms=1000)
        
        assert not handler.render_ui_called

    def test_handler_not_called_for_unregistered_event(self, qtbot, main_window, event_dispatcher):
        handler = DummyEventHandler()
        qtbot.addWidget(main_window)
        event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        run_simulation(main_window, qtbot, duration_ms=1500)
        
        assert handler.render_ui_called
        assert not handler.binding_fired_called

    def test_multiple_handlers_independent(self, qtbot, main_window, event_dispatcher):
        handler1 = DummyEventHandler()
        handler2 = DummyEventHandler()
        qtbot.addWidget(main_window)
        event_dispatcher.register_handler(handler1, [EventType.RENDER_UI])
        event_dispatcher.register_handler(handler2, [EventType.BINDING_FIRED])
        
        run_simulation(main_window, qtbot, duration_ms=1500)
        
        assert handler1.render_ui_called
        assert not handler1.binding_fired_called
        assert not handler2.render_ui_called
        assert handler2.binding_fired_called


class TestBasicVisualisation:
    """
    Tests basic visualisation functionality.
    """
    
    def test_can_run_vis(self, qtbot, main_window):
        qtbot.addWidget(main_window)
        assert main_window is not None
        
        run_simulation(main_window, qtbot, duration_ms=1500)

    def test_render_ui(self, qtbot, main_window, event_dispatcher):
        handler = DummyEventHandler()
        qtbot.addWidget(main_window)
        # Register the handler to listen for RENDER_UI events
        event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        run_simulation(main_window, qtbot, duration_ms=1500)

        assert handler.render_ui_called

    def test_firing(self, qtbot, main_window, event_dispatcher):
        handler = DummyEventHandler()
        qtbot.addWidget(main_window)
        # Register the handler to listen for BINDING_FIRED events
        event_dispatcher.register_handler(handler, [EventType.BINDING_FIRED])

        run_simulation(main_window, qtbot, duration_ms=1500)

        assert handler.binding_fired_called

    def test_clock_time(self, qtbot, main_window):
        # test if after some simulation time, the clock's time is the same as the simproblem's time
        qtbot.addWidget(main_window)
        panel = main_window.pygame_widget.get_panel()

        run_simulation(main_window, qtbot, duration_ms=1500)

        # Get the clock module time from the UI
        clock_time = main_window.clock_module._time
        
        # Get the simulation time from the SimProblem
        sim_time = panel._problem.clock
        
        # They should be equal (or very close due to timing)
        assert abs(clock_time - sim_time) < 0.2  # Allow 0.2 units difference

