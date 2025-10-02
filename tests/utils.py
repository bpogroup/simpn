import pygame
from simpn.visualisation import Node

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