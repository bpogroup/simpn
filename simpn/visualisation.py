import igraph
import pygame
from enum import Enum, auto


MAX_SIZE = 1920, 1080
# colors
TUE_RED = (200, 25, 25)
TUE_LIGHTRED = (249, 204, 204)
TUE_BLUE = (16, 16, 115)
TUE_LIGHTBLUE = (188, 188, 246)
TUE_GREY = (242, 242, 242)
WHITE = (255, 255, 255)
# sizes
NODE_WIDTH, NODE_HEIGHT = 50, 50
NODE_SPACING = 100
GRID_SPACING = 50
LINE_WIDTH = 2
ARROW_WIDTH, ARROW_HEIGHT = 12, 10
TEXT_SIZE = 16


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
        end_node_xy = self.get_end_node().get_pos()
        if start_node_xy[1] - NODE_HEIGHT/2 > end_node_xy[1] + NODE_HEIGHT/2:
            self.set_start_hook(Hook.TOP)
        elif start_node_xy[1] + NODE_HEIGHT/2 < end_node_xy[1] - NODE_HEIGHT/2:
            self.set_start_hook(Hook.BOTTOM)
        elif start_node_xy[0] - NODE_WIDTH/2 > end_node_xy[0] + NODE_WIDTH/2:
            self.set_start_hook(Hook.LEFT)
        else:
            self.set_start_hook(Hook.RIGHT)
        if end_node_xy[1] - NODE_HEIGHT/2 > start_node_xy[1] + NODE_HEIGHT/2:
            self.set_end_hook(Hook.TOP)
        elif end_node_xy[1] + NODE_HEIGHT/2 < start_node_xy[1] - NODE_HEIGHT/2:
            self.set_end_hook(Hook.BOTTOM)
        elif end_node_xy[0] - NODE_WIDTH/2 > start_node_xy[0] + NODE_WIDTH/2:
            self.set_end_hook(Hook.LEFT)
        else:
            self.set_end_hook(Hook.RIGHT)
        start = pygame.Vector2(self._start[0].hook(self._start[1]))
        end = pygame.Vector2(self._end[0].hook(self._end[1]))
        arrow = start - end
        angle = arrow.angle_to(pygame.Vector2(0, -1))
        body_length = arrow.length() - ARROW_HEIGHT

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
    def __init__(self, shape, id, text, pos=(0, 0)):
        self._shape = shape
        self._id = id
        self._text = text
        self._pos = pos  # the center of the node
        self._half_height = NODE_HEIGHT / 2
        self._half_width = NODE_WIDTH / 2
        self._width = NODE_WIDTH
        self._height = NODE_HEIGHT
        self._size = MAX_SIZE
        
    def get_shape(self):
        return self._shape
    
    def draw(self, screen):
        if self._shape == Shape.PLACE:
            pygame.draw.circle(screen, TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), NODE_WIDTH/2)
            pygame.draw.circle(screen, TUE_BLUE, (self._pos[0], self._pos[1]), NODE_WIDTH/2, LINE_WIDTH)    
        elif self._shape == Shape.TRANSTION:
            pygame.draw.rect(screen, TUE_LIGHTBLUE, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, NODE_WIDTH, NODE_HEIGHT))
            pygame.draw.rect(screen, TUE_BLUE, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, NODE_WIDTH, NODE_HEIGHT), LINE_WIDTH)
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)
        bold_font = pygame.font.SysFont('Calibri', TEXT_SIZE, bold=True)
        text_line = 0
        for (c, b, l) in self._text:
            if b:
                label = bold_font.render(l, True, c)
            else:
                label = font.render(l, True, c)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH + int(label.get_height()*text_line)
            screen.blit(label, (text_x_pos, text_y_pos))
            text_line += 1
    
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
        return self._id
    
    def set_text(self, text):
        self._text = text


class Visualisation:
    """
    A class for visualizing the provided simulation problem as a Petri net.

    Attributes:
    - sim_problem (SimProblem): the simulation problem to visualize
    - layout_file (str): the file path to the layout file (optional)

    Methods:
    - save_layout(self, filename): saves the layout to a file
    - show(self): shows the visualisation
    """
    def __init__(self, sim_problem, layout_file=None):
        self._problem = sim_problem
        self._nodes = dict()
        self._edges = []
        self._selected_nodes = None
        for var in self._problem.places:
            self._nodes[var.get_id()] = Node(Shape.PLACE, var.get_id(), [(TUE_BLUE, False, var.get_id()), ""])
        for event in self._problem.events:
            event_shape = Node(Shape.TRANSTION, event.get_id(), [(TUE_BLUE, False, event.get_id())])
            self._nodes[event.get_id()] = event_shape
            for incoming in event.incoming:
                self._edges.append(Edge(start=(self._nodes[incoming.get_id()], Hook.RIGHT), end=(event_shape, Hook.LEFT)))
            for outgoing in event.outgoing:
                self._edges.append(Edge(start=(event_shape, Hook.RIGHT), end=(self._nodes[outgoing.get_id()], Hook.LEFT)))
        layout_loaded = False
        if layout_file is not None:
            try:
                self.__load_layout(layout_file)
                layout_loaded = True
            except FileNotFoundError as e:
                print("WARNING: could not load the layout because of the exception below.\nauto-layout will be used.\n", e)
        if not layout_loaded:
            self.__layout()
        self.__set_token_values()
    
    def __set_token_values(self):
        for p in self._problem.places:
            mstr = ""
            ti = 0
            for token in p.marking_order:
                mstr += str(p.marking_count[token]) + "`" + str(token.value) + "@" + str(round(token.time, 2)) + "`"
                if ti < len(p.marking_order) - 1:
                    mstr += "++"
                ti += 1
            self._nodes[p.get_id()].set_text([(TUE_BLUE, False, p.get_id()), (TUE_RED, True, mstr)])

    def __draw(self, screen):
        screen.fill(TUE_GREY)
        for shape in self._nodes.values():
            shape.draw(screen)
        for shape in self._edges:
            shape.draw(screen)
        self.__draw_buttons(screen)
        pygame.display.flip()
    
    def __draw_buttons(self, screen):
        controls = pygame.Surface((31, 31), pygame.SRCALPHA, 32)
        controls = controls.convert_alpha()
        controls.set_alpha(128)
        pygame.draw.polygon(controls, TUE_RED, [(0, 0), (0, 30), (20, 15)])
        pygame.draw.polygon(controls, TUE_RED, [(20, 0), (20, 30), (25, 30), (25, 0)])
        screen.blit(controls, (self._size[0]-100,self._size[1]-50))

    def __layout(self):
        graph = igraph.Graph()
        graph.to_directed()
        for node in self._nodes.values():
            graph.add_vertex(node.get_id())
        for edge in self._edges:            
            graph.add_edge(edge.get_start_node().get_id(), edge.get_end_node().get_id())
        layout = graph.layout_sugiyama()
        layout.rotate(-90)
        layout.scale(NODE_SPACING)
        boundaries = layout.boundaries(border=NODE_WIDTH)
        layout.translate(-boundaries[0][0], -boundaries[0][1])
        canvas_size = layout.boundaries(border=NODE_WIDTH)[1]
        self._size = (min(MAX_SIZE[0], canvas_size[0]), min(MAX_SIZE[1], canvas_size[1]))
        i = 0
        for v in graph.vs:
            xy = layout[i]
            xy  = (round(xy[0]/GRID_SPACING)*GRID_SPACING, round(xy[1]/GRID_SPACING)*GRID_SPACING)
            self._nodes[v["name"]].set_pos(xy)
            i += 1

    def save_layout(self, filename):
            """
            Saves the current layout of the nodes to a file.
            This method can be called after the show method.

            :param filename (str): The name of the file to save the layout to.
            """
            with open(filename, "w") as f:
                f.write(f"{int(self._size[0])},{int(self._size[1])}\n")
                for node in self._nodes.values():
                    if "," in node.get_id() or "\n" in node.get_id():
                        raise Exception("Node " + node.get_id() + ": Saving the layout cannot work if the node id contains a comma or hard return.")
                    f.write(f"{node.get_id()},{node.get_pos()[0]},{node.get_pos()[1]}\n")
    
    def __load_layout(self, filename):
        with open(filename, "r") as f:
            self._size = tuple(map(int, f.readline().strip().split(",")))
            for line in f:
                id, x, y = line.strip().split(",")
                self._nodes[id].set_pos((int(x), int(y)))

    def __get_node_at(self, pos):
        for node in self._nodes.values():
            if node.get_pos()[0] - NODE_WIDTH/2 <= pos[0] <= node.get_pos()[0] + NODE_WIDTH/2 and node.get_pos()[1] - NODE_HEIGHT/2 <= pos[1] <= node.get_pos()[1] + NODE_HEIGHT/2:
                return node
        return None

    def __drag(self, snap=False):
        nodes = self._selected_nodes[0]
        org_pos = self._selected_nodes[1]
        new_pos = pygame.mouse.get_pos()
        x_delta = new_pos[0] - org_pos[0]
        y_delta = new_pos[1] - org_pos[1]
        for node in nodes:
            new_x = node.get_pos()[0] + x_delta
            new_y = node.get_pos()[1] + y_delta
            if snap:
                new_x = round(new_x/GRID_SPACING)*GRID_SPACING
                new_y = round(new_y/GRID_SPACING)*GRID_SPACING
            node.set_pos((new_x, new_y))
        self._selected_nodes = nodes, new_pos

    def show(self):
            """
            Displays the Petri net visualisation in a window.
            The method will block further execution until the window is closed.

            The visualisation can be interacted with using the mouse and keyboard.
            The spacebar can be used to step through the Petri net problem.
            The mouse can be used to drag nodes around.
            """
            pygame.init()
            pygame.font.init()
            pygame.display.set_caption('Petri Net Visualisation')

            clock = pygame.time.Clock()

            screen = pygame.display.set_mode(self._size, pygame.RESIZABLE)
            
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        node = self.__get_node_at(event.pos)
                        if node is not None:
                            self._selected_nodes = [node], event.pos
                        else:
                            self._selected_nodes = self._nodes.values(), event.pos
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
                            self.__set_token_values()
                try:
                    self.__draw(screen)
                except:
                    print("Error while drawing the visualisation.")
                    running = False
                clock.tick(60)

            pygame.quit()
