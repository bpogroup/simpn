import pygame
from pygame.event import Event
from simpn.visualisation import Node
from simpn.visualisation.events import EventType


class TestEventHandler:
    """
    A test event handler that tracks which event types have been fired.
    Can be registered with the main window's event dispatcher for testing purposes.
    """
    
    def __init__(self):
        """Initialize the event handler with all event tracking flags set to False."""
        self._event_dispatcher = None
        self.visualization_created = False
        self.pre_event_loop_called = False
        self.post_event_loop_called = False
        self.binding_fired_called = False
        self.render_sim_called = False
        self.render_ui_called = False
        self.node_clicked_called = False
        self.selection_clear_called = False
        
    def handle_event(self, event: Event) -> bool:
        """
        Handle an event and track that it was received.
        
        :param event: The pygame event to handle
        :return: True to allow event propagation to continue
        """
        event_type = getattr(event, 'event_type', None)
        
        if event_type == EventType.VISUALIZATION_CREATED:
            self.visualization_created = True
        elif event_type == EventType.PRE_EVENT_LOOP:
            self.pre_event_loop_called = True
        elif event_type == EventType.POST_EVENT_LOOP:
            self.post_event_loop_called = True
        elif event_type == EventType.BINDING_FIRED:
            self.binding_fired_called = True
        elif event_type == EventType.RENDER_SIM:
            self.render_sim_called = True
        elif event_type == EventType.RENDER_UI:
            self.render_ui_called = True
        elif event_type == EventType.NODE_CLICKED:
            self.node_clicked_called = True
        elif event_type == EventType.SELECTION_CLEAR:
            self.selection_clear_called = True
            
        return True  # Allow event to propagate to other handlers


def mock_click_event_with_button(viz:pygame.Rect, button:int=1):
    """
    Posts a mock event to trigger a click on the given rect.
    Optionally a button type can be passed along, expected values are\:
    * `1` - left mouse click
    * `2` - middle mouse click
    * `3` - right mouse click
    """

    if isinstance(viz, pygame.Rect):
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {'button' : button, 'pos' : viz.center}
            )
        )
    elif isinstance(viz, Node):
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {'button' : button, 'pos' : viz._pos}
            )
        )
    else:
        raise ValueError(f"The handling of class of viz has not been implemented :: {viz.__class__}")