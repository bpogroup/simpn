from random import expovariate as exp, uniform
from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import BPMNStartEvent, BPMNTask, BPMNEndEvent, BPMNFlow, BPMNLane
from simpn.reporters import ProcessReporter
import matplotlib.pyplot as plt


model = SimProblem()

R_idle = BPMNLane(model, "R")

T_waiting = BPMNFlow(model, "T_waiting")
E_waiting = BPMNFlow(model, "E_waiting")


BPMNStartEvent(model, [], [T_waiting], "S", lambda: exp(1/10))

BPMNTask(model, [T_waiting, R_idle], [E_waiting, R_idle], 
         "T", 
         lambda c, r: [SimToken((c, r), delay=exp(1/9))])

BPMNEndEvent(model, [E_waiting], [], "E")

model.store_checkpoint("no resources")


def simulate_for(n_resources):
    model.restore_checkpoint("no resources")
    
    for i in range(n_resources):
        R_idle.put(f"r{i+1}")

    model.store_checkpoint("initial state")

    NR_REPLICATIONS = 50
    SIMULATION_DURATION = 40000
    WARMUP_TIME = 20000
    average_cycle_times = []
    for _ in range(NR_REPLICATIONS):
        reporter = ProcessReporter(WARMUP_TIME)
        model.restore_checkpoint("initial state")
        model.simulate(SIMULATION_DURATION, reporter)
        print("iteration", _)

        average_cycle_times.append(reporter.total_cycle_time / reporter.nr_completed)

    return average_cycle_times


results = [simulate_for(3), simulate_for(4)]

BOX_WIDTH = 0.35
plt.boxplot(results, widths=BOX_WIDTH, showfliers=False)
for position, values in enumerate(results, start=1):
    xs = [position + uniform(-BOX_WIDTH / 2, BOX_WIDTH / 2) for _ in values]
    plt.scatter(xs, values, color="blue", s=10, alpha=0.6, zorder=3)
plt.xticks([1, 2], labels=["3 resources", "4 resources"])
plt.ylabel("average cycle time (min)")
plt.savefig("temp/simulation_replications.pdf")
plt.show()