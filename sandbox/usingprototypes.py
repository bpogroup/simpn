import random
from simpn.simulator import SimProblem
import simpn.prototypes as prototype


def arrive():
    return [random.randint(1, 2)]


def arrive_delay():
    return [random.expovariate(1)]


my_problem = SimProblem()

arrived = my_problem.add_svar("arrived")
resource = my_problem.add_svar("resource")
completed = my_problem.add_svar("completed")

my_problem.add_stransition([], [arrived], arrive, delay=arrive_delay, prototype=prototype.arrival)
my_problem.add_stransition([arrived, resource], [completed, resource], None, name="task", guard=lambda a, r: a == r, delay=[0.75], prototype=prototype.task)

resource.put(1)
resource.put(2)

print(my_problem)
print()

sim_run = my_problem.simulate(40)
print("\n".join([str(e) for e in sim_run]))
