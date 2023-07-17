import random
from simpn.simulator import SimProblem, SimToken, transition
from simpn.reporters import SimpleReporter


my_problem = SimProblem()


@transition(my_problem, ["arrival", "arrived"])
def arrive(arrival):
    return [SimToken(arrival, random.expovariate(1)), SimToken(random.randint(1, 2))]


@transition(my_problem, ["busy"], guard=lambda a, r: a == r)
def start(arrived, resources):
    return [SimToken((arrived, resources), 0.75)]


@transition(my_problem, ["completed", "resources"])
def complete(busy):
    return [SimToken(busy[0], 0), SimToken(busy[1], 0)]


my_problem.svar("resources").put(1)
my_problem.svar("resources").put(2)
my_problem.svar("arrival").put(None)

my_problem.simulate(40, SimpleReporter())