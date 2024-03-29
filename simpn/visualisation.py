import igraph
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
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
    def __init__(self, model_node):
        self._model_node = model_node
        self._pos = (0, 0)  # the center of the node
        self._half_height = NODE_HEIGHT / 2
        self._half_width = NODE_WIDTH / 2
        self._width = NODE_WIDTH
        self._height = NODE_HEIGHT
        self._size = MAX_SIZE
            
    def draw(self, screen):
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
        raise Exception("Node.get_id must be implemented at subclass level.")
        

class PlaceViz(Node):
    def __init__(self, model_node):
        super().__init__(model_node)
    
    def draw(self, screen):
        pygame.draw.circle(screen, TUE_LIGHTBLUE, (self._pos[0], self._pos[1]), NODE_WIDTH/2)
        pygame.draw.circle(screen, TUE_BLUE, (self._pos[0], self._pos[1]), NODE_WIDTH/2, LINE_WIDTH)    
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)
        bold_font = pygame.font.SysFont('Calibri', TEXT_SIZE, bold=True)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))

        # draw marking
        mstr = "["
        ti = 0
        for token in self._model_node.marking:
            mstr += str(token.value) + "@" + str(round(token.time, 2))
            if ti < len(self._model_node.marking) - 1:
                mstr += ", "
            ti += 1
        mstr += "]"
        label = label = bold_font.render(mstr, True, TUE_RED)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH + int(label.get_height())
        screen.blit(label, (text_x_pos, text_y_pos))

    def get_id(self):
        return self._model_node.get_id()


class TransitionViz(Node):
    def __init__(self, model_node):
        super().__init__(model_node)
    
    def draw(self, screen):
        pygame.draw.rect(screen, TUE_LIGHTBLUE, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, NODE_WIDTH, NODE_HEIGHT))
        pygame.draw.rect(screen, TUE_BLUE, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, NODE_WIDTH, NODE_HEIGHT), LINE_WIDTH)
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)

        # draw label
        label = font.render(self._model_node.get_id(), True, TUE_BLUE)
        text_x_pos = self._pos[0] - int(label.get_width()/2)
        text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH
        screen.blit(label, (text_x_pos, text_y_pos))

    def get_id(self):
        return self._model_node.get_id()


class Button(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((31, 31), pygame.SRCALPHA, 32)
        self.image = self.image.convert_alpha()
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def draw(self, screen):
        screen.blit(self.image, self.rect)
    

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
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption('Petri Net Visualisation')
        
        self.__running = False
        self._problem = sim_problem
        self._nodes = dict()
        self._edges = []
        self._selected_nodes = None        
        
        for var in self._problem.places:
            self._nodes[var.get_id()] = PlaceViz(var)
        for event in self._problem.events:
            event_shape = TransitionViz(event)
            self._nodes[event.get_id()] = event_shape
            for incoming in event.incoming:
                node_id = incoming.get_id()
                if node_id.endswith(".queue"):
                    node_id = node_id[:-len(".queue")]
                self._edges.append(Edge(start=(self._nodes[node_id], Hook.RIGHT), end=(event_shape, Hook.LEFT)))
            for outgoing in event.outgoing:
                node_id = outgoing.get_id()
                if node_id.endswith(".queue"):
                    node_id = node_id[:-len(".queue")]
                self._edges.append(Edge(start=(event_shape, Hook.RIGHT), end=(self._nodes[node_id], Hook.LEFT)))
        layout_loaded = False
        if layout_file is not None:
            try:
                self.__load_layout(layout_file)
                layout_loaded = True
            except FileNotFoundError as e:
                print("WARNING: could not load the layout because of the exception below.\nauto-layout will be used.\n", e)
        if not layout_loaded:
            self.__layout()        

        self.__screen = pygame.display.set_mode(self._size, pygame.RESIZABLE)
        self._buttons = self.__init_buttons()
    
    def __draw(self):
        self.__screen.fill(TUE_GREY)
        for shape in self._nodes.values():
            shape.draw(self.__screen)
        for shape in self._edges:
            shape.draw(self.__screen)
        self.__draw_buttons()
        pygame.display.flip()

    def action_step(self):
        self._problem.step()
    
    def __init_buttons(self):
        # No buttons for now.
        # btn_step = Button()        
        # pygame.draw.polygon(btn_step.image, TUE_RED, [(0, 0), (0, 30), (20, 15)])
        # pygame.draw.polygon(btn_step.image, TUE_RED, [(20, 0), (20, 30), (25, 30), (25, 0)])
        # btn_step.set_pos(self._size[0]-100, self._size[1]-50)
        # btn_step.action = self.action_step

        # return [btn_step]
        return []

    def __draw_buttons(self):
        for btn in self._buttons:
            btn.draw(self.__screen)

    def __click_button_at(self, pos):
        for btn in self._buttons:
            if btn.rect.collidepoint(pos):
                btn.action()
                return True
        return False

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

    def __handle_event(self, event):
        if event.type == pygame.QUIT:
            self.__running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            button_clicked = self.__click_button_at(event.pos)
            if not button_clicked:
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
                for event in pygame.event.get():
                    self.__handle_event(event)
                try:
                    self.__draw()
                except:
                    print("Error while drawing the visualisation.")
                    self.__running = False
                clock.tick(30)

            pygame.quit()
