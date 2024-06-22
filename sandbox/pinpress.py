from simpn.simulator import SimProblem, SimToken, SimVar
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation, Node, TUE_BLUE, TUE_RED, LINE_WIDTH, TEXT_SIZE, TUE_LIGHTBLUE
import pygame


# This class is just here to visualize the capacity place as a triangle.
# I think it is a bit superfluous, so you can also simply remove it.
class Capacity(SimVar):
    def __init__(self, model, _id, priority=lambda token: token.time):
        """
        A SimVar that represents a queue in a queueing system.
        It is just a SimVar with a different visualisation.
        """
        super().__init__(_id, priority)

        model.add_prototype_var(self)

    class CapacityViz(Node):
        def __init__(self, model_node):
            super().__init__(model_node)
        
        def draw(self, screen):
            x, y = self._pos
            hw, hh = self._half_width, self._half_height
            pygame.draw.polygon(screen, TUE_LIGHTBLUE, ((x-hw, y+hh), (x, y-hh), (x+hw, y+hh)))
            pygame.draw.polygon(screen, TUE_BLUE, ((x-hw, y+hh), (x, y-hh), (x+hw, y+hh)), LINE_WIDTH)

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
            label = bold_font.render(mstr, True, TUE_RED)
            text_x_pos = self._pos[0] - int(label.get_width()/2)
            text_y_pos = self._pos[1] + self._half_height + LINE_WIDTH + int(label.get_height())
            screen.blit(label, (text_x_pos, text_y_pos))        

    def get_visualisation(self):
        return self.CapacityViz(self)





# this is where the actual example starts
my_problem = SimProblem()

pinpress = my_problem.add_var("pinpress")
pinpress.put("pinpress")

operator = my_problem.add_var("operator")
operator.put("operator")

# pinpress_capacity = my_problem.add_var("pinpress_capacity")
pinpress_capacity = Capacity(my_problem, "pinpress_capacity")  # this line can also be replaced by the line above to simply represent the capacity as a place
pinpress_capacity.put(1)

flow_to_transition_in = prototype.BPMNFlow(my_problem, "to_transition_in")
flow_to_pinpressing = prototype.BPMNFlow(my_problem, "to_pinpressing")
flow_to_transition_out = prototype.BPMNFlow(my_problem, "to_transition_out")
flow_to_completed = prototype.BPMNFlow(my_problem, "to_completed")

prototype.BPMNStartEvent(my_problem, [], [flow_to_transition_in], "arrive", lambda: 4)
prototype.BPMNTask(my_problem, [flow_to_transition_in, operator, pinpress_capacity], [flow_to_pinpressing, operator], "Transition into Pin Press", lambda c, o, cap: [SimToken((c, o), delay=1)])
prototype.BPMNTask(my_problem, [flow_to_pinpressing, pinpress], [flow_to_transition_out, pinpress], "Pin Pressing", lambda c, p: [SimToken((c, p), delay=1)])
prototype.BPMNTask(my_problem, [flow_to_transition_out, operator], [flow_to_completed, operator, pinpress_capacity], "Transition out of Pin Press", lambda c, o: [SimToken((c, o), delay=1)], outgoing_behavior=lambda i: [SimToken(i[0]), SimToken(i[1]), SimToken(1)])
prototype.BPMNEndEvent(my_problem, [flow_to_completed], [], name="done")


vis = Visualisation(my_problem)
vis.show()