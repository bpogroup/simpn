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
LINE_WIDTH = 3
ARROW_SIZE = 15
TEXT_SIZE = 24

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
    def __init__(self, start, end, intermediate = []):
        self._start = start
        self._end = end
        self._intermediate = intermediate

    def draw(self, screen):
        start = self._start[0].hook(self._start[1])
        end = self._end[0].hook(self._end[1])
        (x, y) = start
        for (x_new, y_new) in self._intermediate:
            dst = ((x_new if x_new >= 0 else x, y_new if y_new >= 0 else y))
            pygame.draw.line(screen, TUE_RED, (x, y), dst, LINE_WIDTH)
            (x, y) = dst
        pygame.draw.line(screen, TUE_RED, (x, y), end, LINE_WIDTH)
        arrowhead = [end]
        if self._end[1] == Hook.LEFT:
            arrowhead.append((end[0] - ARROW_SIZE, int(end[1] - ARROW_SIZE/2)))
            arrowhead.append((end[0] - ARROW_SIZE, int(end[1] + ARROW_SIZE/2)))
        elif self._end[1] == Hook.RIGHT:
            arrowhead.append((end[0] + ARROW_SIZE, int(end[1] - ARROW_SIZE/2)))
            arrowhead.append((end[0] + ARROW_SIZE, int(end[1] + ARROW_SIZE/2)))
        elif self._end[1] == Hook.TOP:
            arrowhead.append((int(end[0] - ARROW_SIZE/2), end[1] - ARROW_SIZE))
            arrowhead.append((int(end[0] + ARROW_SIZE/2), end[1] - ARROW_SIZE))
        elif self._end[1] == Hook.BOTTOM:
            arrowhead.append((int(end[0] - ARROW_SIZE/2), end[1] + ARROW_SIZE))
            arrowhead.append((int(end[0] + ARROW_SIZE/2), end[1] + ARROW_SIZE))
        pygame.draw.polygon(screen, TUE_RED, arrowhead)

    def get_shape(self):
        return Shape.EDGE

        
class Node:
    def __init__(self, shape, text, pos):
        self._shape = shape
        self._text = text
        self._pos = pos  # the center of the node
        self._half_height = NODE_HEIGHT / 2
        self._half_width = NODE_WIDTH / 2
        self._width = NODE_WIDTH
        self._height = NODE_HEIGHT
        
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


class Model:
    def __init__(self):
        self._shapes = []
        
    
    def draw(self, screen):
        screen.fill(TUE_GREY)
        for shape in self._shapes:
            shape.draw(screen)
        pygame.display.flip()

    
    def add_shape(self, shape):
        self._shapes.append(shape)


    def add_shapes(self, shapes):
        self._shapes += shapes


    def get_marking(self):
        return self._marking
    

    def run(self):
        pygame.init()
        pygame.font.init()
        
        screen = pygame.display.set_mode(SIZE)
        
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

        
m = Model()
t11 = Node(Shape.PLACE, ["Task 1","line 2"], (150, 100))
t12 = Node(Shape.TRANSTION, ["Task 2"], (450, 100))
t13 = Node(Shape.TRANSTION, ["Task 2"], (650, 100))
f1 = Edge(start=(t11, Hook.RIGHT), end=(t12, Hook.LEFT))
f2 = Edge(start=(t12, Hook.RIGHT), end=(t13, Hook.LEFT))
m.add_shapes([t11, t12, f1, t13, f2])

# Key here is automated layout.
# igraph Python seems promising: this also has a grid layout
# networkx is also an option

m.run()