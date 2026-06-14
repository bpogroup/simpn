"""
Text rendering utilities for visualization.

This module provides helper functions for rendering text on pygame surfaces
with automatic text wrapping and overflow prevention.
"""

from typing import Tuple, Literal
from pygame.surface import Surface
from enum import StrEnum


LINEBREAK_MODES = Literal["word", "character"]


class LineBreakMode(StrEnum):
    WORD = "word"
    CHARACTER = "character"


def prevent_overflow_while_rendering(
    surface: Surface,
    fonter: callable,
    width: float,
    text: str,
    initial_pos: Tuple[float, float],
    line_offset: float,
    line_break_mode: LINEBREAK_MODES = 'character',
) -> Tuple[float, float]:
    """
    Render text with automatic line wrapping to prevent overflow.
    
    This function renders text on a pygame surface, automatically breaking lines
    to ensure the text fits within the specified width. It returns the final
    position after rendering all text.
    
    :param surface: The pygame surface to render text on
    :param fonter: Callable that takes text and returns a rendered surface
        (e.g., font.render)
    :param width: Maximum width in pixels before wrapping
    :param text: The text string to render
    :param initial_pos: Starting (x, y) position for rendering
    :param line_offset: Vertical spacing in pixels between lines
    :param line_break_mode: Whether to break lines on characters or words
    :return: Final (x, y) position after rendering all text
    """
    pos_x, pos_y = initial_pos

    while len(text) > 0:
        if line_break_mode == LineBreakMode.WORD:
            words = text.split()
            if not words:
                rendered_text = fonter(text)
                text = ""
            else:
                line = words[0]
                words_used = 1

                for word in words[1:]:
                    candidate = f"{line} {word}"
                    if fonter(candidate).get_width() > width:
                        break
                    line = candidate
                    words_used += 1

                rendered_text = fonter(line)
                text = " ".join(words[words_used:])
        else:
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
