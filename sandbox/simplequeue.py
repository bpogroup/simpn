import random
from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter

my_problem = SimProblem()

arrival = my_problem.add_var("arrival")
arrived = my_problem.add_var("arrived")
busy = my_problem.add_var("busy")
resource = my_problem.add_var("resource")
completed = my_problem.add_var("completed")


def arrive(a):
    return [SimToken(a, delay=random.expovariate(1)), SimToken(random.randint(1, 2))]


my_problem.add_event([arrival], [arrival, arrived], arrive)


def start(a, r):
    return [SimToken((a, r), delay=0.75)]


my_problem.add_event([arrived, resource], [busy], start, guard=lambda a, r: a == r)


def complete(b):
    return [SimToken(b[0], delay=0), SimToken(b[1], delay=0)]


my_problem.add_event([busy], [completed, resource], complete)


resource.put(1)
resource.put(2)
arrival.put(None)

print(my_problem)
my_problem.simulate(40, SimpleReporter())
