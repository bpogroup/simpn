"""
Text rendering utilities for visualization.

This module provides helper functions for rendering text on pygame surfaces
with automatic text wrapping and overflow prevention.
"""

from typing import Tuple
from pygame.surface import Surface


def prevent_overflow_while_rendering(
    surface: Surface,
    fonter: callable,
    width: float,
    text: str,
    initial_pos: Tuple[float, float],
    line_offset: float,
) -> Tuple[float, float]:
    """
    Render text with automatic line wrapping to prevent overflow.
    
    This function renders text on a pygame surface, automatically breaking lines
    to ensure the text fits within the specified width. It returns the final
    position after rendering all text.
    
    :param surface: The pygame surface to render text on
    :param fonter: Callable that takes text and returns a rendered surface (e.g., font.render)
    :param width: Maximum width in pixels before wrapping
    :param text: The text string to render
    :param initial_pos: Starting (x, y) position for rendering
    :param line_offset: Vertical spacing in pixels between lines
    :return: Final (x, y) position after rendering all text
    """
    pos_x, pos_y = initial_pos

    while len(text) > 0:
        curr = 1
        rendered_text = fonter(text[:curr])
        while rendered_text.get_width() < width:
            curr += 1
            rendered_text = fonter(text[:curr])
            if curr >= len(text):
                break

        text = text[curr:]
        surface.blit(rendered_text, (pos_x, pos_y))
        pos_y += rendered_text.get_height()
        if len(text) > 0:
            pos_y += line_offset

    return (pos_x, pos_y)
