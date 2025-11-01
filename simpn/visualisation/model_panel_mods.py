"""
Additional visualization modules for the model panel.

This module provides supplementary components that can be rendered on the model panel
to enhance the visualization with additional information and controls.

Classes:
    ClockModule: Displays the current simulation time with configurable precision.
"""

import pygame
from PyQt6.QtCore import Qt
from pygame.surface import Surface
from simpn.visualisation.constants import TUE_BLUE, TUE_LIGHTBLUE, LINE_WIDTH
from simpn.assets import get_img_asset
from simpn.visualisation.events import (
    EventType, IEventHandler, check_event, dispatch, create_event, listen_to
)


class ClockModule(IEventHandler):
    """
    Clock module for displaying simulation time on the visualization.

    Renders a clock icon with the current simulation time below it. The time display
    precision can be adjusted dynamically to show more or fewer decimal places.
    
    This module listens to visualization events to update the displayed time when
    the simulation progresses.

    :param precision: Number of decimal places to show in the time display (default: 2, minimum: 1)
    """

import pygame
from pygame.surface import Surface
from simpn.visualisation.constants import TUE_BLUE, TUE_LIGHTBLUE, LINE_WIDTH
from simpn.assets import get_img_asset
from simpn.visualisation.events import EventType, IEventHandler, check_event


class ClockModule(IEventHandler):
    """
    This modules handles creating a clock to
    show the current simulation time to a predefined precision.

    :param `precision=2`:
        The preicision of the clock to show in the UI.
    """

    CLOCK_SIZE = (50, 50)
    OFFSET = 16

    def __init__(self, precision: int = 2):
        """
        Initialize the clock module.
        
        :param precision: Number of decimal places for time display (minimum: 1)
        """
        self._precision = max(1, precision)
        self._time = 0
        self._target = 0
        self._pusher = 1.0 / (self._precision + 1)
        self._font_size = 12
        self._clock_img = None
        self._clock_rect = None
        self._font = None
        self._format = "0.0"

        listen_to(
            EventType.CLOCK_PREC_INC,
            self.increase_precision,
            False
        )
        listen_to(
            EventType.CLOCK_PREC_DEC,
            self.decrease_precision,
            False
        )

    def listen_to(self):
        """
        Specify which event types this handler listens to.
        
        :return: List of EventType enums (VISUALIZATION_CREATED, POST_EVENT_LOOP, RENDER_UI)
        """
        return [
            EventType.VISUALIZATION_CREATED,
            EventType.POST_EVENT_LOOP,
            EventType.RENDER_UI,
            EventType.SIM_CLICK
        ]

    def handle_event(self, event, *args, **kwargs):
        """
        Handle visualization events to update and render the clock.
        
        Responds to:
        - VISUALIZATION_CREATED: Initialize clock graphics and font
        - POST_EVENT_LOOP: Update displayed time after simulation step
        - RENDER_UI: Draw the clock on the screen
        
        :param event: The pygame event to handle
        :return: True to allow event propagation
        """
        # Handle lifecycle events
        if check_event(event, EventType.VISUALIZATION_CREATED):
            self._time = event.sim.clock
            self._format = f"{round(self._time, self._precision)}"
            self._clock_img = pygame.image.load(get_img_asset("clock.png"))
            self._clock_img = pygame.transform.smoothscale(
                self._clock_img, self.CLOCK_SIZE
            )
            self._clock_rect = self._clock_img.get_rect()
            self._font = pygame.font.SysFont("Calibri", self._font_size)

        elif check_event(event, EventType.POST_EVENT_LOOP):
            # Update clock immediately after simulation step
            self._target = event.sim.clock
            self._time = self._target
            self._format = f"{round(self._time, self._precision)}"

        elif check_event(event, EventType.RENDER_UI):
            self._render_clock(event.window)

        elif check_event(event, EventType.SIM_CLICK):
            if self._clock_rect:
                x, y = event.pos['x'], event.pos['y']
                if self._clock_rect.collidepoint(
                    x,
                    y
                ):
                    if event.button == Qt.MouseButton.LeftButton:
                        dispatch(
                            create_event(
                                EventType.CLOCK_PREC_INC
                            )
                        )
                    elif event.button == Qt.MouseButton.RightButton:
                        dispatch(
                            create_event(
                                EventType.CLOCK_PREC_DEC
                            )
                        )

        return True

    def increase_precision(self):
        """
        Increase the number of decimal places shown in the time display by 1.
        """
        self._precision += 1
        self._pusher = 1.0 / (self._precision + 1)
        self._format = f"{round(self._time, self._precision)}"

    def decrease_precision(self):
        """
        Decrease the number of decimal places shown in the time display by 1.
        
        The precision will not go below 1 decimal place.
        """
        self._precision = max(1, self._precision - 1)
        self._pusher = 1.0 / (self._precision + 1)
        self._format = f"{round(self._time, self._precision)}"

    def _render_clock(self, window: Surface):
        """
        Render the clock icon and time display on the pygame surface.
        
        Draws a clock icon with a text box below showing the current simulation time.
        Positioned at the bottom-left corner of the window.
        
        :param window: The pygame surface to draw on
        """
        if not self._clock_rect or not self._font:
            return

        self._clock_rect.center = (
            self.OFFSET + self._clock_rect.width // 2,
            window.get_height()
            - self.OFFSET
            - self._font_size
            - self._clock_rect.height // 2,
        )

        # draw holder for text
        clock_text_rect = pygame.Rect(
            self.OFFSET,
            window.get_height() - self.OFFSET - self._font_size,
            self._clock_rect.width,
            24,
        )
        pygame.draw.rect(
            window,
            TUE_LIGHTBLUE,
            (
                clock_text_rect.x,
                clock_text_rect.y,
                clock_text_rect.width,
                clock_text_rect.height,
            ),
            border_radius=5,
        )
        pygame.draw.rect(
            window,
            TUE_BLUE,
            (
                clock_text_rect.x,
                clock_text_rect.y,
                clock_text_rect.width,
                clock_text_rect.height,
            ),
            LINE_WIDTH,
            border_radius=5,
        )

        # handle the font and show it on the screen
        font_length = len(self._format)
        show = self._format[:font_length]
        label = self._font.render(show, True, TUE_BLUE)
        while label.get_width() > clock_text_rect.width * 0.9:
            font_length -= 1
            show = self._format[:font_length]
            label = self._font.render(show, True, TUE_BLUE)

        text_x_pos = (
            clock_text_rect.x + (clock_text_rect.width // 2) - (label.get_width() // 2)
        )
        text_y_pos = (
            clock_text_rect.y
            + (clock_text_rect.height // 2)
            - (label.get_height() // 2)
        )
        window.blit(label, (text_x_pos, text_y_pos))

        # blit image for clock
        window.blit(self._clock_img, self._clock_rect)
