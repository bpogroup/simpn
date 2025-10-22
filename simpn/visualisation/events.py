"""
Module to handle the creation and handling of custom events
within the pygame loop.

This module provides a unified event system with:
1. Centralized event type definitions (EventType enum)
2. Event dispatcher (EventDispatcher class)
3. Event handler interface (IEventHandler)
4. Uniform event production (create_event function)

Example usage:
    # Define a handler
    class MyHandler(IEventHandler):
        def handle_event(self, event: Event) -> bool:
            if check_event(event, EventType.NODE_CLICKED):
                print(f"Clicked: {event.node}")
            return True  # Propagate to other handlers
    
    # Create dispatcher and register handlers
    dispatcher = EventDispatcher()
    dispatcher.register_handler(MyHandler())
    
    # Create and dispatch an event
    evt = create_event(EventType.NODE_CLICKED, node=my_node)
    dispatcher.dispatch(evt)
"""

from enum import Enum, auto
from typing import List, Protocol
from pygame.event import Event
from pygame import USEREVENT 


class EventType(Enum):
    """
    Centralized definition of all custom event types in the visualization system.
    
    To add a new event type:
    1. Add it to this enum
    2. Add it to the legacy string mapping if backward compatibility is needed
    3. Document when/where it should be fired
    """
    # Lifecycle events
    VISUALIZATION_CREATED = auto()      # Fired once during visualization initialization; includes 'sim' attribute
    PRE_EVENT_LOOP = auto()             # Fired at start of each game loop; includes 'sim' attribute
    POST_EVENT_LOOP = auto()            # Fired at end of each game loop; includes 'sim' attribute
    BINDING_FIRED = auto()              # Fired when simulation binding fires; includes 'fired' and 'sim' attributes
    
    # Rendering events
    RENDER_SIM = auto()                 # Fired during simulation rendering; includes 'screen' attribute
    RENDER_UI = auto()                  # Fired during UI rendering; includes 'window' attribute
    
    # User interaction events
    NODE_CLICKED = auto()               # Fired when a node is clicked; includes 'node' attribute
    SELECTION_CLEAR = auto()            # Fired when selection is cleared; no additional attributes


# Legacy string constants for backward compatibility
NODE_CLICKED = "node.clicked"
SELECTION_CLEAR = "selection.clear"


class IEventHandler(Protocol):
    """
    Interface for event handlers.
    
    Any class that wants to handle events should implement this interface.
    """
    
    def handle_event(self, event: Event) -> bool:
        """
        Handle a pygame event.
        
        :param event: The pygame event to handle
        :return: True if the event should propagate to other handlers, False to stop propagation
        """
        ...


class EventDispatcher:
    """
    Central event dispatcher that receives events and forwards them to registered handlers.
    
    Handlers are called in the order they were registered. If a handler returns False,
    event propagation stops.
    """
    
    def __init__(self):
        self._handlers: List[IEventHandler] = []
    
    def register_handler(self, handler: IEventHandler) -> None:
        """
        Register an event handler.
        
        :param handler: The handler to register (must implement IEventHandler)
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def unregister_handler(self, handler: IEventHandler) -> None:
        """
        Unregister an event handler.
        
        :param handler: The handler to unregister
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    def dispatch(self, event: Event) -> bool:
        """
        Dispatch an event to all registered handlers.
        
        :param event: The event to dispatch
        :return: True if the event propagated to all handlers, False if stopped early
        """
        for handler in self._handlers:
            if not handler.handle_event(event):
                return False
        return True
    
    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()


def create_event(event_type: EventType | str, **kwargs) -> Event:
    """
    Creates a custom pygame event.
    
    This is the uniform way to produce events in the system.
    
    :param event_type: The type of event (EventType enum or legacy string)
    :param kwargs: Event attributes (e.g., node=my_node, position=(x,y))
    :return: A pygame Event
    """
    # Convert string to enum if needed
    if isinstance(event_type, str):
        event_type = _string_to_event_type(event_type)
    
    return Event(
        USEREVENT + 1,
        event_type=event_type,
        **kwargs
    )


def check_event(event: Event, event_type: EventType | str) -> bool:
    """
    Checks whether the event matches the desired type.
    
    :param event: The pygame event to check
    :param event_type: The type to check for (EventType enum or legacy string)
    :return: True if the event matches the type
    """
    if event.type != USEREVENT + 1:
        return False
    
    # Convert string to enum if needed
    if isinstance(event_type, str):
        event_type = _string_to_event_type(event_type)
    
    return getattr(event, 'event_type', None) == event_type


def _string_to_event_type(type_str: str) -> EventType:
    """Convert legacy string event type to EventType enum."""
    mapping = {
        NODE_CLICKED: EventType.NODE_CLICKED,
        SELECTION_CLEAR: EventType.SELECTION_CLEAR,
    }
    return mapping.get(type_str, None)