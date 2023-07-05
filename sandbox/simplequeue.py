import random
from simpn.simulator import SimProblem


my_problem = SimProblem()

arrival = my_problem.add_svar("arrival")
arrived = my_problem.add_svar("arrived")
busy = my_problem.add_svar("busy")
resource = my_problem.add_svar("resource")
completed = my_problem.add_svar("completed")


def arrive(a):
    return [None, random.randint(1, 2)]


def arrive_delay(a):
    return [random.expovariate(1), 0]


my_problem.add_stransition([arrival], [arrival, arrived], arrive, delay=arrive_delay)


def start(a, r):
    return [(a, r)]


my_problem.add_stransition([arrived, resource], [busy], start, guard=lambda a, r: a == r, delay=[0.75])


def complete(b):
    return [b[0], b[1]]


my_problem.add_stransition([busy], [completed, resource], complete)


resource.put(1)
resource.put(2)
arrival.put(None)

print(my_problem)
sim_run = my_problem.simulate(40)
print("\n".join([str(e) for e in sim_run]))
