import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation

def arrive():
    return [SimToken(random.randint(1, 2))]


my_problem = SimProblem()

arrived = my_problem.add_var("arrived")
resource = my_problem.add_var("resource")
completed = my_problem.add_var("completed")

prototype.BPMNStartEvent(my_problem, [], [arrived], "arrive", lambda: random.expovariate(1), behavior=arrive)
prototype.BPMNTask(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=0.75)], guard=lambda a, r: a[1] == r)
prototype.BPMNEndEvent(my_problem, [completed], [], name="done")

resource.put(1)
resource.put(2)

m = Visualisation(my_problem)
m.show()
