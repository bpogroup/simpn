"""
This module contains modules for ui compontents used in the visualisation
of simulation problems.
"""
import pygame
from pygame.surface import Surface

from simpn.visualisation.modules.base import ModuleInterface
from simpn.visualisation.base import TUE_GREY, TUE_BLUE, TUE_LIGHTBLUE, LINE_WIDTH, TEXT_SIZE
from simpn.assets import get_img_asset

class UIClockModule(ModuleInterface):
    """
    This modules handles creating a clock in the top right corner to
    show the current simulation time to a predefined precision.

    :param `precision=2`:
        The preicision of the clock to show in the UI.
    """

    CLOCK_SIZE = (64, 64)
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
            window.get_width() - self.OFFSET- self._clock_rect.width // 2, 
            self.OFFSET + self._clock_rect.height // 2
        )

        # draw holder for text
        clock_text_rect = pygame.Rect(
            window.get_width() - self.OFFSET - self._clock_rect.width,
            self.OFFSET + self._clock_rect.height - 5,
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
            UIClockModule(3)
        ]
    )

    vis.show()