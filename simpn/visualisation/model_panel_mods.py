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
from simpn.visualisation.constants import (
    TUE_BLUE,
    TUE_LIGHTBLUE,
    LINE_WIDTH,
    TUE_RED,
    GREEN,
)
from simpn.assets import get_img_asset
from simpn.visualisation.events import (
    EventType,
    IEventHandler,
    check_event,
    dispatch,
    create_event,
    listen_to,
    Event,
)
from dataclasses import dataclass
from collections import deque
from typing import List, Tuple, Literal
from .text import prevent_overflow_while_rendering
import imageio


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

        listen_to(EventType.CLOCK_PREC_INC, self.increase_precision, False)
        listen_to(EventType.CLOCK_PREC_DEC, self.decrease_precision, False)

    def listen_to(self):
        """
        Specify which event types this handler listens to.

        :return: List of EventType enums (VISUALIZATION_CREATED, POST_EVENT_LOOP, RENDER_UI)
        """
        return [
            EventType.VISUALIZATION_CREATED,
            EventType.POST_EVENT_LOOP,
            EventType.RENDER_UI,
            EventType.SIM_CLICK,
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
                x, y = event.pos["x"], event.pos["y"]
                if self._clock_rect.collidepoint(x, y):
                    if event.button == Qt.MouseButton.LeftButton:
                        dispatch(create_event(EventType.CLOCK_PREC_INC))
                    elif event.button == Qt.MouseButton.RightButton:
                        dispatch(create_event(EventType.CLOCK_PREC_DEC))

        return True

    def increase_precision(self):
        """
        Increase the number of decimal places shown in the time display by 1.
        """
        self._precision += 1
        self._pusher = 1.0 / (self._precision + 1)
        self._format = f"{round(self._time, self._precision)}"
        return True

    def decrease_precision(self):
        """
        Decrease the number of decimal places shown in the time display by 1.

        The precision will not go below 1 decimal place.
        """
        self._precision = max(1, self._precision - 1)
        self._pusher = 1.0 / (self._precision + 1)
        self._format = f"{round(self._time, self._precision)}"
        return True

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


@dataclass
class FiredTracker:
    event: object = None
    name: str = "foo"
    inputs: int = 1
    outputs: int = 1
    time: float = 0.0
    bindings: List = None
    clickable: pygame.Rect = None
    cache: pygame.Surface = None

    def describe(self) -> List:
        """
        Returns a formated description for the attribute panel.
        """
        from simpn.simulator import Describable
        from html import escape

        name = escape(self.name)
        ret = [
            (f"Fired Event: {name}", Describable.Style.HEADING),
            (
                f"This event was fired at a time of: {self.time}",
                Describable.Style.NORMAL,
            ),
            (
                f"This event consumed {self.inputs} tokens as it fired.",
                Describable.Style.NORMAL,
            ),
            (
                f"This event produced {self.outputs} tokens as output.",
                Describable.Style.NORMAL,
            ),
            (
                "Binding Used:",
                Describable.Style.HEADING,
            ),
        ] + [(f"{escape(str(tok))}", Describable.Style.BOXED) for tok in self.bindings]

        return ret


class FiredTrackerModule(IEventHandler):
    """
    This visualisation module tracks the last ten fired modules. For each one
    it keeps track the binding and creates a small graphical element at the
    bottom of the screen.
    """

    def __init__(self):
        super().__init__()
        self.que: List[FiredTracker] = deque([], 10)
        self._tracker_width = 50
        self._tracker_height = 50
        self._tracker_cir_radius = 3
        self._tracker_cir_dia = self._tracker_cir_radius * 2
        self._fonter = pygame.font.SysFont(
            "Calibri",
            10,
        )
        self._big_fonter = pygame.font.SysFont("Calibri", 24, True)

    def listen_to(self):
        return [
            EventType.BINDING_FIRED,
            EventType.RENDER_UI,
            EventType.SIM_CLICK,
            EventType.SIM_RESET_SIM_STATE,
        ]

    def handle_event(self, event):
        if check_event(event, EventType.BINDING_FIRED):
            self.update_tracking(event)
        elif check_event(event, EventType.RENDER_UI):
            self.render(event.window)
        elif check_event(event, EventType.SIM_CLICK):
            if event.button == Qt.MouseButton.LeftButton:
                return self.check_and_post_description(event.pos)
        elif check_event(event, EventType.SIM_RESET_SIM_STATE):
            self.que.clear()
        return True

    def render(self, window: pygame.Surface):
        width = window.get_width()
        height = window.get_height()

        y_top = height - self._tracker_height - 5
        x_top = width - self._tracker_width - 5

        if len(self.que) > 0:
            # add display hints for what the boxes are
            tmp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            out_text = self._fonter.render("Previously Fired Bindings:", True, TUE_RED)
            tmp_surface.blit(
                out_text, (width - out_text.get_width(), y_top - out_text.get_height())
            )
            tmp_surface.set_alpha(125)
            window.blit(tmp_surface, (0, 0))

        for num, tracker in enumerate(reversed(self.que)):
            # print(x_top, y_top, tracker)
            if tracker.cache is None:
                tracker.cache = pygame.Surface(
                    (self._tracker_height, self._tracker_height), pygame.SRCALPHA
                )

                rect = pygame.Rect(0, 0, self._tracker_width, self._tracker_height)

                pygame.draw.rect(tracker.cache, TUE_LIGHTBLUE, rect, border_radius=5)
                pygame.draw.rect(tracker.cache, TUE_BLUE, rect, 2, 5)

                # draw red circles for input
                y_cir_top = self._tracker_cir_dia
                x_cir_top = self._tracker_cir_dia
                for _ in range(tracker.inputs):
                    pygame.draw.circle(
                        tracker.cache,
                        TUE_RED,
                        (x_cir_top, y_cir_top),
                        self._tracker_cir_radius,
                    )
                    y_cir_top += self._tracker_cir_dia * 1.2
                    if y_cir_top > self._tracker_height:
                        x_cir_top -= self._tracker_cir_dia * 1.2
                        y_cir_top = self._tracker_cir_dia

                # draw red circles for input
                y_cir_top = self._tracker_cir_dia
                x_cir_top = self._tracker_width - self._tracker_cir_dia
                for _ in range(tracker.outputs):
                    pygame.draw.circle(
                        tracker.cache,
                        GREEN,
                        (x_cir_top, y_cir_top),
                        self._tracker_cir_radius,
                    )
                    y_cir_top += self._tracker_cir_dia * 1.2
                    if y_cir_top > self._tracker_height:
                        x_cir_top -= self._tracker_cir_dia * 1.2
                        y_cir_top = self._tracker_cir_dia

                # draw text name of event
                prevent_overflow_while_rendering(
                    tracker.cache,
                    lambda t: self._fonter.render(t, True, TUE_BLUE),
                    self._tracker_width - 20,
                    tracker.name,
                    (10, 10),
                    2.5,
                )

                window.blit(tracker.cache, (x_top, y_top))
            else:
                window.blit(tracker.cache, (x_top, y_top))

            # draw the sequence number
            tmp_surface = pygame.Surface(
                (self._tracker_height, self._tracker_height), pygame.SRCALPHA
            )
            prevent_overflow_while_rendering(
                tmp_surface,
                lambda t: self._big_fonter.render(t, True, TUE_BLUE),
                self._tracker_width - 20,
                f"{num}" if num < 1 else f"-{num}",
                (12.5 if num > 1 else 15, self._tracker_height / 2.5),
                2.5,
            )
            tmp_surface.set_alpha(85)
            window.blit(tmp_surface, (x_top, y_top))

            # update their clickable
            rect = pygame.Rect(x_top, y_top, self._tracker_width, self._tracker_height)
            tracker.clickable = rect

            # move pos to the next firing spot
            x_top = x_top - self._tracker_width - 2.5

    def update_tracking(self, event: Event):
        """
        Adds and pushes the que along based on the fired binding.
        """
        bindings, time, eventer = event.fired
        self.que.append(
            FiredTracker(
                event=eventer,
                name=eventer._id,
                bindings=bindings,
                inputs=len(eventer.incoming),
                outputs=len(eventer.outgoing),
                time=time,
            )
        )

    def check_and_post_description(self, pos: Tuple[int, int]):
        """
        Finds if there was a collision with any of the trackers, and
        if so, will send up a description to be shown in the attribute
        panel.
        """
        x, y = pos["x"], pos["y"]
        for tracker in self.que:
            if tracker.clickable is not None:
                if tracker.clickable.collidepoint(x, y):
                    dispatch(
                        create_event(
                            EventType.DES_POST, description=tracker.describe()
                        ),
                        self,
                    )
                    name = tracker.name
                    # a hack to handle prototypes using lifecycles
                    if "<" in name:
                        name = name.split("<")[0]
                    dispatch(create_event(EventType.HLIGHT_FOCUS, node=name), self)
                    return False
        return True


class NodeHighlightingModule(IEventHandler):
    """
    This visualization module highlights nodes when hovered over.

    It draws a border around nodes to indicate they are being hovered.
    """

    def __init__(self):
        super().__init__()
        self._node_rects = []
        self._hovered = None
        self._highlighted = None

    def listen_to(self):
        return [
            EventType.RENDER_PRE_NODES,
            EventType.SIM_HOVER,
            EventType.NODE_CLICKED,
            EventType.SELECTION_CLEAR,
            EventType.HLIGHT_FOCUS,
            EventType.HLIGHT_DEFOCUS,
            EventType.HLIGHT_HOVER,
            EventType.HLIGHT_UNHOVER,
        ]

    def _find_node(self, name):
        for node, rect in self._node_rects:
            if node.get_id() == name:
                return node
        return None

    def handle_focus(self, event):
        if check_event(event, EventType.HLIGHT_FOCUS):
            self._highlighted = self._find_node(event.node)
        elif check_event(event, EventType.HLIGHT_DEFOCUS):
            self._highlighted = None
        return True

    def handle_hover(self, event):
        if check_event(event, EventType.HLIGHT_HOVER):
            self._hovered = self._find_node(event.node)
        elif check_event(event, EventType.HLIGHT_UNHOVER):
            self._hovered = None
        return True

    def handle_event(self, event):
        if check_event(event, EventType.RENDER_PRE_NODES):
            self.update_node_positions(event)
            self.render(event)
        elif check_event(event, EventType.SIM_HOVER):
            self.check_for_hovered(event)
        elif check_event(event, EventType.NODE_CLICKED):
            self._highlighted = event.node
        elif check_event(event, EventType.SELECTION_CLEAR):
            self._highlighted = None
            self._hovered = None
        elif check_event(event, EventType.HLIGHT_FOCUS) or check_event(
            event, EventType.HLIGHT_DEFOCUS
        ):
            self.handle_focus(event)
        elif check_event(event, EventType.HLIGHT_HOVER) or check_event(
            event, EventType.HLIGHT_UNHOVER
        ):
            self.handle_hover(event)
        return True

    def update_node_positions(self, event: Event) -> bool:
        """
        Update the positions of nodes before rendering.

        :param event: The event containing node information
        """
        self._node_rects = []
        for node in event.nodes:
            rect = node.get_rect()
            self._node_rects.append((node, rect))
        return True

    def check_for_hovered(self, event: Event) -> bool:
        """
        Check if the mouse is hovering over any node.

        :param event: The event containing mouse position
        """
        x, y = event.pos
        hovered_node = None
        for node, rect in self._node_rects:
            if rect.collidepoint(x, y):
                hovered_node = node
                break
        self._hovered = hovered_node
        return True

    def render(self, event: Event) -> bool:
        """
        Render a highlight around the hovered node.

        :param window: The pygame surface to draw on
        :param hovered_node: The node currently being hovered over
        """
        surface: pygame.Surface = event.window
        tmpsur = pygame.Surface(
            (surface.get_width(), surface.get_height()), pygame.SRCALPHA
        )
        tmpsur.set_alpha(80)
        if self._hovered is not None and self._hovered is not self._highlighted:
            rect = self._hovered.get_rect()
            pygame.draw.circle(
                tmpsur,
                TUE_RED,
                rect.center,
                rect.width // 2 + 10,
            )
        if self._highlighted is not None:
            rect = self._highlighted.get_rect()
            pygame.draw.circle(
                tmpsur,
                GREEN,
                rect.center,
                rect.width // 2 + 10,
            )
        surface.blit(tmpsur, (0, 0))
        return True


class RecorderModule(IEventHandler):
    """
    This module records the visulisation of the `SimProblem` for latter
    use.

    The module records the format in a gif format so that it can be used to
    show the unfolding of a system. The module begins recording as soon as
    the visualisation executes the problem for the first time, i.e. either
    a step is trigger or playing is trigger.

    parameters:
        filepath:
            Where to save the recording after the visualisation has been
            closed
        format:
            What format should be the recording be, current options include:
            "gif".
        include_ui:
            Whether to include the ui in the recording. Specifically the
            UI for the visualisation, not the application ui.
        size:
            Tuple[int, int]
            The gif size for all frames, all surfaces will be scaled to match
            these dimensions.
        settings:
            A `RecordingSettings` dataclass for adjusting the output
            parameters for the recording.

    methods:
        save():
            Force the recording to be saved out.
    """

    @dataclass
    class RecordingSettings:
        """
        A light wrapper around the settings for mimsave api call for imageio.

        See docs (<https://imageio.readthedocs.io/en/stable/_autosummary/imageio.plugins.pillow_legacy.html>)
        for more information on these settings.
        """

        fps: int = 30
        palettesize: int = 256
        subrectangles: bool = True

    def __init__(
        self,
        fname: str,
        format: Literal["gif"] = "gif",
        include_ui: bool = False,
        settings: RecordingSettings = None,
        size: Tuple[int, int] = None,
    ):
        super().__init__()
        self._fname = fname
        self._format = format
        self._frames = []
        self._started = False
        self._includeui = include_ui
        self._size = size

        if settings is None:
            self._settings = self.RecordingSettings()
        else:
            self._setting = settings

    def listen_to(self):
        return [
            EventType.SIM_PLAY,
            EventType.SIM_PLAYING,
            EventType.SIM_STOP,
            EventType.RENDER_POST_NODES,
            EventType.RENDER_POST_UI,
            EventType.SIM_CLOSE,
        ]

    def handle_event(self, event):

        if not self._started and any(
            [
                check_event(event, EventType.SIM_PLAY),
                check_event(event, EventType.SIM_PLAYING),
            ]
        ):
            self._started = True

        if check_event(event, EventType.SIM_STOP):
            self._started = False

        if self._started:
            if not self._includeui and check_event(event, EventType.RENDER_POST_NODES):
                self._handle_frames(event.window)

            if self._includeui and check_event(event, EventType.RENDER_POST_UI):
                self._handle_frames(event.window)

        if check_event(event, EventType.SIM_CLOSE):
            self._started = False
            self.save()

    def _handle_frames(self, screen: pygame.Surface):
        """
        Extracts the screen state into a frame for recording.
        """
        if self._size is None:
            self._size = screen.get_width(), screen.get_height()
        temp_surface = pygame.Surface(self._size)
        pygame.transform.smoothscale(
            screen, self._size, temp_surface
        )
        frame = pygame.surfarray.array3d(temp_surface)
        frame = frame.transpose([1, 0, 2])  # Convert to (height, width, channels)

        self._frames.append(frame)

    def save(self):
        if self._format == "gif":
            if len(self._frames) > 0:
                print("RecorderModule:: saving out recording...")
                imageio.mimsave(
                    self._fname,
                    self._frames,
                    fps=self._settings.fps,
                    palettesize=self._settings.palettesize,
                    subrectangles=self._settings.subrectangles,
                )
            else:
                import warnings

                warnings.warn(
                    "RecorderModule:: No frames have been saved,"
                    " no ouput will be produced."
                )
        else:
            raise ValueError(f"Unknown format for saving :: {self._format}")
