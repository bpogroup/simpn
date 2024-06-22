import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


my_problem = SimProblem()

pinpress = my_problem.add_var("pinpress")
pinpress.put("pinpress")

operator = my_problem.add_var("operator")
operator.put("operator")

pinpress_capacity = my_problem.add_var("pinpress_capacity")
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