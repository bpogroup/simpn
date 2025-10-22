import unittest
from time import time, sleep
import threading
from tests.utils import mock_click_event_with_button
from tests.dummy_problems import create_dummy_bpmn, create_dummy_pn

import pygame

from simpn.simulator import SimProblem, SimToken
from simpn.helpers import Place, Transition
from simpn.visualisation import Visualisation
from simpn.visualisation.test_modules import CheckerModule
from simpn.visualisation.ui_modules import UIClockModule
# UISidePanelModule has been removed


class PipelineTests(unittest.TestCase):

    def setUp(self):
        self.problem = create_dummy_pn()
    
    @staticmethod
    def quick_close(vis, wait_time=0.4):
        start = time()

        vis.action_play()
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT + 1,
                { "message" : "hello, world!"}
            )
        )

        while (time() - start) <= wait_time:
            sleep(0.02)

        vis.close()
            
    def test_adding_modules(self):
        vis = Visualisation(
            self.problem,
            extra_modules=[
                
            ]
        )
        self.assertEqual(len(vis._modules), 2)

        vis = Visualisation(
            self.problem,
            extra_modules=[
                CheckerModule(),
            ]
        )
        self.assertEqual(len(vis._modules), 3)


        vis = Visualisation(
            self.problem,
            extra_modules=[
                CheckerModule(),
                CheckerModule(),
            ]
        )
        self.assertEqual(len(vis._modules), 4)

    def test_create_hook(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )

        self.assertTrue(checker.create_called)

    def test_pre_hook(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )
        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(checker.pre_called)

    def test_handle_event(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )
        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(checker.handle_event_called)

    def test_render_sim(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )
        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(checker.render_sim_called)

    def test_render_ui(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )
        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(checker.render_ui_called)

    def test_firing(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )
        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(checker.firing_called)

    def test_post_event_loop(self):
        checker = CheckerModule()
        vis = Visualisation(
            self.problem,
            extra_modules=[
                checker
            ]
        )
        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

        self.assertTrue(checker.post_called)

class UIClockTests(unittest.TestCase):
    """
    Tests the functionality for UIClock Module in visualisations.
    """

    def setUp(self):
        self.problem = create_dummy_pn()
    
    @staticmethod
    def quick_close(vis, wait_time=0.75):
        start = time()

        vis.action_play()
        pygame.event.post(
            pygame.event.Event(
                pygame.USEREVENT + 1,
                { "message" : "hello, world!"}
            )
        )

        while (time() - start) <= wait_time:
            sleep(0.02)

        vis.close()

    def test_no_crash(self):
        mod = UIClockModule(1)
        vis = Visualisation(
            self.problem,
            extra_modules=[
                mod
            ]
        )

        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

    def test_time_matches(self):
        mod = UIClockModule(1)
        vis = Visualisation(
            self.problem,
            extra_modules=[
                mod
            ]
        )

        thread = threading.Thread(target=self.quick_close, args=([vis, 3]))
        thread.start()
        vis.show()
        thread.join()

        self.assertEqual(mod._time, self.problem.clock)

    @staticmethod
    def trigger_click(rect, button, wait=0.25):
        sleep(wait)
        mock_click_event_with_button(rect, button)

    def test_increasing_precision(self):
        mod = UIClockModule(1)
        vis = Visualisation(
            self.problem,
            extra_modules=[
                mod
            ]
        )

        thread = threading.Thread(target=self.quick_close, args=([vis, 2]))
        mock = threading.Thread(target=self.trigger_click, 
                                args=[mod._clock_rect, 1])
        mock.start()
        thread.start()
        vis.show()
        thread.join()
        mock.join()

        self.assertEqual(mod._precision, 2)

    def test_decreasing_precision(self):
        mod = UIClockModule(2)
        vis = Visualisation(
            self.problem,
            extra_modules=[
                mod
            ]
        )

        thread = threading.Thread(target=self.quick_close, args=([vis, 2]))
        mock = threading.Thread(target=self.trigger_click, 
                                args=[mod._clock_rect, 3])
        thread.start()
        mock.start()
        vis.show()
        mock.join()
        thread.join()

        self.assertEqual(mod._precision, 1)

    def test_min_decreasing_precision(self):
        mod = UIClockModule(1)
        vis = Visualisation(
            self.problem,
            extra_modules=[
                mod
            ]
        )

        thread = threading.Thread(target=self.quick_close, args=([vis, 2]))
        mock = threading.Thread(target=self.trigger_click, 
                                args=[mod._clock_rect, 3])
        mock2 = threading.Thread(target=self.trigger_click, 
                                args=[mod._clock_rect, 3, 0.5])
        thread.start()
        mock.start()
        mock2.start()
        vis.show()
        mock.join()
        mock2.join()
        thread.join()

        self.assertEqual(mod._precision, 1)

    def test_increase_descrease_precision(self):
        mod = UIClockModule(3)
        vis = Visualisation(
            self.problem,
            extra_modules=[
                mod
            ]
        )

        thread = threading.Thread(target=self.quick_close, args=([vis, 2]))
        mock = threading.Thread(target=self.trigger_click, 
                                args=[mod._clock_rect, 3])
        mock2 = threading.Thread(target=self.trigger_click, 
                                args=[mod._clock_rect, 1, 0.5])
        thread.start()
        mock.start()
        mock2.start()
        vis.show()
        mock.join()
        mock2.join()
        thread.join()

        self.assertEqual(mod._precision, 3)

class UISidePanelTests(unittest.TestCase):
    """
    Tests the functionality of the module for the side panel.
    """

    def setUp(self):
        self.problem = create_dummy_pn()
        self.bpmn_problem = create_dummy_bpmn()
            
    @staticmethod
    def quick_close(vis, wait_time=2):
        start = time()

        vis.action_play()

        while (time() - start) <= wait_time:
            sleep(0.02)

        vis.close()

    @staticmethod
    def trigger_click(mod, rect_name, button, wait=0.25):
        sleep(wait)
        rect = getattr(mod, rect_name)
        mock_click_event_with_button(rect, button)

    @staticmethod
    def get_side_panel_module(vis):
        # UISidePanelModule has been removed
        return None

    @staticmethod
    def trigger_node_click(vis, node_name, button, wait=0.5):
        sleep(wait)
        node = vis._nodes[node_name]
        mock_click_event_with_button(node, button)
            
    def test_no_crash(self):
        vis = Visualisation(
            self.problem
        )

        thread = threading.Thread(target=self.quick_close, args=([vis]))
        thread.start()
        vis.show()
        thread.join()

    def test_open_panel(self):
        vis = Visualisation(
            self.problem
        )
        mod = self.get_side_panel_module(vis)

        thread = threading.Thread(target=self.quick_close, args=([vis, 1]))
        hit_thread = threading.Thread(
            target=self.trigger_click, args=([mod, 'orect', 1])
        )
        thread.start()
        hit_thread.start()
        vis.show()
        hit_thread.join()
        self.assertTrue(
            mod._opened
        )
        thread.join()

    def test_close_panel(self):
        vis = Visualisation(
            self.problem
        )
        mod = self.get_side_panel_module(vis)

        thread = threading.Thread(target=self.quick_close, args=([vis, 1.5]))
        hit_thread = threading.Thread(
            target=self.trigger_click, args=([mod, 'orect', 1])
        )
        hit_thread2 = threading.Thread(
            target=self.trigger_click, args=([mod, 'crect', 1, 0.75])
        )
        thread.start()
        hit_thread.start()
        hit_thread2.start()
        vis.show()
        hit_thread.join()
        hit_thread2.join()
        self.assertFalse(
            mod._opened
        )
        thread.join()

    def test_description(self):
        vis = Visualisation(
            self.problem
        )
        mod = self.get_side_panel_module(vis)

        thread = threading.Thread(target=self.quick_close, args=([vis, 1.5]))
        hit_thread = threading.Thread(
            target=self.trigger_click, args=([mod, 'orect', 1,  0.5])
        )
        hit_thread2 = threading.Thread(
            target=self.trigger_node_click, args=([vis, 'start', 1, 0.5])
        )
        thread.start()
        hit_thread.start()
        hit_thread2.start()
        vis.show()
        hit_thread.join()
        hit_thread2.join()
        thread.join()

        node = vis._nodes['start']._model_node
        description = mod._description

        self.assertIn(
            node.get_id(),
            description[0][0]
        )

    def test_clicking_on_things(self):
        vis = Visualisation(
            self.problem
        )
        mod = self.get_side_panel_module(vis)

        def clicker(vis, wait):
            sleep(wait)
            for node in vis._nodes.values():
                sleep(0.2)
                mock_click_event_with_button(node, 1)

        thread = threading.Thread(target=self.quick_close, args=([vis, 1.5]))
        hit_thread = threading.Thread(
            target=self.trigger_click, args=([mod, 'orect', 1,  0.2])
        )
        hit_thread2 = threading.Thread(
            target=clicker, args=([vis, 0.3])
        )
        thread.start()
        hit_thread.start()
        hit_thread2.start()
        vis.show()
        hit_thread.join()
        hit_thread2.join()
        thread.join()

    def test_clicking_on_bpmn_things(self):
        vis = Visualisation(
            self.bpmn_problem
        )
        mod = self.get_side_panel_module(vis)

        def clicker(vis, wait):
            sleep(wait)
            for node in vis._nodes.values():
                sleep(0.1)
                mock_click_event_with_button(node, 1)

        thread = threading.Thread(target=self.quick_close, args=([vis, len(vis._nodes.values())*0.1 + 0.3]))
        hit_thread = threading.Thread(
            target=self.trigger_click, args=([mod, 'orect', 1,  0.2])
        )
        hit_thread2 = threading.Thread(
            target=clicker, args=([vis, 0.3])
        )
        thread.start()
        hit_thread.start()
        hit_thread2.start()
        vis.show()
        hit_thread.join()
        hit_thread2.join()
        thread.join()
        

