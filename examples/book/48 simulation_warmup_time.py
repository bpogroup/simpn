from random import expovariate as exp
from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import BPMNStartEvent, BPMNTask, BPMNEndEvent, BPMNFlow, BPMNLane
from simpn.reporters import WarmupReporter
import matplotlib.pyplot as plt


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

reporter = WarmupReporter()
model.simulate(200000, reporter)

plt.plot(reporter.times, reporter.average_cycle_times, color="blue")
plt.xlabel("arrival time (min)")
plt.xticks(range(0, 200001, 50000))
plt.ylabel("cycle time (min)")
plt.savefig("temp/simulation_warmup_time.pdf")
plt.show()