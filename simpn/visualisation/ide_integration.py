"""
Integration layer between the existing Visualisation class and the IDE PygameWidget.
This module adapts the base.py Visualisation to work within a PyQt6 widget.
"""

import pygame
from typing import Optional, Tuple
from simpn.visualisation.base import Visualisation


class IDEVisualisation:
    """
    Adapter class that wraps the Visualisation class to work within the IDE's PygameWidget.
    
    This class manages the rendering of a Petri net visualisation onto a pygame surface
    that can be displayed in the IDE's PygameWidget.
    """
    
    def __init__(self, sim_problem, 
                 layout_file=None, 
                 grid_spacing=50, 
                 node_spacing=100, 
                 layout_algorithm="sugiyama",
                 extra_modules=None):
        """
        Initialize the IDE visualisation adapter.
        
        :param sim_problem: The simulation problem to visualize
        :param layout_file: Optional file path to load layout from
        :param grid_spacing: Spacing between grid lines
        :param node_spacing: Spacing between nodes in layout
        :param layout_algorithm: Algorithm to use for layout (sugiyama, davidson_harel, grid, auto)
        :param extra_modules: Additional visualization modules
        """
        # Store initialization parameters
        self._sim_problem = sim_problem
        self._layout_file = layout_file
        self._grid_spacing = grid_spacing
        self._node_spacing = node_spacing
        self._layout_algorithm = layout_algorithm
        self._extra_modules = extra_modules
        
        # Create the base visualisation but don't show it
        self._viz = Visualisation(
            sim_problem=sim_problem,
            layout_file=layout_file,
            grid_spacing=grid_spacing,
            node_spacing=node_spacing,
            layout_algorithm=layout_algorithm,
            extra_modules=extra_modules
        )
        
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
            
        self._selected_nodes = None
        self._dragging = False
        
    def get_nodes(self):
        """Get the dictionary of visualization nodes."""
        return self._viz._nodes
    
    def get_edges(self):
        """Get the list of edges."""
        return self._viz._edges
    
    def get_problem(self):
        """Get the simulation problem."""
        return self._viz._problem
    
    def get_modules(self):
        """Get the visualization modules."""
        return self._viz._modules
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the Petri net visualization onto the provided pygame surface.
        
        :param surface: The pygame surface to render onto
        """
        # Fill background
        from simpn.visualisation.base import TUE_GREY
        
        # Get zoom level
        zoom_level = self._viz._zoom_level
        
        # Create a scaled surface for zooming
        scaled_width = int(surface.get_width() / zoom_level)
        scaled_height = int(surface.get_height() / zoom_level)
        scaled_surface = pygame.Surface((scaled_width, scaled_height))
        scaled_surface.fill(TUE_GREY)
        
        # Draw edges on scaled surface
        for edge in self._viz._edges:
            edge.draw(scaled_surface)
        
        # Draw nodes on scaled surface
        for node in self._viz._nodes.values():
            node._curr_time = self._viz._problem.clock
            node.draw(scaled_surface)
        
        # Render simulation modules on scaled surface
        for mod in self._viz._modules:
            mod.render_sim(scaled_surface)
        
        # Scale the surface back to original size and blit
        surface.fill(TUE_GREY)
        scaled_back = pygame.transform.smoothscale(scaled_surface, (surface.get_width(), surface.get_height()))
        surface.blit(scaled_back, (0, 0))
    
    def handle_mouse_press(self, pos: Tuple[int, int], button: int) -> Optional[object]:
        """
        Handle mouse press events.
        
        :param pos: (x, y) position of the mouse click
        :param button: Mouse button pressed (1=left, 2=middle, 3=right)
        :return: The node that was clicked, or None
        """
        if button == 1:  # Left click
            node = self._get_node_at(pos)
            if node is not None:
                self._selected_nodes = [node], pos
                self._dragging = True
                return node
            else:
                self._selected_nodes = list(self._viz._nodes.values()), pos
                self._dragging = True
        return None
    
    def handle_mouse_release(self, pos: Tuple[int, int], button: int) -> None:
        """
        Handle mouse release events.
        
        :param pos: (x, y) position of the mouse release
        :param button: Mouse button released
        """
        if button == 1 and self._selected_nodes is not None:
            self._drag(pos, snap=True)
            self._selected_nodes = None
            self._dragging = False
    
    def handle_mouse_motion(self, pos: Tuple[int, int]) -> None:
        """
        Handle mouse motion events.
        
        :param pos: (x, y) position of the mouse
        """
        if self._dragging and self._selected_nodes is not None:
            self._drag(pos, snap=False)
    
    def _get_node_at(self, pos: Tuple[int, int]) -> Optional[object]:
        """
        Get the node at the specified position.
        
        :param pos: (x, y) position to check
        :return: Node at position or None
        """
        # Scale position by zoom level
        zoom_level = self._viz._zoom_level
        scaled_pos = (pos[0] / zoom_level, pos[1] / zoom_level)
        
        for node in self._viz._nodes.values():
            node_pos = node.get_pos()
            if (node_pos[0] - max(node._width/2, 10) <= scaled_pos[0] <= node_pos[0] + max(node._width/2, 10) and
                node_pos[1] - max(node._height/2, 10) <= scaled_pos[1] <= node_pos[1] + max(node._height/2, 10)):
                return node
        return None
    
    def _drag(self, new_pos: Tuple[int, int], snap: bool = False) -> None:
        """
        Drag selected nodes to a new position.
        
        :param new_pos: New mouse position
        :param snap: Whether to snap to grid
        """
        if self._selected_nodes is None:
            return
            
        nodes, org_pos = self._selected_nodes
        zoom_level = self._viz._zoom_level
        x_delta = (new_pos[0] - org_pos[0]) / zoom_level
        y_delta = (new_pos[1] - org_pos[1]) / zoom_level
        
        for node in nodes:
            new_x = node.get_pos()[0] + x_delta
            new_y = node.get_pos()[1] + y_delta
            if snap:
                new_x = round(new_x / self._grid_spacing) * self._grid_spacing
                new_y = round(new_y / self._grid_spacing) * self._grid_spacing
            node.set_pos((new_x, new_y))
        
        self._selected_nodes = nodes, new_pos
    
    def step(self) -> object:
        """
        Execute one step of the simulation.
        
        :return: The fired binding, or None
        """
        fired_binding = self._viz._problem.step()
        
        if fired_binding is not None:
            for mod in self._viz._modules:
                mod.firing(fired_binding, self._viz._problem)
        
        return fired_binding
    
    def save_layout(self, filename: str) -> None:
        """
        Save the current layout to a file.
        
        :param filename: Path to save the layout file
        """
        self._viz.save_layout(filename)
    
    def get_zoom_level(self) -> float:
        """Get the current zoom level."""
        return self._viz._zoom_level
    
    def set_zoom_level(self, zoom: float) -> None:
        """Set the zoom level."""
        self._viz._zoom_level = max(0.3, min(zoom, 3.0))
    
    def zoom(self, action: str) -> None:
        """
        Zoom the visualization.
        
        :param action: One of 'increase', 'decrease', 'reset'
        """
        self._viz.zoom(action)
