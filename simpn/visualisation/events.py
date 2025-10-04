"""
Module to handle the creation and handling of custom events
within the pygame loop.
"""

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Dict
from pygame.event import Event
from pygame import USEREVENT 

### list of known custom events
## Node related
NODE_CLICKED = "node.clicked"
SELECTION_CLEAR = "selection.clear"
    

def create_event(type:str, context:Dict[str,object]) -> Event:
    """
    Creates a custom pygame event to throw into the event que.
    """
    context = context
    context['named_type'] = type
    return Event(
        USEREVENT + 1,
        context
    )

def check_event(event:Event, type:str) -> bool:
    """
    Checks whether the event is a custom event and has the desired named
    type.
    """
    if event.type == USEREVENT +1 :
        try:
            return event.named_type == type
        except AttributeError:
            return False
    return False