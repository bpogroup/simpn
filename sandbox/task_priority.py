import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


my_problem = SimProblem()

resource = my_problem.add_var("resource")
resource.put(1)
resource.put(2)

arrive_to_a = my_problem.add_var("arrive_to_a")
a_to_b = my_problem.add_var("a_to_b")
b_to_done = my_problem.add_var("b_to_done")

prototype.BPMNStartEvent(my_problem, [], [arrive_to_a], "arrive", lambda: random.expovariate(1))
prototype.BPMNTask(my_problem, [arrive_to_a, resource, a_to_b.queue], [a_to_b, resource], "a", 
                   lambda a, r, q: [SimToken((a, r), delay=0.75)],
                   guard=lambda a, r, q: len(q) == 0
                   )
prototype.BPMNTask(my_problem, [a_to_b, resource], [b_to_done, resource], "b", lambda a, r: [SimToken((a, r), delay=0.75)])
prototype.BPMNEndEvent(my_problem, [b_to_done], [], name="done")

vis = Visualisation(my_problem, "./temp/task_prio_layout.txt")
vis.show()
vis.save_layout("./temp/task_prio_layout.txt")