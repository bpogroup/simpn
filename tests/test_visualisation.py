import unittest
from time import time, sleep
import threading
from tests.utils import TestEventHandler
from tests.dummy_problems import create_dummy_bpmn, create_dummy_pn
import pygame
from PyQt6.QtWidgets import QApplication

from simpn.visualisation import Visualisation, Node
from simpn.visualisation.events import EventType

class EventDispatchingTests(unittest.TestCase):
    """
    Tests the event dispatching system functionality.
    """

    def setUp(self):
        self.problem = create_dummy_bpmn()
    
    def test_register_single_handler(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        vis.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        thread = threading.Thread(target=BasicVisualisationTests.quick_close, args=[vis, 1.0])
        thread.start()
        vis.show()
        thread.join()
        
        self.assertTrue(handler.render_ui_called)

    def test_register_multiple_handlers(self):
        handler1 = TestEventHandler()
        handler2 = TestEventHandler()
        vis = Visualisation(self.problem)
        vis.event_dispatcher.register_handler(handler1, [EventType.RENDER_UI])
        vis.event_dispatcher.register_handler(handler2, [EventType.RENDER_UI])
        
        thread = threading.Thread(target=BasicVisualisationTests.quick_close, args=[vis, 1.0])
        thread.start()
        vis.show()
        thread.join()
        
        self.assertTrue(handler1.render_ui_called)
        self.assertTrue(handler2.render_ui_called)

    def test_handler_multiple_event_types(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        vis.event_dispatcher.register_handler(handler, [EventType.RENDER_UI, EventType.BINDING_FIRED])
        
        thread = threading.Thread(target=BasicVisualisationTests.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()
        
        self.assertTrue(handler.render_ui_called)
        self.assertTrue(handler.binding_fired_called)

    def test_unregister_handler(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        vis.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        vis.event_dispatcher.unregister_handler(handler)
        
        thread = threading.Thread(target=BasicVisualisationTests.quick_close, args=[vis, 1.0])
        thread.start()
        vis.show()
        thread.join()
        
        self.assertFalse(handler.render_ui_called)

    def test_handler_not_called_for_unregistered_event(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        vis.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        thread = threading.Thread(target=BasicVisualisationTests.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()
        
        self.assertTrue(handler.render_ui_called)
        self.assertFalse(handler.binding_fired_called)

    def test_multiple_handlers_independent(self):
        handler1 = TestEventHandler()
        handler2 = TestEventHandler()
        vis = Visualisation(self.problem)
        vis.event_dispatcher.register_handler(handler1, [EventType.RENDER_UI])
        vis.event_dispatcher.register_handler(handler2, [EventType.BINDING_FIRED])
        
        thread = threading.Thread(target=BasicVisualisationTests.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()
        
        self.assertTrue(handler1.render_ui_called)
        self.assertFalse(handler1.binding_fired_called)
        self.assertFalse(handler2.render_ui_called)
        self.assertTrue(handler2.binding_fired_called)


class BasicVisualisationTests(unittest.TestCase):

    def setUp(self):
        self.problem = create_dummy_bpmn() # for some reason, if I try this with PN, it hangs
    
    @staticmethod
    def quick_close(vis, wait_time=0.4):
        start = time()
        for _ in range(5):
            vis.main_window.pygame_widget.get_panel().action_faster()
        vis.main_window.pygame_widget.get_panel().action_play()
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT + 1,
                { "message" : "hello, world!"}
            )
        )

        while (time() - start) <= wait_time:
            sleep(0.02)

        QApplication.instance().quit()

    def test_can_run_vis(self):
        vis = Visualisation(self.problem)
        self.assertIsNotNone(vis)
        
        thread = threading.Thread(target=self.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()

    def test_render_ui(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        # Register the handler to listen for RENDER_UI events
        vis.event_dispatcher.register_handler(handler, [EventType.RENDER_UI])
        
        thread = threading.Thread(target=self.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(handler.render_ui_called)

    def test_firing(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        # Register the handler to listen for BINDING_FIRED events
        vis.event_dispatcher.register_handler(handler, [EventType.BINDING_FIRED])

        thread = threading.Thread(target=self.quick_close, args=[vis, 1.5])
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(handler.binding_fired_called)

    def test_node_clicked_event(self):
        handler = TestEventHandler()
        vis = Visualisation(self.problem)
        panel = vis.main_window.pygame_widget.get_panel()
        # Register the handler to listen for NODE_CLICKED events
        vis.event_dispatcher.register_handler(handler, [EventType.NODE_CLICKED])

        thread = threading.Thread(target=self.quick_close, args=[vis, 1.5])

        # Find a node to click on and simulate a mouse press directly
        node_to_click = None
        for node in panel._nodes.values():
            if isinstance(node, Node):
                node_to_click = node
                break
        
        # Directly call handle_mouse_press with the node's position
        if node_to_click is not None:
            panel.handle_mouse_press(node_to_click.get_pos(), 1)

        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(handler.node_clicked_called)

    # TODO: Create a test for the Clock
    # TODO: fix the clock's higher and lower precision on click