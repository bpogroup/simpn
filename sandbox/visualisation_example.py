import igraph
import pygame
import traceback
from enum import Enum, auto

SIZE = 1280, 720
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
GRID_SPACING = 100
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

        pygame.draw.polygon(screen, TUE_RED, head_verts)

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

            pygame.draw.polygon(screen, TUE_RED, body_verts)

    def get_shape(self):
        return Shape.EDGE

    def get_start(self):
        return self._start
    
    def get_end(self):
        return self._end
    
    def set_start_hook(self, hook):
        self._start = (self._start[0], hook)
    
    def set_end_hook(self, hook):
        self._end = (self._end[0], hook)


class Node:
    def __init__(self, shape, id, text, pos):
        self._shape = shape
        self._id = id
        self._text = text
        self._pos = pos  # the center of the node
        self._half_height = NODE_HEIGHT / 2
        self._half_width = NODE_WIDTH / 2
        self._width = NODE_WIDTH
        self._height = NODE_HEIGHT
        self._size = SIZE
        
    def get_shape(self):
        return self._shape
    
    def draw(self, screen):
        if self._shape == Shape.PLACE:
            pygame.draw.circle(screen, TUE_LIGHTRED, (self._pos[0], self._pos[1]), NODE_WIDTH/2)
            pygame.draw.circle(screen, TUE_RED, (self._pos[0], self._pos[1]), NODE_WIDTH/2, LINE_WIDTH)    
        elif self._shape == Shape.TRANSTION:
            pygame.draw.rect(screen, TUE_LIGHTRED, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, NODE_WIDTH, NODE_HEIGHT))
            pygame.draw.rect(screen, TUE_RED, pygame.Rect(self._pos[0]-self._half_width, self._pos[1]-self._half_height, NODE_WIDTH, NODE_HEIGHT), LINE_WIDTH)
        font = pygame.font.SysFont('Calibri', TEXT_SIZE)        
        text_line = 0
        for l in self._text:
            label = font.render(l, True, TUE_RED)
            text_height = int(label.get_height()*len(self._text))
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


class Model:
    def __init__(self, sim_problem):
        self._problem = sim_problem
        self._nodes = dict()
        self._edges = []
        for var in self._problem.places:
            self._nodes[var.get_id()] = Node(Shape.PLACE, var.get_id(), [var.get_id()], (0, 0))
        for event in self._problem.events:
            event_shape = Node(Shape.TRANSTION, event.get_id(), [event.get_id()], (0, 0))
            self._nodes[event.get_id()] = event_shape
            for incoming in event.incoming:
                self._edges.append(Edge(start=(self._nodes[incoming.get_id()], Hook.RIGHT), end=(event_shape, Hook.LEFT)))
            for outgoing in event.outgoing:
                self._edges.append(Edge(start=(event_shape, Hook.RIGHT), end=(self._nodes[outgoing.get_id()], Hook.LEFT)))
            
    def draw(self, screen):
        screen.fill(TUE_GREY)
        for shape in self._nodes.values():
            shape.draw(screen)
        for shape in self._edges:
            shape.draw(screen)
        pygame.display.flip()
    
    def layout(self):
        graph = igraph.Graph()
        graph.to_directed()
        for node in self._nodes.values():
            graph.add_vertex(node.get_id())
        for edge in self._edges:            
            graph.add_edge(edge.get_start()[0].get_id(), edge.get_end()[0].get_id())
        layout = graph.layout_sugiyama()
        layout.rotate(-90)
        layout.scale(NODE_SPACING)
        boundaries = layout.boundaries(border=NODE_WIDTH)
        layout.translate(-boundaries[0][0], -boundaries[0][1])
        self._size = layout.boundaries(border=NODE_WIDTH)[1]
        i = 0
        for v in graph.vs:
            xy = layout[i]
            xy  = (int(xy[0]/GRID_SPACING)*GRID_SPACING, int(xy[1]/GRID_SPACING)*GRID_SPACING)
            self._nodes[v["name"]].set_pos(xy)
            i += 1
        for edge in self._edges:
            start = edge.get_start()
            end = edge.get_end()
            start_node_xy = start[0].get_pos()
            end_node_xy = end[0].get_pos()
            if start_node_xy[1] - NODE_HEIGHT/2 > end_node_xy[1] + NODE_HEIGHT/2:
                edge.set_start_hook(Hook.TOP)
            elif start_node_xy[1] + NODE_HEIGHT/2 < end_node_xy[1] - NODE_HEIGHT/2:
                edge.set_start_hook(Hook.BOTTOM)
            elif start_node_xy[0] - NODE_WIDTH/2 > end_node_xy[0] + NODE_WIDTH/2:
                edge.set_start_hook(Hook.LEFT)
            else:
                edge.set_start_hook(Hook.RIGHT)
            if end_node_xy[1] - NODE_HEIGHT/2 > start_node_xy[1] + NODE_HEIGHT/2:
                edge.set_end_hook(Hook.TOP)
            elif end_node_xy[1] + NODE_HEIGHT/2 < start_node_xy[1] - NODE_HEIGHT/2:
                edge.set_end_hook(Hook.BOTTOM)
            elif end_node_xy[0] - NODE_WIDTH/2 > start_node_xy[0] + NODE_WIDTH/2:
                edge.set_end_hook(Hook.LEFT)
            else:
                edge.set_end_hook(Hook.RIGHT)

    def run(self):
        pygame.init()
        pygame.font.init()
        
        screen = pygame.display.set_mode(self._size)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            try:
                self.draw(screen)
            except:
                traceback.print_exc()
                running = False
            
        pygame.quit()

        
from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.prototypes import task, start_event, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
to_split = shop.add_var("to split")
scan_queue = shop.add_var("scan queue")
atm_queue = shop.add_var("atm queue")
wait_sync_w_atm = shop.add_var("waiting for synchronization with atm")
wait_sync_w_scan = shop.add_var("waiting for synchronization with scanning")
to_done = shop.add_var("to done")

# Define resources.
cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

# Define events.
def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_split], "arrive", interarrival_time)


shop.add_event([to_split], [scan_queue, atm_queue], lambda c: [SimToken(c), SimToken(c)], name="split")


def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [scan_queue, cassier], [wait_sync_w_atm, cassier], "scan_groceries", start_scan_groceries)

def start_use_atm(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [atm_queue, atm], [wait_sync_w_scan, atm], "use_atm", start_use_atm)


shop.add_event([wait_sync_w_atm, wait_sync_w_scan], [to_done], lambda c1, c2: [SimToken(c1)], name="join", guard=lambda c1, c2: c1 == c2)


end_event(shop, [to_done], [], "done")


m = Model(shop)
m.layout()
m.run()