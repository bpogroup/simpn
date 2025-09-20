import pygame

def mock_click_event_with_button(rect:pygame.Rect, button:int=1):
    """
    Posts a mock event to trigger a click on the given rect.
    Optionally a button type can be passed along, expected values are\:
    * `1` - left mouse click
    * `2` - middle mouse click
    * `3` - right mouse click
    """
    pygame.event.post(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {'button' : button, 'pos' : rect.center}
        )
    )