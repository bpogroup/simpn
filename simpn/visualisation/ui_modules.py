"""
UI modules for the visualization framework.

This module contains UI components that can be added to visualizations
to enhance the user interface with clocks, panels, and other controls.
"""
import pygame
from pygame.surface import Surface
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simpn.simulator import Describable

from simpn.visualisation.constants import TUE_GREY, TUE_BLUE, TUE_LIGHTBLUE, LINE_WIDTH, TEXT_SIZE, TUE_RED
from simpn.assets import get_img_asset
from simpn.visualisation.events import (
    EventType, IEventHandler, check_event, NODE_CLICKED, SELECTION_CLEAR
)
from simpn.visualisation.text import prevent_overflow_while_rendering


class UIClockModule:
    """
    This modules handles creating a clock in the top right corner to
    show the current simulation time to a predefined precision.

    :param `precision=2`:
        The preicision of the clock to show in the UI.
    """

    CLOCK_SIZE = (50, 50)
    OFFSET = 16

    def __init__(self, precision:int=2):
        self._precision = max(1, precision)
        self._time = 0
        self._target = 0
        self._pusher = 1.0 / (self._precision + 1)
        self._font_size = 12
        self._clock_img = None
        self._clock_rect = None
        self._font = None
        self._format = "0.0"

    def handle_event(self, event, *args, **kwargs):
        """Handle all events through the unified event system."""
        # Handle lifecycle events
        if check_event(event, EventType.VISUALIZATION_CREATED):
            self._time = event.sim.clock
            self._format = f"{round(self._time, self._precision)}"
            self._clock_img = pygame.image.load(get_img_asset("clock.png"))
            self._clock_img = pygame.transform.smoothscale(
                self._clock_img, self.CLOCK_SIZE
            )
            self._clock_rect = self._clock_img.get_rect()
            self._font = pygame.font.SysFont('Calibri', self._font_size)
        
        elif check_event(event, EventType.POST_EVENT_LOOP):
            # Update clock immediately after simulation step
            self._target = event.sim.clock
            self._time = self._target
            self._format = f"{round(self._time, self._precision)}"
        
        elif check_event(event, EventType.RENDER_UI):
            self._render_clock(event.window)
        
        # Handle pygame mouse events for clock interaction
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self._clock_rect and self._clock_rect.collidepoint(event.pos):
                # on left click increase precision
                if event.button == 1:
                    self._precision += 1
                # on right click decrease precision
                elif event.button == 3:
                    self._precision = max(1, self._precision - 1)

        return True
    
    def _render_clock(self, window: Surface):
        """Render the clock UI element."""
        if not self._clock_rect or not self._font:
            return
            
        self._clock_rect.center = (
            self.OFFSET + self._clock_rect.width // 2, 
            window.get_height() - self.OFFSET - self._font_size - self._clock_rect.height // 2
        )

        # draw holder for text
        clock_text_rect = pygame.Rect(
            self.OFFSET,
            window.get_height() - self.OFFSET - self._font_size,
            self._clock_rect.width,
            24
        )
        pygame.draw.rect(
            window, TUE_LIGHTBLUE,
            (clock_text_rect.x, clock_text_rect.y,
             clock_text_rect.width, clock_text_rect.height),
            border_radius=5
        )
        pygame.draw.rect(
            window, TUE_BLUE,
            (clock_text_rect.x, clock_text_rect.y,
             clock_text_rect.width, clock_text_rect.height),
            LINE_WIDTH,
            border_radius=5
        )
        
        # handle the font and show it on the screen
        font_length = len(self._format)
        show = self._format[:font_length]
        label = self._font.render(show, True, TUE_BLUE)
        while label.get_width() > clock_text_rect.width * 0.9:
            font_length -= 1
            show = self._format[:font_length]
            label = self._font.render(show, True, TUE_BLUE)

        text_x_pos = clock_text_rect.x \
            + (clock_text_rect.width//2) \
            - (label.get_width()// 2)
        text_y_pos = clock_text_rect.y \
            + (clock_text_rect.height//2) \
            - (label.get_height()//2)
        window.blit(label, (text_x_pos, text_y_pos))

        #blit image for clock
        window.blit(self._clock_img, self._clock_rect)
