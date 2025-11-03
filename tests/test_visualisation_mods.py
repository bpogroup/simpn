from tests.dummy_problems import create_dummy_bpmn
from tests.utils import run_visualisation_for
from simpn.visualisation.model_panel_mods import FiredTracker, FiredTrackerModule
from simpn.visualisation.events import (
    create_event,
    register_handler,
    reset_dispatcher,
    EventType,
    dispatch,
    get_dispatcher,
)

import unittest
import pygame

pygame.init()


class TestFiringTrackingMod(unittest.TestCase):

    def setUp(self):
        self.problem = create_dummy_bpmn()
        self.mod = FiredTrackerModule()
        reset_dispatcher()

    def tearDown(self):
        reset_dispatcher()

    def test_join(self):
        register_handler(self.mod)
        dispatcher = get_dispatcher()

        handlers = set()
        for group in dispatcher._handlers.values():
            for handler in group:
                handlers.add(handler)

        self.assertEqual(len(handlers), 1)

    def test_description(self):
        tracker = FiredTracker(bindings=["foo", "bar"])

        des = tracker.describe()

        self.assertEqual(len(des), 7)

    def test_fire(self):
        register_handler(self.mod)
        binding = self.problem.bindings()[0]
        dispatch(create_event(EventType.BINDING_FIRED, fired=binding), self)

        self.assertGreaterEqual(len(self.mod.que), 1)

        for _ in range(3):
            binding = self.problem.bindings()[0]
            dispatch(create_event(EventType.BINDING_FIRED, fired=binding), self)

        self.assertGreaterEqual(len(self.mod.que), 4)

    def test_reset(self):
        register_handler(self.mod)
        binding = self.problem.bindings()[0]
        dispatch(create_event(EventType.BINDING_FIRED, fired=binding), self)

    def test_render_draws_content(self):
        surface = pygame.Surface((400, 400))
        surface.fill((0, 0, 0))  # Fill with black

        # Capture initial state
        initial_sum = pygame.surfarray.array3d(surface).sum()

        register_handler(self.mod)

        # Add some fired bindings to have content to render
        binding = self.problem.bindings()[0]
        dispatch(create_event(EventType.BINDING_FIRED, fired=binding), self)

        dispatch(create_event(EventType.RENDER_UI, window=surface), self)

        # Check if surface changed
        final_sum = pygame.surfarray.array3d(surface).sum()
        self.assertNotEqual(
            initial_sum, final_sum, "Surface should be modified after rendering"
        )

    def test_render_empty_que(self):
        surface = pygame.Surface((400, 400))
        register_handler(self.mod)
        # Render without firing any bindings
        dispatch(create_event(EventType.RENDER_UI, window=surface), self)
        # Should not raise any errors

    def test_multiple_fires_and_render(self):
        surface = pygame.Surface((400, 400))
        register_handler(self.mod)

        for _ in range(5):
            binding = self.problem.bindings()[0]
            dispatch(create_event(EventType.BINDING_FIRED, fired=binding), self)

        self.assertEqual(len(self.mod.que), 5)
        dispatch(create_event(EventType.RENDER_UI, window=surface), self)

    def test_reset_clears_que(self):
        register_handler(self.mod)
        binding = self.problem.bindings()[0]

        for _ in range(3):
            dispatch(create_event(EventType.BINDING_FIRED, fired=binding), self)

        self.assertGreaterEqual(len(self.mod.que), 1)

        dispatch(create_event(EventType.SIM_RESET_SIM_STATE), self)
        self.assertEqual(len(self.mod.que), 0, "Queue should be empty after reset")

    def test_visualisation_with_mod(self):
        run_visualisation_for(
            1500,
            sim_problem=self.problem,
            include_default_modules=False,
            extra_modules=[self.mod]
        )