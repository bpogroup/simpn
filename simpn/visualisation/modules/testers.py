"""
This module containers helpers for testing out the module pipeline 
through the `Visualisation` class.
"""

from .base import ModuleInterface

class CheckerModule(ModuleInterface):

    def create(self, sim, *args, **kwargs):
        self.create_called = True 
        self.pre_called = False 
        self.handle_event_called = False
        self.render_sim_called = False 
        self.render_ui_called = False 
        self.firing_called = False 
        self.post_called = False 

    def pre_event_loop(self, sim, *args, **kwargs):
        # print("[Checking] pre_event_loop called...")
        self.pre_called = True

    def handle_event(self, event, *args, **kwargs):
        self.handle_event_called = True 

    def render_sim(self, screen, *args, **kwargs):
        self.render_sim_called = True 

    def render_ui(self, window, *args, **kwargs):
        self.render_ui_called = True 

    def firing(self, fired, sim, *args, **kwargs):
        self.firing_called = True

    def post_event_loop(self, sim, *args, **kwargs):
        self.post_called = True
