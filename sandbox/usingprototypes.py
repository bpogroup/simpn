import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.reporters import SimpleReporter


def arrive():
    return [SimToken(random.randint(1, 2))]


my_problem = SimProblem()

arrived = my_problem.add_var("arrived")
resource = my_problem.add_var("resource")
completed = my_problem.add_var("completed")

prototype.start_event(my_problem, [], [arrived], "arrive", lambda: random.expovariate(1), behavior=arrive)
prototype.task(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), 0.75)], guard=lambda a, r: a[1] == r)
prototype.end_event(my_problem, [completed], [], name="done")

resource.put(1)
resource.put(2)

print(my_problem)
print()

my_problem.simulate(40, SimpleReporter())
