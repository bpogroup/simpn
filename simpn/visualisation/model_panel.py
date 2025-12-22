import pygame
import igraph
import threading
import math
from enum import Enum, auto
from typing import Optional, Tuple, List, Literal, Union
import simpn
from PyQt6.QtCore import Qt
from simpn.visualisation.events import (
    EventType,
    Event,
    create_event,
    listen_to,
    dispatch,
)
from simpn.visualisation.constants import (
    MAX_SIZE,
    TUE_RED,
    TUE_BLUE,
    TUE_LIGHTBLUE,
    TUE_GREY,
    STANDARD_NODE_WIDTH,
    STANDARD_NODE_HEIGHT,
    LINE_WIDTH,
    ARROW_WIDTH,
    ARROW_HEIGHT,
    TEXT_SIZE,
)


class Shape(Enum):
    TRANSTION = auto()
    PLACE = auto()
    EDGE = auto()


class Hook(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


class Edge:
    # An edge from a start node to and end node
    # start is a pair (node, Hook), where node is start node of the flow and Hook is the hook on that node
    # end is a pair (node, Hook), where node is start node of the flow and Hook is the hook on that node
    # intermediate is a list of pairs (x_new, y_new) of intermediate points on the flow, such that the flow
    #   is routed through these intermediate points. An intermediate point is computed from the previous point (x, y)
    #   by using (x_new if x_new >= 0 else x, y_new if y_new >= 0 else y)
    def __init__(self, start, end):
        self._start = start
        self._end = end

    def draw(self, screen):
        start_node_xy = self.get_start_node().get_pos()
        start_node_width, start_node_height = (
            self.get_start_node()._width,
            self.get_start_node()._height,
        )
        end_node_xy = self.get_end_node().get_pos()
        end_node_width, end_node_height = (
            self.get_end_node()._width,
            self.get_end_node()._height,
        )
        if (
            start_node_xy[1] - start_node_height / 2
            > end_node_xy[1] + end_node_height / 2
        ):
            self.set_start_hook(Hook.TOP)
        elif (
            start_node_xy[1] + start_node_height / 2
            < end_node_xy[1] - end_node_height / 2
        ):
            self.set_start_hook(Hook.BOTTOM)
        elif (
            start_node_xy[0] - start_node_width / 2
            > end_node_xy[0] + end_node_width / 2
        ):
            self.set_start_hook(Hook.LEFT)
        else:
            self.set_start_hook(Hook.RIGHT)
        if (
            end_node_xy[1] - end_node_height / 2
            > start_node_xy[1] + start_node_height / 2
        ):
            self.set_end_hook(Hook.TOP)
        elif (
            end_node_xy[1] + end_node_height / 2
            < start_node_xy[1] - start_node_height / 2
        ):
            self.set_end_hook(Hook.BOTTOM)
        elif (
            end_node_xy[0] - end_node_width / 2
            > start_node_xy[0] + start_node_width / 2
        ):
            self.set_end_hook(Hook.LEFT)
        else:
            self.set_end_hook(Hook.RIGHT)

        # Get hook positions
        start_hook_pos = self._start[0].hook(self._start[1])
        end_hook_pos = self._end[0].hook(self._end[1])

        # If hook positions are not valid
        if (
            start_hook_pos is None
            or not isinstance(start_hook_pos, tuple)
            or len(start_hook_pos) != 2
            or start_hook_pos[0] is None
            or start_hook_pos[1] is None
        ):
            start_hook_pos = self._start[0].get_pos()  # Fallback to center
        if (
            end_hook_pos is None
            or not isinstance(end_hook_pos, tuple)
            or len(end_hook_pos) != 2
            or end_hook_pos[0] is None
            or end_hook_pos[1] is None
        ):
            end_hook_pos = self._end[0].get_pos()  # Fallback to center

        start = pygame.Vector2(start_hook_pos)
        end = pygame.Vector2(end_hook_pos)
        arrow = start - end
        angle = arrow.angle_to(pygame.Vector2(0, -1))
        body_length = arrow.length() - ARROW_HEIGHT

        # if the end node does not want to show arrowheads, we simply draw a line from start to end
        if not self.get_end_node()._show_arrowheads:
            pygame.draw.line(screen, TUE_BLUE, start, end, int(LINE_WIDTH * 1.5))
            return

        # Create the triangle head around the origin
        head_verts = [
            pygame.Vector2(0, ARROW_HEIGHT / 2),  # Center
            pygame.Vector2(ARROW_WIDTH / 2, -ARROW_HEIGHT / 2),  # Bottomright
            pygame.Vector2(-ARROW_WIDTH / 2, -ARROW_HEIGHT / 2),  # Bottomleft
        ]
        # Rotate and translate the head into place
        translation = pygame.Vector2(0, arrow.length() - (ARROW_HEIGHT / 2)).rotate(
            -angle
        )
        for i in range(len(head_verts)):
            head_verts[i].rotate_ip(-angle)
            head_verts[i] += translation
            head_verts[i] += start

        pygame.draw.polygon(screen, TUE_BLUE, head_verts)

        # Stop weird shapes when the arrow is shorter than arrow head
        if arrow.length() >= ARROW_HEIGHT:
            # Calculate the body rect, rotate and translate into place
            body_verts = [
                pygame.Vector2(-LINE_WIDTH / 2, body_length / 2),  # Topleft
                pygame.Vector2(LINE_WIDTH / 2, body_length / 2),  # Topright
                pygame.Vector2(LINE_WIDTH / 2, -body_length / 2),  # Bottomright
                pygame.Vector2(-LINE_WIDTH / 2, -body_length / 2),  # Bottomleft
            ]
            translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
            for i in range(len(body_verts)):
                body_verts[i].rotate_ip(-angle)
                body_verts[i] += translation
                body_verts[i] += start

            pygame.draw.polygon(screen, TUE_BLUE, body_verts)

    def get_shape(self):
        return Shape.EDGE

    def get_start_node(self):
        return self._start[0]

    def get_end_node(self):
        return self._end[0]

    def set_start_hook(self, hook):
        self._start = (self._start[0], hook)

    def set_end_hook(self, hook):
        self._end = (self._end[0], hook)


class Node:
    def __init__(self, model_node):
        self._model_node = model_node
        self._pos = (0, 0)  # the center of the node
        self._width = STANDARD_NODE_WIDTH
        self._height = STANDARD_NODE_HEIGHT
        self._half_width = self._width / 2
        self._half_height = self._height / 2
        self._show_arrowheads = True

    def draw(self, screen):
        """
        This adds the drawable aspects of the node unto the given screen.
        """
        raise Exception("Node.raise must be implemented at subclass level.")

    def hook(self, hook_pos):
        if hook_pos == Hook.LEFT:
            result = (self._pos[0] - self._half_width, self._pos[1])
        elif hook_pos == Hook.RIGHT:
            result = (self._pos[0] + self._half_width, self._pos[1])
        elif hook_pos == Hook.TOP:
            result = (self._pos[0], self._pos[1] - self._half_height)
        elif hook_pos == Hook.BOTTOM:
            result = (self._pos[0], self._pos[1] + self._half_height)

        return result

    def set_pos(self, pos):
        self._pos = pos

    def get_pos(self):
        return self._pos

    def get_id(self):
        return self._model_node.get_id()

    def get_rect(self):
        return pygame.Rect(
            self._pos[0] - self._half_width,
            self._pos[1] - self._half_height,
            self._width,
            self._height,
        )


class TokenShower(Node):
    """
    Visualises the given set of sorted markings at some (x,y)
    location.

    Tokens are shown as grey circles if their time is lower than the
    current supplied clock time via `set_time`. Otherwise, they are shown
    as a red token.

    A token count in the center of the ring can be shown via
    `show_token_count`.
    """

    def __init__(self, markings: List["simpn.simulator.SimToken"]):
        super().__init__(None)
        self._count = len(markings)
        if self._count > 0:
            self._first_token = markings[0]
            self._last_token = markings[-1]
        self._visualable_tokens = markings
        self._rings = False
        self._token_radius = 5
        self._inner_ring_offset = (self._width / 2) - (self._token_radius * 2)
        self._curr_time = None
        self._show_count = False
        self._show_timing = False
        self._show_token_values = False

    def show_many_rings(self, show: bool = True) -> "TokenShower":
        """
        Allow the shower to make more than one ring of tokens.
        """
        self._rings = show
        return self

    def show_token_count(self, show: bool = True) -> "TokenShower":
        """
        Sets whether to show the token count.
        """
        self._show_count = show
        return self

    def show_timing_info(self, show: bool = True) -> "TokenShower":
        """
        Sets whether to show timing info about tokens.
        """
        self._show_timing = show
        return self

    def show_token_values(self, show: bool = True) -> "TokenShower":
        """
        Sets whether to show the token values.
        """
        self._show_token_values = show
        return self

    def set_pos(self, pos: Tuple[float, float]) -> "TokenShower":
        self._pos = pos
        return self

    def set_time(self, clock: float) -> "TokenShower":
        self._curr_time = clock
        return self

    def _compute_tokens_in_ring(
        self, offset: float, radius: float
    ) -> Tuple[int, float]:
        """
        Computes the number of tokens in a ring given an offset and radius.
        """
        circum = 2 * math.pi * offset
        n = math.ceil(circum / (radius * 2))

        return n, circum

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws tokens in a ring around the current position of the shower.
        """
        bold_font = pygame.font.SysFont("Calibri", TEXT_SIZE, bold=True)

        offset = self._inner_ring_offset
        n, _ = self._compute_tokens_in_ring(offset, self._token_radius)
        # draw the ring
        i = -1
        for token in self._visualable_tokens:
            i += 1
            angle = 2 * math.pi * i / n
            x_offset = offset * math.cos(angle)
            y_offset = offset * math.sin(angle)
            color = TUE_GREY if token.time <= self._curr_time else TUE_RED
            # draw tokens
            pygame.draw.circle(
                screen,
                color,
                (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                int(self._token_radius),
            )
            pygame.draw.circle(
                screen,
                pygame.colordict.THECOLORS.get("black"),
                (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                int(self._token_radius),
                LINE_WIDTH,
            )

            # should we break or make a larger ring
            if i > 0 and i % n == 0:
                if self._rings:
                    i = 0
                    offset += self._token_radius
                    n, _ = self._compute_tokens_in_ring(offset, self._token_radius)
                    n -= 2
                else:
                    break

        # draw label for count
        if self._count > 0 and self._show_count:
            label = bold_font.render(f"{self._count}", True, TUE_RED)
            screen.blit(
                label,
                (
                    self._pos[0] - label.get_width() * 0.5,
                    self._pos[1] - label.get_height() * 0.5,
                ),
            )

        text_x_pos = self._pos[0]
        text_y_pos = self._pos[1] + self._half_height
        # draw labels for the timing info
        if self._show_timing:
            last_time = None
            first_time = None
            if self._count > 0:
                first_time = round(self._first_token.time, 2)
                mstr = f"first @ {first_time}"
                label = bold_font.render(mstr, True, TUE_RED)
                text_y_pos += LINE_WIDTH + int(label.get_height())
                screen.blit(label, (text_x_pos - label.get_width() / 2, text_y_pos))
            if self._count > 1:
                last_time = round(self._last_token.time, 2)
                mstr = f"last @ {last_time}"
                label = bold_font.render(mstr, True, TUE_RED)
                text_y_pos += LINE_WIDTH + int(label.get_height())
                screen.blit(label, (text_x_pos - label.get_width() / 2, text_y_pos))

        # draw labels for token values
        if self._show_token_values:
            for token in self._visualable_tokens:
                label = bold_font.render(
                    str(token.value) + "@" + str(token.time), True, TUE_RED
                )
                text_y_pos += LINE_WIDTH + int(label.get_height())
                screen.blit(label, (text_x_pos - label.get_width() / 2, text_y_pos))


class PlaceViz(Node):
    def __init__(self, model_node):
        super().__init__(model_node)
        self._last_time = None

    def draw(self, screen):
        pygame.draw.circle(
            screen, TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._half_height
        )
        pygame.draw.circle(
            screen,
            TUE_BLUE,
            (self._pos[0], self._pos[1]),
            self._half_height,
            LINE_WIDTH,
        )
        font = pygame.font.SysFont("Calibri", TEXT_SIZE)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width() / 2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))

        # draw marking as tokens
        TokenShower(self._model_node.marking).set_pos(self._pos).set_time(
            self._curr_time
        ).show_token_count().draw(screen)


class TransitionViz(Node):
    def __init__(self, model_node):
        super().__init__(model_node)

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            TUE_LIGHTBLUE,
            pygame.Rect(
                self._pos[0] - self._half_width,
                self._pos[1] - self._half_height,
                self._width,
                self._height,
            ),
        )
        pygame.draw.rect(
            screen,
            TUE_BLUE,
            pygame.Rect(
                self._pos[0] - self._half_width,
                self._pos[1] - self._half_height,
                self._width,
                self._height,
            ),
            LINE_WIDTH,
        )
        font = pygame.font.SysFont("Calibri", TEXT_SIZE)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width() / 2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))


class ModelPanel:
    """
    A class for visualizing the provided simulation problem as a Petri net.

    .. Attributes::
    - sim_problem (SimProblem): the simulation problem to visualize
    - layout_file (str): the file path to the layout file (optional)
    - grid_spacing (int): the spacing between grid lines (default: 50)
    - node_spacing (int): the spacing between nodes (default: 100)
    - layout_algorithm (str): the layout algorithm to use (default: "sugiyama"),
     possible values: auto, sugiyama, davidson_harel, grid

    .. Methods::
    - save_layout(self, filename): saves the layout to a file
    - render(self, surface): renders the visualization onto a pygame surface
    """

    def __init__(
        self,
        sim_problem,
        layout_file=None,
        grid_spacing=50,
        node_spacing=100,
        layout_algorithm: Union[
            Literal["sugiyama", "davidson_harel", "grid", "auto"], None
        ] = "sugiyama",
    ):
        """
        Initialize the visualization.

        :param sim_problem: The simulation problem to visualize
        :param layout_file: Optional file path to load layout from
        :param grid_spacing: Spacing between grid lines
        :param node_spacing: Spacing between nodes in layout
        :param layout_algorithm: Algorithm to use for layout (sugiyama, davidson_harel, grid, auto, or None)
        """
        self._grid_spacing = grid_spacing
        self._node_spacing = node_spacing
        self._layout_algorithm = layout_algorithm

        self.__playing = False
        self._play_step_delay = 500
        self._problem = sim_problem
        self._nodes = dict()
        self._edges = []
        self._selected_nodes = None
        self._zoom_level = 1.0
        self._size = MAX_SIZE
        self._surface = pygame.Surface((640, 480))
        self._mods = []

        # Add visualizations for prototypes, places, and transitions,
        # but not for places and transitions that are part of prototypes.
        element_to_prototype = (
            dict()
        )  # mapping of prototype element ids to prototype ids
        viznodes_with_edges = []
        for prototype in self._problem.prototypes:
            if prototype.visualize:
                prototype_viznode = prototype.get_visualisation()
                self._nodes[prototype.get_id()] = prototype_viznode
                if prototype.visualize_edges:
                    viznodes_with_edges.append(prototype_viznode)
                for event in prototype.events:
                    element_to_prototype[event.get_id()] = prototype.get_id()
                for place in prototype.places:
                    element_to_prototype[place.get_id()] = prototype.get_id()
        for var in self._problem.places:
            if var.visualize and var.get_id() not in element_to_prototype:
                self._nodes[var.get_id()] = var.get_visualisation()
        for event in self._problem.events:
            if event.visualize and event.get_id() not in element_to_prototype:
                event_viznode = event.get_visualisation()
                self._nodes[event.get_id()] = event_viznode
                if event.visualize_edges:
                    viznodes_with_edges.append(event_viznode)
        # Add visualization for edges.
        # If an edge is from or to a prototype element, it must be from or to the prototype itself.
        for viznode in viznodes_with_edges:
            from_nodes = viznode._model_node.incoming
            to_nodes = viznode._model_node.outgoing
            if viznode._model_node.visualization_of_edges is not None:
                from_nodes = []
                to_nodes = []
                for a, b in viznode._model_node.visualization_of_edges:
                    if a == viznode._model_node:
                        to_nodes.append(b)
                    else:
                        from_nodes.append(a)
            for incoming in from_nodes:
                if incoming.visualize_edges:
                    node_id = incoming.get_id()
                    if node_id.endswith(".queue"):
                        node_id = node_id[: -len(".queue")]
                    if node_id in element_to_prototype:
                        node_id = element_to_prototype[node_id]
                    if node_id in self._nodes:
                        other_viznode = self._nodes[node_id]
                        self._edges.append(
                            Edge(
                                start=(other_viznode, Hook.RIGHT),
                                end=(viznode, Hook.LEFT),
                            )
                        )
            for outgoing in to_nodes:
                if outgoing.visualize_edges:
                    node_id = outgoing.get_id()
                    if node_id.endswith(".queue"):
                        node_id = node_id[: -len(".queue")]
                    if node_id in element_to_prototype:
                        node_id = element_to_prototype[node_id]
                    if node_id in self._nodes:
                        other_viznode = self._nodes[node_id]
                        self._edges.append(
                            Edge(
                                start=(viznode, Hook.RIGHT),
                                end=(other_viznode, Hook.LEFT),
                            )
                        )
        layout_loaded = False
        if layout_file is not None:
            try:
                self.__load_layout(layout_file)
                layout_loaded = True
            except FileNotFoundError as e:
                print(
                    "WARNING: could not load the layout because of the exception below.\nauto-layout will be used.\n",
                    e,
                )
        if not layout_loaded:
            if layout_algorithm is not None:
                self.__layout()

        # listen to the event que
        self._setup_listeners()

    def _setup_listeners(self):
        listen_to(EventType.SIM_ZOOM, self._ev_zoom)
        listen_to(EventType.SIM_UPDATE, self._ev_render)
        listen_to(EventType.SIM_RESIZE, self._ev_resize)
        listen_to(EventType.SIM_PRESS, self.handle_mouse_press)
        listen_to(EventType.SIM_RELEASE, self.handle_mouse_release)
        listen_to(EventType.SIM_MOVE, self.handle_mouse_motion)
        listen_to(EventType.SIM_HOVER, self.scale_to_surface)
        listen_to(EventType.SIM_PLAY, self.step, False)
        listen_to(EventType.SIM_RESET_LAYOUT, self.reset_layout, False)
        listen_to(EventType.SIM_RESET_SIM_STATE, self.reset_to_inital, False)

    def play(self):
        self.__playing = True
        while self.__playing:
            self.step()
            pygame.time.delay(self._play_step_delay)

    def is_playing(self):
        return self.__playing

    def action_faster(self):
        self._play_step_delay = max(100, self._play_step_delay - 100)

    def action_slower(self):
        self._play_step_delay = min(1000, self._play_step_delay + 100)

    def action_play(self):
        if not self.__playing:
            threading.Thread(target=self.play).start()

    def action_stop(self):
        self.__playing = False

    def action_step(self):
        if not self.__playing:
            self._problem.step()

    def __layout(self):
        graph = igraph.Graph()
        graph.to_directed()
        for node in self._nodes.values():
            graph.add_vertex(node.get_id())
        for edge in self._edges:
            graph.add_edge(edge.get_start_node().get_id(), edge.get_end_node().get_id())
        if self._layout_algorithm == "auto":
            layout = graph.layout(
                layout="auto",
            )
        elif self._layout_algorithm == "sugiyama":
            layout = graph.layout_sugiyama()
        elif self._layout_algorithm == "davidson_harel":
            layout = graph.layout_davidson_harel()
        elif self._layout_algorithm == "grid":
            layout = graph.layout_grid()
        else:
            raise Exception(f"Unknown layout algorithm: {self._layout_algorithm}")
        layout.rotate(-90)
        layout.scale(self._node_spacing)
        boundaries = layout.boundaries(border=STANDARD_NODE_WIDTH * 2)
        layout.translate(-boundaries[0][0], -boundaries[0][1])
        canvas_size = layout.boundaries(border=STANDARD_NODE_WIDTH * 2)[1]
        self._size = (
            min(MAX_SIZE[0], canvas_size[0]),
            min(MAX_SIZE[1], canvas_size[1]),
        )
        i = 0
        for v in graph.vs:
            xy = layout[i]
            xy = (
                round(xy[0] / self._grid_spacing) * self._grid_spacing,
                round(xy[1] / self._grid_spacing) * self._grid_spacing,
            )
            self._nodes[v["name"]].set_pos(xy)
            i += 1

    def reset_layout(self):
        """
        Recomputes the layout of the nodes using the selected layout algorithm.
        This method can be called to reset the layout to an automatic layout.
        """
        self.__layout()

    def reset_to_inital(self):
        """
        Resets the simulation problem to an initial state and refreshes the
        rendering process.

        Uses the named state "INITIAL_STATE" as a restore point.
        """
        self._problem.restore_checkpoint("INITIAL_STATE")
        dispatch(create_event(EventType.SIM_UPDATE), self)
        dispatch(create_event(EventType.POST_EVENT_LOOP, sim=self._problem), self)
        return True

    def save_layout(self, filename):
        """
        Saves the current layout of the nodes to a file.
        This method can be called after the show method.

        :param filename (str): The name of the file to save the layout to.
        """
        with open(filename, "w") as f:
            f.write("version 2.0\n")
            f.write(f"{self._zoom_level}\n")
            f.write(f"{int(self._size[0])},{int(self._size[1])}\n")
            for node in self._nodes.values():
                if "," in node.get_id() or "\n" in node.get_id():
                    raise Exception(
                        "Node "
                        + node.get_id()
                        + ": Saving the layout cannot work if the node id contains a comma or hard return."
                    )
                f.write(f"{node.get_id()},{node.get_pos()[0]},{node.get_pos()[1]}\n")

    def __load_layout(self, filename):
        with open(filename, "r") as f:
            firstline = f.readline().strip()
            if firstline == "version 2.0":
                self._zoom_level = float(f.readline().strip())
                self._size = tuple(map(int, f.readline().strip().split(",")))
            else:
                self._size = tuple(map(int, firstline.split(",")))
            for line in f:
                id, x, y = line.strip().split(",")
                if id in self._nodes:
                    self._nodes[id].set_pos((int(x), int(y)))

    def _ev_zoom(self, event: Event) -> bool:
        """
        Event que wrapper for calling zoom.
        """
        action = getattr(event, "action")
        self.zoom(action)
        return True

    def zoom(self, action):
        """
        Zooms the model. Action can be one of: increase, decrease, reset.

        :param action: The zoom action to perform.
        """
        if action == "reset":
            self._zoom_level = 1.0
        elif action == "decrease":
            self._zoom_level /= 1.1
        elif action == "increase":
            self._zoom_level *= 1.1
        self._zoom_level = max(0.3, min(self._zoom_level, 3.0))  # clamp zoom level

    def close(self):
        """
        Triggers the game loop showing the visualisation to close.
        """
        self.__playing = False

    def get_nodes(self):
        """Get the dictionary of visualization nodes."""
        return self._nodes

    def get_edges(self):
        """Get the list of edges."""
        return self._edges

    def get_problem(self):
        """Get the simulation problem."""
        return self._problem

    def _ev_resize(self, event) -> bool:

        width, height = event.width, event.height
        self._surface = pygame.Surface((width, height))

        return True

    def _ev_render(self, event) -> bool:
        """
        Event que wrapper for rendering the visualization.
        """
        self.render()
        return True

    def render(self) -> None:
        """
        Render the Petri net visualization onto the provided pygame surface (for IDE integration).

        :param surface: The pygame surface to render onto
        """
        # Get zoom level
        surface = self._surface
        zoom_level = self._zoom_level

        # Create a scaled surface for zooming
        scaled_width = int(surface.get_width() / zoom_level)
        scaled_height = int(surface.get_height() / zoom_level)
        scaled_surface = pygame.Surface((scaled_width, scaled_height))
        scaled_surface.fill(TUE_GREY)

        # Draw edges on scaled surface
        for edge in self._edges:
            edge.draw(scaled_surface)

        # Draw nodes on scaled surface
        evt = create_event(
            EventType.RENDER_PRE_NODES,
            window=scaled_surface,
            nodes=self._nodes.values(),
        )
        dispatch(evt, self)
        for node in self._nodes.values():
            node._curr_time = self._problem.clock
            node.draw(scaled_surface)

        # show the surface after nodes have been drawn
        evt = create_event(
            EventType.RENDER_POST_NODES,
            window=scaled_surface
        )
        dispatch(evt, self)

        # Scale the surface back to original size and blit
        surface.fill(TUE_GREY)
        scaled_back = pygame.transform.smoothscale(
            scaled_surface, (surface.get_width(), surface.get_height())
        )
        surface.blit(scaled_back, (0, 0))

        # Dispatch RENDER_UI event to all modules
        evt = create_event(EventType.RENDER_UI, window=surface)
        dispatch(evt, self)

        # share the final surface after ui rendering
        evt = create_event(EventType.RENDER_POST_UI, window=surface)
        dispatch(evt, self)

        dispatch(create_event(EventType.SIM_RENDERED, window=surface), self)

    def handle_mouse_press(self, event: Event) -> Optional[object]:
        """
        Handle mouse press events (for IDE integration).

        :param event.pos: (x, y) position of the mouse click
        :param event.button: Mouse button pressed
        :return: The node that was clicked, or None
        """
        pos: Tuple[int, int] = event.pos
        button: Qt.MouseButton = event.button
        if button == Qt.MouseButton.LeftButton:
            node = self._get_node_at(pos)
            if node is not None:
                self._selected_nodes = [node], pos
                # Dispatch event through centralized dispatcher
                evt = create_event(EventType.NODE_CLICKED, node=node, button=button)
                dispatch(evt, self)
            else:
                self._selected_nodes = list(self._nodes.values()), pos
                # Dispatch event through centralized dispatcher
                evt = create_event(EventType.SELECTION_CLEAR)
                dispatch(evt, self)
        return True

    def handle_mouse_release(self, event: Event) -> bool:
        """
        Handle mouse release events (for IDE integration).

        :param event.pos: (x, y) position of the mouse release
        :param event.button: Mouse button released
        """
        pos: Tuple[int, int] = event.pos
        button: Qt.MouseButton = event.button
        if button == Qt.MouseButton.LeftButton and self._selected_nodes is not None:
            self._drag_nodes(snap=True, pos=pos)
            self._selected_nodes = None
        return True

    def handle_mouse_motion(self, event: Event) -> bool:
        """
        Handle mouse motion events (for IDE integration).

        :param event.pos: (x, y) position of the mouse
        """
        pos = event.pos
        if self._selected_nodes is not None:
            self._drag_nodes(pos=pos)
        return True

    def _get_node_at(self, pos: Tuple[int, int]) -> Optional[object]:
        """
        Get the node at the given position.

        :param pos: (x, y) position to check
        :return: The node at the position, or None
        """
        scaled_pos = (pos[0] / self._zoom_level, pos[1] / self._zoom_level)
        for node in self._nodes.values():
            if node.get_pos()[0] - max(node._width / 2, 10) <= scaled_pos[
                0
            ] <= node.get_pos()[0] + max(node._width / 2, 10) and node.get_pos()[
                1
            ] - max(
                node._height / 2, 10
            ) <= scaled_pos[
                1
            ] <= node.get_pos()[
                1
            ] + max(
                node._height / 2, 10
            ):
                return node
        return None

    def _drag_nodes(
        self, snap: bool = False, pos: Optional[Tuple[int, int]] = None
    ) -> None:
        """
        Drag the selected nodes.

        :param snap: Whether to snap to grid
        :param pos: Position to drag to (if None, uses current mouse position)
        """
        if self._selected_nodes is None:
            return

        nodes = self._selected_nodes[0]
        org_pos = self._selected_nodes[1]
        new_pos = pos if pos is not None else (0, 0)
        x_delta = (new_pos[0] - org_pos[0]) / self._zoom_level
        y_delta = (new_pos[1] - org_pos[1]) / self._zoom_level

        for node in nodes:
            new_x = node.get_pos()[0] + x_delta
            new_y = node.get_pos()[1] + y_delta
            if snap:
                new_x = round(new_x / self._grid_spacing) * self._grid_spacing
                new_y = round(new_y / self._grid_spacing) * self._grid_spacing
            node.set_pos((new_x, new_y))

        self._selected_nodes = nodes, new_pos

    def scale_to_surface(self, event: Event) -> bool:
        """
        A hack to scale mouse positions from the upper
        pywidget mouse events to the internal surface coordinates.
        """
        if not hasattr(event, "scaled"):
            new_pos = (event.pos[0] / self._zoom_level, event.pos[1] / self._zoom_level)
            dispatch(
                create_event(EventType.SIM_HOVER, pos=new_pos, scaled=True),
                self            
            )
            return False
        return True

    def step(self) -> object:
        """
        Execute one step of the simulation (for IDE integration).

        :return: The fired binding, or None
        """
        # Dispatch PRE_EVENT_LOOP event
        evt = create_event(EventType.PRE_EVENT_LOOP, sim=self._problem)
        dispatch(evt, self)

        fired_binding = self._problem.step()

        if fired_binding is not None:
            # Dispatch BINDING_FIRED event
            evt = create_event(
                EventType.BINDING_FIRED, fired=fired_binding, sim=self._problem
            )
            dispatch(evt, self)

        # Dispatch POST_EVENT_LOOP event
        evt = create_event(EventType.POST_EVENT_LOOP, sim=self._problem)
        dispatch(evt, self)

        return fired_binding

    def get_zoom_level(self) -> float:
        """Get the current zoom level."""
        return self._zoom_level

    def set_zoom_level(self, zoom: float) -> None:
        """Set the zoom level."""
        self._zoom_level = max(0.3, min(zoom, 3.0))

    def mods(self) -> List[object]:
        """
        Returns the registered modules for the panel.
        """
        return self._mods

    def add_mod(self, module: object):
        """
        Adds a new module to be included in a visualisation.
        """
        self._mods.append(module)

    def listen_to(self):
        """Specify which event types this handler listens to."""
        return []  # ModelPanel doesn't listen to any events currently

    def handle_event(self, event: pygame.event.Event) -> bool:
        return True
