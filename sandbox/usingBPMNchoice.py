import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


my_problem = SimProblem()

resource = my_problem.add_var("resource")
resource.put(1)
resource.put(2)

start_to_and_split = prototype.BPMNFlow(my_problem, "start_to_end_plit")
and_split_to_a = prototype.BPMNFlow(my_problem, "and_split_to_a")
and_split_to_b = prototype.BPMNFlow(my_problem, "and_split_to_b")
a_to_join = prototype.BPMNFlow(my_problem, "a_to_join")
b_to_join = prototype.BPMNFlow(my_problem, "b_to_join")
join_to_end = prototype.BPMNFlow(my_problem, "join_to_end")

def choice_behavior(c):
    # a single input from the case incoming to the split
    # the split has two outgoing arcs, the choice randomly selects one and puts a token on that arc, but not on the other
    if random.random() <= 0.5:
        return [SimToken(c), None]
    else:
        return [None, SimToken(c)]


prototype.BPMNStartEvent(my_problem, [], [start_to_and_split], "arrive", lambda: random.expovariate(1))
prototype.BPMNExclusiveSplitGateway(my_problem, [start_to_and_split], [and_split_to_a, and_split_to_b], "xor split", behavior=choice_behavior)
prototype.BPMNTask(my_problem, [and_split_to_a, resource], [a_to_join, resource], "task a", lambda a, r: [SimToken((a, r), delay=0.4)])
prototype.BPMNTask(my_problem, [and_split_to_b, resource], [b_to_join, resource], "task b", lambda a, r: [SimToken((a, r), delay=0.5)])
prototype.BPMNExclusiveJoinGateway(my_problem, [a_to_join, b_to_join], [join_to_end], "xor join")
prototype.BPMNEndEvent(my_problem, [join_to_end], [], name="end")

vis = Visualisation(my_problem, "./temp/choice_layout.txt")
vis.show()
vis.save_layout("./temp/choice_layout.txt")