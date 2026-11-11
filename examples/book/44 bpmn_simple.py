from random import expovariate as exp
from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import BPMNFlow, BPMNStartEvent, BPMNTask, BPMNEndEvent, BPMNLane
from simpn.reporters import SimpleReporter

model = SimProblem()

R = BPMNLane(model, "R")
R.put("r1")

T_waiting = BPMNFlow(model, "T_waiting")
E_waiting = BPMNFlow(model, "E_waiting")

BPMNStartEvent(model, [], [T_waiting], "S", lambda: exp(1))
BPMNTask(model, [T_waiting, R], [E_waiting, R], "T", lambda c, r: [SimToken((c, r), delay=exp(1/0.8))])
BPMNEndEvent(model, [E_waiting], [], name="E")

model.simulate(2.5, SimpleReporter())