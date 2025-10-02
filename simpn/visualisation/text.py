"""
A module which provide useful text related rendering helpers.
"""

from typing import Tuple
from pygame.surface import Surface

def prevent_overflow_while_rendering(
        surface:Surface,
        fonter:callable,
        width:float,
        text:str,
        initial_pos:Tuple[float,float],
        line_offset:float,
    ) -> Tuple[float, float]:
    """
    Helper function to ensure that the width of a text block
    does not overflow a given width. Returns the final position
    after preventing overflowing.
    """
    pos_x, pos_y = initial_pos

    while len(text) > 0:
        curr = 1
        rendered_text = fonter(text[:curr])
        while rendered_text.get_width() < width:
            curr += 1
            rendered_text = fonter(text[:curr])
            if (curr >= len(text)):
                break 

        text=text[curr:]
        surface.blit(rendered_text, (pos_x, pos_y))
        pos_y += rendered_text.get_height()
        if len(text) > 0 :
            pos_y += line_offset
    
    return (pos_x, pos_y)


