from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import BPMNStartEvent, BPMNExclusiveSplitGateway
from simpn.prototypes import BPMNExclusiveJoinGateway, BPMNTask, BPMNEndEvent
from simpn.visualisation import Visualisation

from random import seed
seed(42)
from math import exp
from random import randint, choice
from time import time

from os.path import join, exists

LAYOUT_FILE = join("./sim.layout")

problem = SimProblem(
    binding_priority= lambda x: choice(x)
)

resources = problem.add_var("resources")
for i in range(5):
    resources.put(f"res-{i}")
resources.visualize_edges = False
start = problem.add_var("start")
left = problem.add_var("left")
left2 = problem.add_var("checked")
right = problem.add_var("right")
right2 = problem.add_var("cleared")
last = problem.add_var("waiting to send")
last2 = problem.add_var("sent")

BPMNStartEvent(
    problem,
    [],
    [start],
    "claim issued",
    lambda : 0.05
)

def split(c):
    pick = randint(0, 100)
    if pick <= 33:
        return [SimToken(c), None]
    return [None, SimToken(c)]

BPMNExclusiveSplitGateway(
    problem,
    [start],
    [left, right],
    "which way",
    split
)

def check_ticket(c,r):
    return [SimToken((c,r), delay=exp(1/15))]

BPMNTask(
    problem,
    [left, resources],
    [left2, resources],
    "check ticket",
    check_ticket
)

def clear_ticket(c,r):
    return [SimToken((c,r), delay=exp(1/10))]

BPMNTask(
    problem,
    [right, resources],
    [right2, resources],
    "clear ticket",
    check_ticket
)

BPMNExclusiveJoinGateway(
    problem,
    [left2, right2],
    [last],
    "join-a"
)

def send_update(c, r):
    return [ SimToken((c,r), delay=exp(1/12))]

BPMNTask(
    problem,
    [last, resources],
    [last2, resources],
    "sent update",
    send_update
)

BPMNEndEvent(
    problem,
    [last2],
    [],
    "claim handled"
)

start = time()
problem.simulate(250)
end = time() - start 

print(f"finished simulation of 250 ticks in :: {end:.2f} seconds")

# vis = Visualisation(problem, LAYOUT_FILE)
# vis.show()
# vis.save_layout(LAYOUT_FILE)



