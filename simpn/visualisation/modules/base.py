"""
This module contains the glue and blueprints for making a visualisation
module to add new features to a visualisation on demand. The modules are
instantiated and passed to the `Visualisation` class from 
`simpn.visualisation`, where the class will pass along information and 
allow the visualisation to be altered at predefined hook locations.

All modules use a unified event-driven architecture. All lifecycle hooks
and rendering callbacks are delivered as events through the centralized
event dispatcher. Modules only need to implement handle_event(event) -> bool.
"""

from pygame.event import Event
from simpn.visualisation.events import EventType, check_event

class ModuleInterface():
    """
    Base class for visualization modules using unified event-driven architecture.
    
    All interactions with the visualization system happen through events:
    - VISUALIZATION_CREATED: Setup assets
    - PRE_EVENT_LOOP: Called at start of each game loop
    - POST_EVENT_LOOP: Called at end of each game loop
    - BINDING_FIRED: Called when simulation binding fires
    - RENDER_SIM: Draw simulation elements
    - RENDER_UI: Draw UI elements
    - NODE_CLICKED, SELECTION_CLEAR: User interactions
    
    Example:
        class MyModule(ModuleInterface):
            def handle_event(self, event: Event) -> bool:
                if check_event(event, EventType.VISUALIZATION_CREATED):
                    self.setup(event.sim)
                elif check_event(event, EventType.RENDER_UI):
                    self.draw(event.window)
                return True  # Propagate to other modules
    """

    def __init__(self):
        pass 

    def handle_event(self, event: Event) -> bool:
        """
        Handle any event from the visualization system.
        
        This is the single entry point for all interactions. Check the event type
        and respond accordingly.
        
        :param event: The event to handle (check event.event_type)
        :return: True to propagate to other modules, False to stop propagation
        """
        return True



