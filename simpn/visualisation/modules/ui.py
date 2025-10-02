"""
This module contains modules for ui compontents used in the visualisation
of simulation problems.
"""
import pygame
from pygame.surface import Surface
from dataclasses import dataclass, field
from typing import List

from simpn.visualisation.modules.base import ModuleInterface
from simpn.visualisation.base import TUE_GREY, TUE_BLUE, TUE_LIGHTBLUE, LINE_WIDTH, TEXT_SIZE, TUE_RED, LINE_WIDTH
from simpn.assets import get_img_asset
from simpn.visualisation.events import check_event, NODE_CLICKED, SELECTION_CLEAR
from simpn.visualisation.text import prevent_overflow_while_rendering
from simpn.simulator import Describable

class UIClockModule(ModuleInterface):
    """
    This modules handles creating a clock in the top right corner to
    show the current simulation time to a predefined precision.

    :param `precision=2`:
        The preicision of the clock to show in the UI.
    """

    CLOCK_SIZE = (50, 50)
    OFFSET = 16

    def __init__(self, precision:int=2):
        super().__init__()
        self._precision = max(1, precision)
        self._time = 0
        self._target = 0
        self._pusher = 1.0 / (self._precision + 1)
        self._font_size = 12

    def create(self, sim, *args, **kwargs):
        self._time = sim.clock
        self._format = f"{round(self._time, self._precision)}"
        self._clock_img = pygame.image.load(get_img_asset("clock.png"))
        self._clock_img = pygame.transform.smoothscale(
            self._clock_img, self.CLOCK_SIZE
        )
        self._clock_rect = self._clock_img.get_rect()
        self._font = pygame.font.SysFont('Calibri', self._font_size)

    def pre_event_loop(self, sim, *args, **kwargs):
        self._target = sim.clock
        if self._time < self._target:
            push = max(self._pusher, (self._target - self._time) * self._pusher)
            self._time = min(self._target, self._time + push)
        self._format = f"{round(self._time, self._precision)}"

    def render_ui(self, window:Surface, *args, **kwargs):
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
        
        # handle the font and show it on the scren
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

    def handle_event(self, event, *args, **kwargs):
        # check if the event is a mousebuttondown
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._clock_rect.collidepoint(event.pos):
                # on left click increase precision
                if event.button == 1:
                    self._precision += 1
                # on right click decrease precision
                elif event.button == 3:
                    self._precision = max(1, self._precision - 1)

        return True

class UISidePanelModule(ModuleInterface):
    """"
    This module is a revealable side panel that can be adjusted to
    show different information packets.

    For the moment it will only trigger when a modelled node
    is clicked or "selected".
    """

    PANEL_CLICKER_SIZE = (16,40)
    PANEL_SIZE = (300,0)
    PUSH_OUT_SPEED = 20
    PUSH_OUT_MAX = PANEL_SIZE[0] - 20
    PANEL_Y_POS = 0

    TITLE_FONT_SIZE = 18
    SUBTITLE_FONT_SIZE = 16
    FONT_SIZE = 14    

    def __init__(self):
        super().__init__()
        self._opened = False
        self._push_out = 0
        self._description = None # if the description is None, nothing is shown
        self._selected = None
        self.reset_and_hide_description()

    def reset_and_hide_description(self):
        self._selected = None
        self._description = None

    def pre_event_loop(self, sim, *args, **kwargs):
        if self._opened:
            self._push_out = min(self.PUSH_OUT_MAX, self._push_out + self.PUSH_OUT_SPEED)
        else:
            self._push_out = max(0, self._push_out - self.PUSH_OUT_SPEED)
        if self._selected is not None:
            self._description = self._selected._model_node.get_description()

    def create(self, sim, *args, **kwargs):
        self.panel = pygame.rect.Rect(
            0, self.PANEL_Y_POS, self.PANEL_SIZE[0] + self.PANEL_CLICKER_SIZE[0], self.PANEL_SIZE[1]
        )
        self.open_button = pygame.image.load(get_img_asset("flip_open.png"))
        self.open_button = pygame.transform.rotate(self.open_button, -90)
        self.open_button = pygame.transform.smoothscale(
            self.open_button, self.PANEL_CLICKER_SIZE
        )
        self.orect = self.open_button.get_rect()
        self.close_button = pygame.image.load(get_img_asset("flip_close.png"))
        self.close_button = pygame.transform.rotate(self.close_button, -90)
        self.close_button = pygame.transform.smoothscale(
            self.close_button, self.PANEL_CLICKER_SIZE
        )
        self.crect = self.close_button.get_rect()

        return super().create(sim, *args, **kwargs)
        
    def handle_event(self, event, *args, **kwargs):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.panel.collidepoint(event.pos):
                if self.orect.collidepoint(event.pos) and not self._opened:
                    if event.button == 1:
                        self._opened = True
                        self._push_out = 0
                elif self.crect.collidepoint(event.pos) and self._opened:
                    if event.button == 1:
                        self._opened = False
                return False
            
        if check_event(event, NODE_CLICKED):
            self._selected = event.node
            self._description = self._selected._model_node.get_description()
        elif check_event(event, SELECTION_CLEAR):
            self.reset_and_hide_description()

        return True
    
    def render_ui(self, window, *args, **kwargs):
        right = window.get_width()
        mid = window.get_height() // 2
        top = 150

        self.orect.y = mid 
        self.orect.x = right - self.orect.width - self._push_out
        self.crect.y = mid 
        self.crect.x = right - self.crect.width - self._push_out
        self.panel.x = right - self._push_out - self.crect.width
        self.panel.height = window.get_height() - self.panel.y

        # if self._push_out > 0:
        pygame.draw.rect(
            window, TUE_LIGHTBLUE, self.panel,
            border_radius=15
        )
        pygame.draw.rect(
            window, TUE_BLUE, self.panel,
            LINE_WIDTH, border_radius=15
        )

        if (not self._opened):
            window.blit(self.open_button, self.orect)
        else:
            window.blit(self.close_button, self.crect)

        if self._push_out >= 0 and self._description is not None:
            self._render_description(window)

        return super().render_ui(window, *args, **kwargs)
    
    def _render_description(self, window:pygame.surface.Surface):
        info_surface = pygame.surface.Surface(self.panel.size, pygame.SRCALPHA)
        pos_x = 32
        pos_y = 16
        line_offset = 8
        frame_height = 65
        
        normal_font = pygame.font.SysFont('Calibri', self.FONT_SIZE)
        heading_font = pygame.font.SysFont('Calibri', self.TITLE_FONT_SIZE, bold=True)
        bold_font = pygame.font.SysFont('Calibri', self.FONT_SIZE, bold=True)
        
        for (text, style) in self._description:
            if style == Describable.Style.HEADING:
                font = heading_font
            elif style == Describable.Style.BOLD:
                font = bold_font
            else:
                font = normal_font                
            org_y = pos_y
            _, pos_y = prevent_overflow_while_rendering(
                info_surface,
                lambda t: font.render(t, True, TUE_BLUE),
                self.panel.width - 106,
                text,
                (pos_x, pos_y) if not style == Describable.Style.BOXED else (pos_x + line_offset/2, pos_y + line_offset/2),
                line_offset
            )
            if style == Describable.Style.BOXED:
                pygame.draw.rect(
                    info_surface, TUE_BLUE, pygame.Rect(pos_x, org_y + line_offset/4, self.panel.width - 96, pos_y - org_y),
                    LINE_WIDTH,
                    border_radius=5
                )
                pos_y += line_offset/2    
        window.blit(info_surface, self.panel)
        
        
if __name__ == "__main__":
    from simpn.simulator import SimProblem, SimToken
    from simpn.helpers import Place, Transition
    from simpn.visualisation import Visualisation

    from random import normalvariate

    problem = SimProblem()

    class Start(Place):
        model=problem
        name="start"
        amount=5

    class Resource(Place):
        model=problem
        name="resource"
        amount=1

    class Action(Transition):
        model=problem
        name="Task One"
        incoming = ["start", "resource"]
        outgoing = ["end", "resource"]

        def behaviour(c, r):
            return [
                SimToken(c, delay=normalvariate(2,0.25)),
                SimToken(r, delay=normalvariate(2,0.25))
            ]

    vis = Visualisation(
        problem,
        extra_modules=[
            UIClockModule(3),
            UISidePanelModule()
        ]
    )

    vis.show()