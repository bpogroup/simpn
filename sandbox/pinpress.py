import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


my_problem = SimProblem()

pinpress = my_problem.add_var("pinpress")
pinpress.put("pinpress")

pinpress_capacity = my_problem.add_var("pinpress_capacity")
pinpress_capacity.put(1)

arrived = prototype.BPMNFlow(my_problem, "arrived")
completed = prototype.BPMNFlow(my_problem, "completed")

prototype.BPMNStartEvent(my_problem, [], [arrived], "arrive", lambda: random.expovariate(1))
prototype.BPMNTask(my_problem, [arrived, resource], [completed, resource], "Transition into Pin Press", lambda a, r: [SimToken((a, r), delay=0.75)])
prototype.BPMNTask(my_problem, [arrived, resource], [completed, resource], "Pin Pressing", lambda a, r: [SimToken((a, r), delay=0.75)])
prototype.BPMNTask(my_problem, [arrived, resource], [completed, resource], "Transition out of Pin Press", lambda a, r: [SimToken((a, r), delay=0.75)])
prototype.BPMNEndEvent(my_problem, [completed], [], name="done")

vis = Visualisation(my_problem)
