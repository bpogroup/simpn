import unittest
from time import time, sleep
from tests.utils import DummyEventHandler
from tests.dummy_problems import create_dummy_bpmn
from PyQt6.QtWidgets import QApplication
from simpn.visualisation.events import EventType
from simpn.visualisation.base import MainWindow, ModelPanel, EventDispatcher
import sys


class TestEventDispatching(unittest.TestCase):
    """
    Tests the event dispatching system functionality.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.problem = create_dummy_bpmn()
        self.event_dispatcher = EventDispatcher()
        
        # Create main window without creating a new QApplication
        self.main_window = MainWindow(as_application=False)
        
        # Inject the event dispatcher  
        self.main_window._event_dispatcher = self.event_dispatcher
        
        # Create model panel
        model_panel = ModelPanel(
            self.problem,
            layout_file=None,
            grid_spacing=50,
            node_spacing=100,
            layout_algorithm="sugiyama"
        )
        
        self.main_window.set_simulation(model_panel)
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.main_window:
            self.main_window.close()
    
    def run_simulation(self, duration_ms=1000):
        """
        Helper method to run simulation for a given duration.
        
        :param duration_ms: Duration to run in milliseconds
        """
        panel = self.main_window.pygame_widget.get_panel()
        
        # Speed up simulation
        for _ in range(5):
            panel.action_faster()
        
        # Start simulation
        panel.action_play()
        
        # Show the window
        self.main_window.show()
        
        # Process events for the specified duration
        start_time = time()
        while (time() - start_time) * 1000 < duration_ms:
            self.app.processEvents()
            sleep(0.01)
        
        # Stop simulation
        panel.action_stop()
    
    def test_register_single_handler(self):
        handler = DummyEventHandler()
        self.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        self.run_simulation(duration_ms=1000)
        
        self.assertTrue(handler.render_ui_called)

    def test_register_multiple_handlers(self):
        handler1 = DummyEventHandler()
        handler2 = DummyEventHandler()
        self.event_dispatcher.register_handler(handler1, [EventType.RENDER_UI])
        self.event_dispatcher.register_handler(handler2, [EventType.RENDER_UI])
        
        self.run_simulation(duration_ms=1000)
        
        self.assertTrue(handler1.render_ui_called)
        self.assertTrue(handler2.render_ui_called)

    def test_handler_multiple_event_types(self):
        handler = DummyEventHandler()
        self.event_dispatcher.register_handler(handler, [EventType.RENDER_UI, EventType.BINDING_FIRED])
        
        self.run_simulation(duration_ms=1500)
        
        self.assertTrue(handler.render_ui_called)
        self.assertTrue(handler.binding_fired_called)

    def test_unregister_handler(self):
        handler = DummyEventHandler()
        self.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        self.event_dispatcher.unregister_handler(handler)
        
        self.run_simulation(duration_ms=1000)
        
        self.assertFalse(handler.render_ui_called)

    def test_handler_not_called_for_unregistered_event(self):
        handler = DummyEventHandler()
        self.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        self.run_simulation(duration_ms=1500)
        
        self.assertTrue(handler.render_ui_called)
        self.assertFalse(handler.binding_fired_called)

    def test_multiple_handlers_independent(self):
        handler1 = DummyEventHandler()
        handler2 = DummyEventHandler()
        self.event_dispatcher.register_handler(handler1, [EventType.RENDER_UI])
        self.event_dispatcher.register_handler(handler2, [EventType.BINDING_FIRED])
        
        self.run_simulation(duration_ms=1500)
        
        self.assertTrue(handler1.render_ui_called)
        self.assertFalse(handler1.binding_fired_called)
        self.assertFalse(handler2.render_ui_called)
        self.assertTrue(handler2.binding_fired_called)


class TestBasicVisualisation(unittest.TestCase):
    """
    Tests basic visualisation functionality.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.problem = create_dummy_bpmn()
        self.event_dispatcher = EventDispatcher()
        
        # Create main window without creating a new QApplication
        self.main_window = MainWindow(as_application=False)
        
        # Inject the event dispatcher  
        self.main_window._event_dispatcher = self.event_dispatcher
        
        # Create model panel
        model_panel = ModelPanel(
            self.problem,
            layout_file=None,
            grid_spacing=50,
            node_spacing=100,
            layout_algorithm="sugiyama"
        )
        
        self.main_window.set_simulation(model_panel)
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.main_window:
            self.main_window.close()
    
    def run_simulation(self, duration_ms=1000):
        """
        Helper method to run simulation for a given duration.
        
        :param duration_ms: Duration to run in milliseconds
        """
        panel = self.main_window.pygame_widget.get_panel()
        
        # Speed up simulation
        for _ in range(5):
            panel.action_faster()
        
        # Start simulation
        panel.action_play()
        
        # Show the window
        self.main_window.show()
        
        # Process events for the specified duration
        start_time = time()
        while (time() - start_time) * 1000 < duration_ms:
            self.app.processEvents()
            sleep(0.01)
        
        # Stop simulation
        panel.action_stop()
    
    def test_can_run_vis(self):
        self.assertIsNotNone(self.main_window)
        
        self.run_simulation(duration_ms=1500)

    def test_render_ui(self):
        handler = DummyEventHandler()
        # Register the handler to listen for RENDER_UI events
        self.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        self.run_simulation(duration_ms=1500)

        self.assertTrue(handler.render_ui_called)

    def test_firing(self):
        handler = DummyEventHandler()
        # Register the handler to listen for BINDING_FIRED events
        self.event_dispatcher.register_handler(handler, [EventType.BINDING_FIRED])

        self.run_simulation(duration_ms=1500)

        self.assertTrue(handler.binding_fired_called)

    def test_clock_time(self):
        # test if after some simulation time, the clock's time is the same as the simproblem's time
        panel = self.main_window.pygame_widget.get_panel()

        self.run_simulation(duration_ms=1500)

        # Get the clock module time from the UI
        clock_time = self.main_window.clock_module._time
        
        # Get the simulation time from the SimProblem
        sim_time = panel._problem.clock
        
        # They should be equal (or very close due to timing)
        self.assertAlmostEqual(clock_time, sim_time, delta=0.2)
