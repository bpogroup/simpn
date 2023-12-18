import random
from simpn.simulator import SimProblem, SimToken, event
from simpn.reporters import SimpleReporter


my_problem = SimProblem()


@event(my_problem, ["arrival", "arrived"])
def arrive(arrival):
    return [SimToken(arrival, delay=random.expovariate(1)), SimToken(random.randint(1, 2))]


@event(my_problem, ["busy"], guard=lambda a, r: a == r)
def start(arrived, resources):
    return [SimToken((arrived, resources), delay=0.75)]


@event(my_problem, ["completed", "resources"])
def complete(busy):
    return [SimToken(busy[0], delay=0), SimToken(busy[1], delay=0)]


my_problem.var("resources").put(1)
my_problem.var("resources").put(2)
my_problem.var("arrival").put(None)

my_problem.simulate(40, SimpleReporter())