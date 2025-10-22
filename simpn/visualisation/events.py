from enum import Enum, auto
from typing import List, Protocol
from pygame.event import Event
from pygame import USEREVENT 


class EventType(Enum):
    VISUALIZATION_CREATED = auto()      # Fired when visualization is created; includes 'sim' attribute
    PRE_EVENT_LOOP = auto()             # Fired at start of each game loop; includes 'sim' attribute
    POST_EVENT_LOOP = auto()            # Fired at end of each game loop; includes 'sim' attribute
    BINDING_FIRED = auto()              # Fired when simulation binding fires; includes 'fired' and 'sim' attributes
    RENDER_SIM = auto()                 # Fired during simulation rendering; includes 'screen' attribute
    RENDER_UI = auto()                  # Fired during UI rendering; includes 'window' attribute
    NODE_CLICKED = auto()               # Fired when a node is clicked; includes 'node' attribute
    SELECTION_CLEAR = auto()            # Fired when selection is cleared; no additional attributes


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

    Handlers can be registered to listen to specific event types. If none are specified, they listen to all events.
    """

    def __init__(self):
        self._handlers: dict[EventType, List[IEventHandler]] = {}

    def register_handler(self, handler: IEventHandler, listens_to: List[EventType] = None) -> None:
        """
        Register an event handler to listen to specific event types.
        Also sets the event dispatcher reference on the handler.
        
        :param handler: The handler to register (must implement IEventHandler)
        :param listens_to: The event types to listen to (defaults to all events)
        """

        if listens_to is None:
            listens_to = list(EventType)
        for event_type in listens_to:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
        handler._event_dispatcher = self

    def unregister_handler(self, handler: IEventHandler) -> None:
        """
        Unregister an event handler.
        Also clears the event dispatcher reference on the handler.
        
        :param handler: The handler to unregister
        """
        for event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
        handler._event_dispatcher = None

    def dispatch(self, source, event: Event) -> bool:
        """
        Dispatch an event to all registered handlers except the source to prevent infinite loops.
        
        :param event: The event to dispatch
        :return: True if the event propagated to all handlers, False if stopped early
        """
        for handler in self._handlers.get(event.event_type, []):
            if handler is not source:
                if not handler.handle_event(event):
                    return False
        return True
    

def create_event(event_type: EventType | str, **kwargs) -> Event:
    """
    Creates a custom pygame event.
    
    This is the uniform way to produce events in the system.
    
    :param event_type: The type of event (EventType enum or legacy string)
    :param kwargs: Event attributes (e.g., node=my_node, position=(x,y))
    :return: A pygame Event
    """    
    return Event(
        USEREVENT + 1,
        event_type=event_type,
        **kwargs
    )

def check_event(event: Event, event_type: EventType | str) -> bool:
    """
    Check if a pygame event matches a specific event type.
    """
    return getattr(event, 'event_type', None) == event_type