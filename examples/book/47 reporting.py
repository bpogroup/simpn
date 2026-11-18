from random import expovariate as exp
from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import BPMNStartEvent, BPMNTask, BPMNEndEvent, BPMNFlow, BPMNLane
from simpn.reporters import EventLogReporter


model = SimProblem()

R_idle = BPMNLane(model, "R")
R_idle.put("r1")

T_waiting = BPMNFlow(model, "T_waiting")
E_waiting = BPMNFlow(model, "E_waiting")


BPMNStartEvent(model, [], [T_waiting], "S", lambda: exp(1/10))

BPMNTask(model, [T_waiting, R_idle], [E_waiting, R_idle], 
         "T", 
         lambda c, r: [SimToken((c, r), delay=exp(1/9))])

BPMNEndEvent(model, [E_waiting], [], "E")

reporter = EventLogReporter("temp/reporting.csv")
model.simulate(24*60, reporter)
reporter.close()