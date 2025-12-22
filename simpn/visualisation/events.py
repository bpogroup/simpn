"""
Event system for visualization components.

This module provides an event dispatching system for communication between
visualization components. It defines event types, handler interfaces, and utilities
for creating and checking events.

Classes:
    EventType: Enum defining all possible event types in the visualization system.
    IEventHandler: Protocol (interface) for classes that handle events.
    EventDispatcher: Central dispatcher that routes events to registered handlers.

Functions:
    create_event: Factory function for creating pygame events with custom attributes.
    check_event: Utility to check if an event matches a specific type.
"""

from enum import Enum, auto
from typing import List, Protocol, Union, Callable
from pygame.event import Event
from pygame import USEREVENT


class EventType(Enum):
    """
    Enumeration of all event types used in the visualization system.

    Each event type represents a specific occurrence in the visualization lifecycle
    or user interaction that components may want to respond to.
    """

    VISUALIZATION_CREATED = (
        auto()
    )  # Fired when visualization is created; includes 'sim' attribute
    PRE_EVENT_LOOP = (
        auto()
    )  # Fired at start of each game loop; includes 'sim' attribute
    POST_EVENT_LOOP = auto()  # Fired at end of each game loop; includes 'sim' attribute
    BINDING_FIRED = (
        auto()
    )  # Fired when simulation binding fires; includes 'fired' and 'sim' attributes
    RENDER_SIM = (
        auto()
    )  # Fired during simulation rendering; includes 'screen' attribute
    RENDER_PRE_NODES = auto()
    RENDER_POST_NODES = auto()
    RENDER_UI = auto()  # Fired during UI rendering; includes 'window' attribute
    RENDER_POST_UI = auto()
    NODE_CLICKED = auto()  # Fired when a node is clicked; includes 'node' attribute
    SELECTION_CLEAR = (
        auto()
    )  # Fired when selection is cleared; no additional attributes

    SIM_ZOOM = auto()
    SIM_UPDATE = auto()
    SIM_RENDERED = auto()
    SIM_PLAY = auto()
    SIM_PLAYING = auto()
    SIM_STOP = auto()
    SIM_RESET = auto()
    SIM_CLOSE = auto()
    SIM_CLICK = auto()
    SIM_PRESS = auto()
    SIM_MOVE = auto()
    SIM_HOVER = auto()
    SIM_RESET_LAYOUT = auto()
    SIM_RESET_SIM_STATE = auto()
    SIM_RELEASE = auto()
    SIM_RESIZE = auto()

    CENTRAL_PANEL_ADD = auto()
    CENTRAL_PANEL_REMOVE = auto()
    CENTRAL_PANEL_ACTIVATE = auto()

    CLOCK_PREC_INC = auto()
    CLOCK_PREC_DEC = auto()

    DES_POST = auto()

    HLIGHT_FOCUS = auto()
    HLIGHT_DEFOCUS = auto()
    HLIGHT_HOVER = auto()
    HLIGHT_UNHOVER = auto()

    DEBUG_LEVEL = auto()

    ALL = auto()

    def __eq__(self, value):
        if self is EventType.ALL and isinstance(value, EventType):
            return True
        if value is EventType.ALL and isinstance(self, EventType):
            return True
        return super().__eq__(value)

    def __hash__(self):
        return super().__hash__()


class IEventHandler(Protocol):
    """
    Protocol (interface) for event handlers in the visualization system.

    Any class that wants to receive and handle events must implement this protocol.
    The protocol requires two methods: handle_event and listen_to.

    Example:
        ```python
        class MyHandler:
            def handle_event(self, event: Event) -> bool:
                if check_event(event, EventType.NODE_CLICKED):
                    print(f"Node clicked: {event.node}")
                return True

            def listen_to(self) -> List[EventType]:
                return [EventType.NODE_CLICKED, EventType.BINDING_FIRED]
        ```
    """

    def handle_event(self, event: Event) -> bool:
        """
        Handle a pygame event.

        This method is called by the EventDispatcher when an event of a type this
        handler listens to is dispatched.

        :param event: The pygame event to handle (includes event_type attribute)
        :return: True to allow event to propagate to other handlers, False to stop
        propagation.
        """
        raise NotImplementedError("Must implement handle_event method")

    def listen_to(self) -> List[EventType]:
        """
        Specify which event types this handler wants to receive.

        Only events of the returned types will be passed to this handler's
        handle_event method.

        :return: List of EventType enums this handler is interested in
        """
        raise NotImplementedError("Must implement listen_to method")


class EventDispatcher:
    """
    Central event dispatcher that routes events to registered handlers.

    This class manages event handlers and dispatches events to them in registration
    order.
    Handlers are organized by the event types they listen to for efficient dispatch.

    If a handler returns False from handle_event, event propagation stops immediately.
    This allows handlers to prevent other handlers from seeing an event if appropriate.

    Automatically sets the _event_dispatcher attribute on registered handlers to allow
    handlers to dispatch their own events if needed.
    """

    def __init__(self):
        """Initialize an empty event dispatcher."""
        self._handlers: dict[EventType, List[IEventHandler]] = {}
        self._globals: List[IEventHandler] = []

    def register_handler(self, handler: IEventHandler) -> None:
        """
        Register an event handler to receive specific event types.

        The handler's listen_to() method is called to determine which event types
        it wants to receive. The handler is added to the dispatch list for each
        of those event types.

        Also sets handler._event_dispatcher = self to allow the handler to dispatch
        events.

        :param handler: The handler to register (must implement IEventHandler protocol)
        """
        listens_to = handler.listen_to()

        for event_type in listens_to:
            if event_type is EventType.ALL:
                self._globals.append(handler)
                continue
            elif event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
        handler._event_dispatcher = self

    def unregister_handler(self, handler: IEventHandler) -> None:
        """
        Unregister an event handler from all event types.

        Removes the handler from all event type dispatch lists and clears its
        _event_dispatcher reference.

        :param handler: The handler to unregister
        """
        for event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            if handler in self._globals:
                self._globals.remove(handler)
        handler._event_dispatcher = None

    def dispatch(self, source, event: Event) -> bool:
        """
        Dispatch an event to all registered handlers (except the source).

        Handlers are called in registration order for the event's type. If any handler
        returns False, propagation stops and remaining handlers are not called.

        The source parameter prevents infinite event loops - the source handler
        will not receive the event it dispatched.

        :param source: The object dispatching the event (will not receive it)
        :param event: The pygame Event to dispatch (must have event_type attribute)
        :return: True if event propagated to all handlers, False if stopped early
        """
        for handler in self._handlers.get(event.event_type, []):
            if handler is not source:
                if not handler.handle_event(event):
                    return False
        for handler in self._globals:
            if not handler.handle_event(event):
                return False
        return True


__dispatcher__ = None


def get_dispatcher() -> EventDispatcher:
    """
    Returns the current dispatcher.
    """
    global __dispatcher__

    if not __dispatcher__:
        __dispatcher__ = EventDispatcher()

    return __dispatcher__


def reset_dispatcher():
    """
    Danger this clears the dispatcher and may brake the implementation of
    running visualisations.

    You better know what your doing if you are calling this function.
    """
    global __dispatcher__
    __dispatcher__ = None


def dispatch(event: Event, source: object = None):
    """
    Sends an event to be dispatcher for anyone that listens to the event.
    """
    dispatcher = get_dispatcher()
    dispatcher.dispatch(source, event)


class OneShotHandler(IEventHandler):
    """
    A quick shorthand for creating a hanlder without the fuss. The purpose
    is to allow for modules to directly link an event to a single callback
    rather than building out a long switch statement within their modules.

    ^^^^
    Examples
    ^^^^

    .. code-block :: python
        dispatcher.register_handler(OneShotHandler('foobar', lambda x: foo(x)))
    """

    def __init__(self, event: Event, callback: Callable, passthrough: bool = True):
        super().__init__()
        self._event = event
        self._callback = callback
        self._passthrough = passthrough

    def listen_to(self):
        return [self._event]

    def handle_event(self, event):
        try:
            if self._passthrough:
                return self._callback(event)
            else:
                return self._callback()
        except Exception as e:
            print(f"Error on one-shot-callback: {str(self)}")
            raise e

    def __str__(self):
        return str((str(self._event), str(self._callback), self._passthrough))


def listen_to(event: Event, callback: Callable, passthrough: bool = True):
    """
    Register a new callback for an event that appears on the event que.
    Creates a OneShotHandler for the dispatcher.

    :param event: the event to listen for
    :param callback: the function to call when event is seen
    :param passthrough: whether to passthrough the event to the callback
    """
    dispatcher = get_dispatcher()
    dispatcher.register_handler(OneShotHandler(event, callback, passthrough))


def register_handler(handler: IEventHandler):
    """
    Registers a handler on the current dispatcher.

    :param handler: the handler to be registered
    """
    get_dispatcher().register_handler(handler)


def unregister_handler(handler: IEventHandler):
    """
    Removes a handler from the current dispatcher.

    :param handler: the handler to be removed
    """
    get_dispatcher().unregister_handler(handler)


def create_event(event_type: Union[EventType, str], **kwargs) -> Event:
    """
    Create a custom pygame event with the specified type and attributes.

    This is the standard way to create events in the visualization system. The event
    will have an event_type attribute set to the provided type, plus any additional
    keyword arguments as attributes.

    Example:
        ```python
        evt = create_event(EventType.NODE_CLICKED, node=my_node, position=(100, 200))
        dispatcher.dispatch(self, evt)
        ```

    :param event_type: The type of event (EventType enum or legacy string
        for compatibility)
    :param kwargs: Additional event attributes (e.g., node=..., sim=...,
        position=...)
    :return: A pygame Event with USEREVENT+1 as the pygame event type
    """
    return Event(USEREVENT + 1, event_type=event_type, **kwargs)


def check_event(event: Event, event_type: Union[EventType, str]) -> bool:
    """
    Check if a pygame event matches a specific event type.

    This is a convenience function for checking events in handle_event methods.

    Example:
        ```python
        def handle_event(self, event):
            if check_event(event, EventType.NODE_CLICKED):
                # Handle node click
                pass
        ```

    :param event: The pygame Event to check
    :param event_type: The event type to check for (EventType enum or string)
    :return: True if the event's event_type attribute matches, False otherwise
    """
    return getattr(event, "event_type", None) == event_type
