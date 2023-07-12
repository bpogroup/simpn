import random
from simpn.simulator import SimProblem
import simpn.prototypes as prototype
from simpn.reporters import SimpleReporter


def arrive():
    return [random.randint(1, 2)]


def arrive_delay():
    return [random.expovariate(1)]


my_problem = SimProblem()

arrived = my_problem.add_svar("arrived")
resource = my_problem.add_svar("resource")
completed = my_problem.add_svar("completed")
done = my_problem.add_svar("done")

my_problem.add_stransition([], [arrived], arrive, delay=arrive_delay, prototype=prototype.start_event)
my_problem.add_stransition([arrived, resource], [completed, resource], None, name="task", guard=lambda a, r: a[1] == r, delay=[0.75], prototype=prototype.task)
my_problem.add_stransition([completed], [done], None, name="done", prototype=prototype.end_event)

resource.put(1)
resource.put(2)

print(my_problem)
print()

my_problem.simulate(40, SimpleReporter())
