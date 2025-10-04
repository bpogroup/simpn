import igraph
import os
import traceback
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import simpn.assets as assets
from simpn.visualisation.events import create_event, NODE_CLICKED, SELECTION_CLEAR
from enum import Enum, auto
from typing import List, Tuple
import threading
import math
import simpn

MAX_SIZE = 1920, 1080
# colors
TUE_RED = (200, 25, 25)
TUE_LIGHTRED = (249, 204, 204)
TUE_BLUE = (16, 16, 115)
TUE_LIGHTBLUE = (188, 188, 246)
TUE_GREY = (242, 242, 242)
WHITE = (255, 255, 255)
# sizes
STANDARD_NODE_WIDTH, STANDARD_NODE_HEIGHT = 50, 50
LINE_WIDTH = 2
ARROW_WIDTH, ARROW_HEIGHT = 12, 10
TEXT_SIZE = 16
BUTTON_POSITION = (16, 16)
BUTTON_SIZE = (50, 50)


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
        start_node_width, start_node_height = self.get_start_node()._width, self.get_start_node()._height
        end_node_xy = self.get_end_node().get_pos()
        end_node_width, end_node_height = self.get_end_node()._width, self.get_end_node()._height
        if start_node_xy[1] - start_node_height/2 > end_node_xy[1] + end_node_height/2:
            self.set_start_hook(Hook.TOP)
        elif start_node_xy[1] + start_node_height/2 < end_node_xy[1] - end_node_height/2:
            self.set_start_hook(Hook.BOTTOM)
        elif start_node_xy[0] - start_node_width/2 > end_node_xy[0] + end_node_width/2:
            self.set_start_hook(Hook.LEFT)
        else:
            self.set_start_hook(Hook.RIGHT)
        if end_node_xy[1] - end_node_height/2 > start_node_xy[1] + start_node_height/2:
            self.set_end_hook(Hook.TOP)
        elif end_node_xy[1] + end_node_height/2 < start_node_xy[1] - start_node_height/2:
            self.set_end_hook(Hook.BOTTOM)
        elif end_node_xy[0] - end_node_width/2 > start_node_xy[0] + start_node_width/2:
            self.set_end_hook(Hook.LEFT)
        else:
            self.set_end_hook(Hook.RIGHT)
        start = pygame.Vector2(self._start[0].hook(self._start[1]))
        end = pygame.Vector2(self._end[0].hook(self._end[1]))
        arrow = start - end
        angle = arrow.angle_to(pygame.Vector2(0, -1))
        body_length = arrow.length() - ARROW_HEIGHT

        # if the end node does not want to show arrowheads, we simply draw a line from start to end
        if not self.get_end_node()._show_arrowheads:
            pygame.draw.line(screen, TUE_BLUE, start, end, int(LINE_WIDTH*1.5))
            return

        # Create the triangle head around the origin
        head_verts = [
            pygame.Vector2(0, ARROW_HEIGHT / 2),  # Center
            pygame.Vector2(ARROW_WIDTH / 2, -ARROW_HEIGHT / 2),  # Bottomright
            pygame.Vector2(-ARROW_WIDTH / 2, -ARROW_HEIGHT / 2),  # Bottomleft
        ]
        # Rotate and translate the head into place
        translation = pygame.Vector2(0, arrow.length() - (ARROW_HEIGHT / 2)).rotate(-angle)
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
        self._half_width =  self._width / 2
        self._half_height = self._height / 2
        self._show_arrowheads = True
            
    def draw(self, screen):
        """
        This adds the drawable aspects of the node unto the given screen.
        """
        raise Exception("Node.raise must be implemented at subclass level.")

    def hook(self, hook_pos):
        if hook_pos == Hook.LEFT:
            return self._pos[0] - self._half_width, self._pos[1]
        elif hook_pos == Hook.RIGHT:
            return self._pos[0] + self._half_width, self._pos[1]
        elif hook_pos == Hook.TOP:
            return self._pos[0], self._pos[1] - self._half_height
        elif hook_pos == Hook.BOTTOM:
            return self._pos[0], self._pos[1] + self._half_height

    def set_pos(self, pos):
        self._pos = pos
    
    def get_pos(self):
        return self._pos
    
    def get_id(self):
        return self._model_node.get_id()
            
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

    def __init__(self, markings:List['simpn.simulator.SimToken']):
        super().__init__(None)
        self._count = len(markings)
        if (self._count > 0):
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

    def show_many_rings(self, show:bool=True) -> 'TokenShower':
        """
        Allow the shower to make more than one ring of tokens.
        """
        self._rings = show
        return self

    def show_token_count(self, show:bool=True) -> 'TokenShower':
        """
        Sets whether to show the token count.
        """
        self._show_count = show 
        return self
    
    def show_timing_info(self, show:bool=True) -> 'TokenShower':
        """
        Sets whether to show timing info about tokens.
        """
        self._show_timing = show
        return self

    def show_token_values(self, show:bool=True) -> 'TokenShower':
        """
        Sets whether to show the token values.
        """
        self._show_token_values = show
        return self

    def set_pos(self, pos:Tuple[float, float]) -> 'TokenShower':
        self._pos = pos
        return self
    
    def set_time(self, clock:float) -> 'TokenShower':
        self._curr_time = clock 
        return self
    
    def _compute_tokens_in_ring(self, offset:float, radius:float) -> Tuple[int, float]:
        """
        Computes the number of tokens in a ring given an offset and radius.
        """
        circum = 2 * math.pi * offset
        n = math.ceil(circum / (radius * 2))

        return n, circum

    def draw(self, screen:pygame.Surface) -> None:
        """
        Draws tokens in a ring around the current position of the shower.
        """
        bold_font = pygame.font.SysFont('Calibri', TEXT_SIZE, bold=True)

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
                screen, color,
                (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                int(self._token_radius)
            )
            pygame.draw.circle(
                screen, pygame.colordict.THECOLORS.get('black'),
                (int(self._pos[0] + x_offset), int(self._pos[1] + y_offset)),
                int(self._token_radius),
                LINE_WIDTH
            )

            # should we break or make a larger ring
            if (i > 0 and i % n == 0):
                if (self._rings):
                    i = 0
                    offset += self._token_radius 
                    n, _ = self._compute_tokens_in_ring(offset, self._token_radius)
                    n -= 2
                else:
                    break

        # draw label for count 
        if (self._count > 0 and self._show_count):
            label = bold_font.render(f"{self._count}", True, TUE_RED)
            screen.blit(label, 
                (self._pos[0]-label.get_width() *  0.5, 
                self._pos[1]-label.get_height() * 0.5)
            )

        text_x_pos = self._pos[0]
        text_y_pos = self._pos[1] + self._half_height
        # draw labels for the timing info
        if (self._show_timing):
            last_time = None 
            first_time = None
            if self._count > 0:
                first_time = round(self._first_token.time,2) 
                mstr = f"first @ {first_time}"
                label = bold_font.render(mstr, True, TUE_RED)
                text_y_pos += LINE_WIDTH + int(label.get_height())
                screen.blit(label, (text_x_pos - label.get_width()/2, text_y_pos))     
            if self._count > 1:
                last_time = round(self._last_token.time,2) 
                mstr = f"last @ {last_time}"
                label = bold_font.render(mstr, True, TUE_RED)
                text_y_pos += LINE_WIDTH + int(label.get_height())
                screen.blit(label, (text_x_pos - label.get_width()/2, text_y_pos)) 

        # draw labels for token values
        if (self._show_token_values):
            for token in self._visualable_tokens:
                label = bold_font.render(str(token.value) + "@" + str(token.time), True, TUE_RED)
                text_y_pos += LINE_WIDTH + int(label.get_height())
                screen.blit(label, (text_x_pos - label.get_width()/2, text_y_pos))

class PlaceViz(Node):
    def __init__(self, model_node):
        super().__init__(model_node)
        self._last_time = None
    
    def draw(self, screen):
        pygame.draw.circle(screen, TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), self._half_height)
        pygame.draw.circle(screen, TUE_BLUE, (self._pos[0], self._pos[1]), self._half_height, LINE_WIDTH)    
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)
        bold_font = pygame.font.SysFont('Calibri', TEXT_SIZE, bold=True)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))

        # draw marking as tokens
        TokenShower(self._model_node.marking) \
            .set_pos(self._pos) \
            .set_time(self._curr_time) \
            .show_token_count() \
            .draw(screen)    

class TransitionViz(Node):
    def __init__(self, model_node):
        super().__init__(model_node)
    
    def draw(self, screen):
        pygame.draw.rect(screen, TUE_LIGHTBLUE, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, self._width, self._height))
        pygame.draw.rect(screen, TUE_BLUE, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, self._width, self._height), LINE_WIDTH)
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))
    
class Button:
    """
    A button as it will be drawn. The action is a function that will be executed when the button is clicked.
    The button image will be scaled to the specified size.

    :param image: The image to be displayed on the button.
    :param action: The function to be executed when the button is clicked.
    :param size: The size of the button (default: BUTTON_SIZE).
    """
    def __init__(self, image, action, size=BUTTON_SIZE):
        self.image = image
        self.image = pygame.transform.smoothscale(self.image, size)
        self.position = None
        self.button_rect = None
        self.action = action

    def draw(self, screen):
        screen.blit(self.image, self.position)

    def set_position(self, pos):
        self.position = pos
        self.button_rect = self.image.get_rect(topleft=self.position)

    def click(self, pos):
        x, y = pos
        if self.button_rect.collidepoint(x, y):
            self.action()
            return True
        return False

class Visualisation:
    """
    A class for visualizing the provided simulation problem as a Petri net.

    Attributes:
    - sim_problem (SimProblem): the simulation problem to visualize
    - layout_file (str): the file path to the layout file (optional)
    - grid_spacing (int): the spacing between grid lines (default: 50)
    - node_spacing (int): the spacing between nodes (default: 100)
    - layout_algorithm (str): the layout algorithm to use (default: "sugiyama"), possible values: auto, sugiyama, davidson_harel, grid

    Methods:
    - save_layout(self, filename): saves the layout to a file
    - show(self): shows the visualisation
    """
    def __init__(self, sim_problem, 
                 layout_file=None, 
                 grid_spacing=50, 
                 node_spacing=100, 
                 layout_algorithm="sugiyama",
                 extra_modules:List=None):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Petri Net Visualisation')
        # assets.create_assets(assets.images, "assets")
        icon = pygame.image.load(
            assets.get_img_asset("logo.png")
        )
        pygame.display.set_icon(icon)

        self._grid_spacing = grid_spacing
        self._node_spacing = node_spacing
        self._layout_algorithm = layout_algorithm

        self.__playing = False
        self.__running = False
        self._play_step_delay = 500
        self._problem = sim_problem
        self._nodes = dict()
        self._edges = []
        self._selected_nodes = None        
        self._zoom_level = 1.0
        self._size = MAX_SIZE
        self.buttons = []

        # default modules used in the visualisation process
        from .modules.base import ModuleInterface
        from .modules.ui import UIClockModule, UISidePanelModule
        self._modules:List[ModuleInterface] = [
            UIClockModule(3),
            UISidePanelModule()
        ]
        if extra_modules != None and isinstance(extra_modules, list):
            self._modules = self._modules + extra_modules

        self.__create_buttons_closed_menu()

        # Add visualizations for prototypes, places, and transitions,
        # but not for places and transitions that are part of prototypes.
        element_to_prototype = dict()  # mapping of prototype element ids to prototype ids
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
                for (a, b) in viznode._model_node.visualization_of_edges:
                    if a == viznode._model_node:
                        to_nodes.append(b)
                    else:
                        from_nodes.append(a)
            for incoming in from_nodes:
                if incoming.visualize_edges:
                    node_id = incoming.get_id()
                    if node_id.endswith(".queue"):
                        node_id = node_id[:-len(".queue")]
                    if node_id in element_to_prototype:
                        node_id = element_to_prototype[node_id]
                    if node_id in self._nodes:
                        other_viznode = self._nodes[node_id]
                        self._edges.append(Edge(start=(other_viznode, Hook.RIGHT), end=(viznode, Hook.LEFT)))
            for outgoing in to_nodes:
                if outgoing.visualize_edges:
                    node_id = outgoing.get_id()
                    if node_id.endswith(".queue"):
                        node_id = node_id[:-len(".queue")]
                    if node_id in element_to_prototype:
                        node_id = element_to_prototype[node_id]
                    if node_id in self._nodes:
                        other_viznode = self._nodes[node_id]
                        self._edges.append(Edge(start=(viznode, Hook.RIGHT), end=(other_viznode, Hook.LEFT)))
        layout_loaded = False
        if layout_file is not None:
            try:
                self.__load_layout(layout_file)
                layout_loaded = True
            except FileNotFoundError as e:
                print("WARNING: could not load the layout because of the exception below.\nauto-layout will be used.\n", e)
        if not layout_loaded:
            self.__layout()        

        for mod in self._modules:
            mod.create(self._problem)

        self.__win = pygame.display.set_mode(self._size, pygame.RESIZABLE) # the window
    
    def __create_buttons_open_menu(self):
        self.buttons = []
        self.buttons.append(Button(pygame.image.load(assets.get_img_asset("flip_close.png")), self.action_hide_buttons, size=(BUTTON_SIZE[0], int(BUTTON_SIZE[1]/2))))
        self.buttons.append(Button(pygame.image.load(assets.get_img_asset("step.png")), self.action_step))
        self.buttons.append(Button(pygame.image.load(assets.get_img_asset("play.png")), self.action_play))
        self.buttons.append(Button(pygame.image.load(assets.get_img_asset("stop.png")), self.action_stop))
        self.buttons.append(Button(pygame.image.load(assets.get_img_asset("faster.png")), self.action_faster))
        self.buttons.append(Button(pygame.image.load(assets.get_img_asset("slower.png")), self.action_slower))

        # Set button positions
        position = BUTTON_POSITION
        for button in self.buttons:
            button.set_position(position)
            position = (position[0], position[1] + button.button_rect.height + 4)

    def __create_buttons_closed_menu(self):
        show_button = Button(pygame.image.load(assets.get_img_asset("flip_open.png")), self.action_show_buttons, size=(BUTTON_SIZE[0], int(BUTTON_SIZE[1]/2)))
        show_button.set_position(BUTTON_POSITION)
        self.buttons = [show_button]

    def action_hide_buttons(self):
        self.__create_buttons_closed_menu()
    
    def action_show_buttons(self):
        self.__create_buttons_open_menu()
    
    def play(self):
        self.__playing = True
        while self.__playing:
            fired_binding = self._problem.step()
            
            if fired_binding != None:
                for mod in self._modules:
                    mod.firing(fired_binding, self._problem)

            pygame.time.delay(self._play_step_delay)

    def action_faster(self):
        self._play_step_delay = max(100, self._play_step_delay - 100)

    def action_slower(self):
        self._play_step_delay = min(1000, self._play_step_delay + 100)

    def action_play(self):
        if not self.__playing:
            threading.Thread(target=self.play).start()

    def action_stop(self):
        self.__playing = False

    def __draw(self):
        self.__screen = pygame.Surface((self._size[0]/self._zoom_level, self._size[1]/self._zoom_level))
        self.__win.fill(TUE_GREY)
        self.__screen.fill(TUE_GREY)
        for shape in self._edges:
            shape.draw(self.__screen)
        for shape in self._nodes.values():
            shape._curr_time = self._problem.clock
            shape.draw(self.__screen)
        # scale the entire screen using the self._zoom_level and draw it in the window
        
        for mod in self._modules:
            mod.render_sim(self.__screen)

        self.__screen.get_width()
        self.__win.blit(pygame.transform.smoothscale(self.__screen, (self._size[0], self._size[1])), (0, 0))
        # draw buttons
        for button in self.buttons:
            button.draw(self.__win)
        
        for mod in self._modules:
            mod.render_ui(self.__win)

        # flip
        pygame.display.flip()

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
            layout = graph.layout(layout="auto", )
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
        boundaries = layout.boundaries(border=STANDARD_NODE_WIDTH*2)
        layout.translate(-boundaries[0][0], -boundaries[0][1])
        canvas_size = layout.boundaries(border=STANDARD_NODE_WIDTH*2)[1]
        self._size = (min(MAX_SIZE[0], canvas_size[0]), min(MAX_SIZE[1], canvas_size[1]))
        i = 0
        for v in graph.vs:
            xy = layout[i]
            xy  = (round(xy[0]/self._grid_spacing)*self._grid_spacing, round(xy[1]/self._grid_spacing)*self._grid_spacing)
            self._nodes[v["name"]].set_pos(xy)
            i += 1

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
                        raise Exception("Node " + node.get_id() + ": Saving the layout cannot work if the node id contains a comma or hard return.")
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

    def __get_node_at(self, pos):
        scaled_pos = (pos[0] / self._zoom_level, pos[1] / self._zoom_level)
        for node in self._nodes.values():
            if node.get_pos()[0] - max(node._width/2, 10) <= scaled_pos[0] <= node.get_pos()[0] + max(node._width/2, 10) and \
            node.get_pos()[1] - max(node._height/2, 10) <= scaled_pos[1] <= node.get_pos()[1] + max(node._height/2, 10):
                return node
        return None

    def __drag(self, snap=False):
        nodes = self._selected_nodes[0]
        org_pos = self._selected_nodes[1]
        new_pos = pygame.mouse.get_pos()
        x_delta = (new_pos[0] - org_pos[0]) / self._zoom_level
        y_delta = (new_pos[1] - org_pos[1]) / self._zoom_level
        for node in nodes:
            new_x = node.get_pos()[0] + x_delta
            new_y = node.get_pos()[1] + y_delta
            if snap:
                new_x = round(new_x/self._grid_spacing)*self._grid_spacing
                new_y = round(new_y/self._grid_spacing)*self._grid_spacing
            node.set_pos((new_x, new_y))
        self._selected_nodes = nodes, new_pos

    def __handle_event(self, event):
        for mod in self._modules:
            propagate = mod.handle_event(event)
            if not propagate:
                return
        if event.type == pygame.QUIT:
            self.__running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.click(event.pos):
                    return
            node = self.__get_node_at(event.pos)
            if node is not None:
                self._selected_nodes = [node], event.pos
                pygame.event.post(
                    create_event(
                        NODE_CLICKED,
                        { 'node' : node }
                    )
                )
            else:
                self._selected_nodes = self._nodes.values(), event.pos
                pygame.event.post(
                    create_event(
                        SELECTION_CLEAR,
                        {}
                    )
                )
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._selected_nodes is not None:
            self.__drag(snap=True)
            self._selected_nodes = None
        elif event.type == pygame.MOUSEMOTION and self._selected_nodes is not None:
            self.__drag()
        elif event.type == pygame.VIDEORESIZE:
            self._size = event.size
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._problem.step()
            elif event.key == pygame.K_0 and event.mod & pygame.KMOD_CTRL:
                self.zoom("reset")
            elif event.key == pygame.K_MINUS and event.mod & pygame.KMOD_CTRL:
                self.zoom("decrease")
            elif event.key == pygame.K_EQUALS and event.mod & pygame.KMOD_CTRL:
                self.zoom("increase")
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.zoom("increase")
            else:
                self.zoom("decrease")


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
        self.__running = False
        self.__playing = False

    def show(self):
        """
        Displays the Petri net visualisation in a window.
        The method will block further execution until the window is closed.

        The visualisation can be interacted with using the mouse and keyboard.
        The spacebar can be used to step through the Petri net problem.
        The mouse can be used to drag nodes around.
        """
        clock = pygame.time.Clock()
        
        self.__running = True
        while self.__running:

            for mod in self._modules:
                mod.pre_event_loop(self._problem)

            for event in pygame.event.get():
                self.__handle_event(event)
            try:
                self.__draw()
            except Exception:
                print("Error while drawing the visualisation.")
                print(traceback.format_exc())
                self.__running = False

            for mod in self._modules:
                mod.post_event_loop(self._problem)

            clock.tick(30)
        
        self.__playing = False
        pygame.time.delay(self._play_step_delay)
        pygame.display.quit()
        pygame.quit()

