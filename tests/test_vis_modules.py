import unittest
from time import time, sleep
import threading
from tests.utils import mock_click_event_with_button

import pygame

from simpn.simulator import SimProblem, SimToken
from simpn.helpers import Place, Transition
from simpn.visualisation import Visualisation
from simpn.visualisation.modules.testers import CheckerModule
from simpn.visualisation.modules.ui import UIClockModule


class PipelineTests(unittest.TestCase):

    def setUp(self):
        self.problem = SimProblem()

        class Start(Place):
            model=self.problem
            name="start"
            amount=1

        class Action(Transition):
            model=self.problem
            name="Task One"
            incoming = ["start"]
            outgoing = ["end"]

            def behaviour(c):
                return [
                    SimToken(c, delay=1)
                ]
    
    @staticmethod
    def quick_close(vis, wait_time=0.2):
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
        self.assertEqual(len(vis._modules), 1)

        vis = Visualisation(
            self.problem,
            extra_modules=[
                CheckerModule(),
            ]
        )
        self.assertEqual(len(vis._modules), 2)


        vis = Visualisation(
            self.problem,
            extra_modules=[
                CheckerModule(),
                CheckerModule(),
            ]
        )
        self.assertEqual(len(vis._modules), 3)

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
        from random import uniform
        self.problem = SimProblem()

        class Start(Place):
            model=self.problem
            name="start"
            amount=5

        class Resource(Place):
            model=self.problem
            name="resource"
            amount=1

        class Action(Transition):
            model=self.problem
            name="Task One"
            incoming = ["start", "resource"]
            outgoing = ["end", "resource"]

            def behaviour(c, r):
                return [
                    SimToken(c, delay=1),
                    SimToken(r, delay=uniform(1,5))
                ]
    
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


    



        

