"""
This module contains the glue and blueprints for making a visualisation
module to add new features to a visualisation on demand. The modules are
instantiated and passed to the `Visualisation` class from 
`simpn.visualisation`, where the class will pass along information and 
allow the visualisation to be altered at predefined hook locations.
"""

from pygame.event import Event
from pygame.surface import Surface

class ModuleInterface():
    """
    Ideally, modules are mostly stateless and rely on message passing 
    via the ``handle_event`` hook to consider if they need to do anything at 
    all.

    ## Interface
    Modules can implement the following functions as hooks into the
    visualisation pipeline to implement their behaviour\:

    :create(...): 
        called once within ``Visualisation.__init__``
    :pre_event_loop(...): 
        called once per cycle of game loop
    :handle_event(event,...): 
        called once for each event of a game loop
    :render_sim(screen,...):
        called once for each draw of a game loop, for drawing simulation
        elements that will be zoomable.
    :render_ui(window,...):
        called once for each draw of a game loop, for drawing ui elements
        that are drawn over the simulation and are not zoomable.
    :firing(fired,sim,...):
        called once in the play loop when the next step of the simulation
        is decided. Useful for creating diagnostic ui elements.
    :post_event_loop(sim,...): 
        called once per cycle of game loop
    """

    def __init__(self):
        pass 

    def create(self, sim, *args, **kwargs):
        """
        This hook is called once during the setup of the visualisation.
        This function should setup any internal pygame assets required or
        other functionalities at this point.
        """
        pass 

    def pre_event_loop(self, sim, *args, **kwargs):
        """
        This hook is called at the start of each game loop for the 
        visualisation.
        """
        pass 

    def handle_event(self, event:Event, *args, **kwargs) -> bool:
        """
        This hook is called once for each event produced in the game loop
        of the visualisation. Returns a truthy value to say that the event
        should propagate to other modules and the base visualisation.

        :param event: 
            the event to consider
        :return bool:
            whether the event should be propagated.
        """
        return True

    def render_sim(self, screen:Surface, *args, **kwargs):
        """
        This hook is called once in the draw loop and will be passed a 
        surface to draw onto. This function should be implemented to add
        any drawable elements into the simulation pane.
        """
        pass

    def render_ui(self, window:Surface, *args, **kwargs):
        """
        This hook is called once in the draw loop and will be passed a 
        surface to draw onto. This function should be implemented to add
        any drawable elements into the ui pane.
        """
        pass 

    def firing(self, fired, sim, *args, **kwargs):
        """
        This hook is called once per simulation step and is passed along
        information about the step of the simulation.
        """
        pass

    def post_event_loop(self, sim, *args, **kwargs):
        """
        This hook is called at the end of each game loop for the 
        visualisation.
        """
        pass



