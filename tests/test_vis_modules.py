import unittest
from time import time, sleep
import threading

import pygame

from simpn.simulator import SimProblem, SimToken
from simpn.helpers import Place, Transition
from simpn.visualisation import Visualisation
from simpn.visualisation.modules.testers import CheckerModule


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
        self.assertEqual(len(vis._modules), 0)

        vis = Visualisation(
            self.problem,
            extra_modules=[
                CheckerModule(),
            ]
        )
        self.assertEqual(len(vis._modules), 1)


        vis = Visualisation(
            self.problem,
            extra_modules=[
                CheckerModule(),
                CheckerModule(),
            ]
        )
        self.assertEqual(len(vis._modules), 2)

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

