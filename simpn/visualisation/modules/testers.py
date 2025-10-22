"""
This module containers helpers for testing out the module pipeline 
through the `Visualisation` class.
"""

from .base import ModuleInterface
from simpn.visualisation.events import EventType, check_event

class CheckerModule(ModuleInterface):
    """Test module to verify all events are being dispatched correctly."""
    
    def __init__(self):
        super().__init__()
        self.create_called = False 
        self.pre_called = False 
        self.handle_event_called = False
        self.render_sim_called = False 
        self.render_ui_called = False 
        self.firing_called = False 
        self.post_called = False

    def handle_event(self, event, *args, **kwargs):
        """Handle all events through the unified event system."""
        self.handle_event_called = True
        
        if check_event(event, EventType.VISUALIZATION_CREATED):
            self.create_called = True
        elif check_event(event, EventType.PRE_EVENT_LOOP):
            self.pre_called = True
        elif check_event(event, EventType.POST_EVENT_LOOP):
            self.post_called = True
        elif check_event(event, EventType.BINDING_FIRED):
            self.firing_called = True
        elif check_event(event, EventType.RENDER_SIM):
            self.render_sim_called = True
        elif check_event(event, EventType.RENDER_UI):
            self.render_ui_called = True
        
        return True
