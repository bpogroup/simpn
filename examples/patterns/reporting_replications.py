import matplotlib.pyplot as plt 
from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import WarmupReporter, ProcessReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
waiting = shop.add_var("waiting")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")

# Define events.
prototype.BPMNStartEvent(shop, [], [waiting], "arrive", lambda: exp(1/10))

prototype.BPMNTask(shop, [waiting, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNEndEvent(shop, [done], [], "complete")

shop.store_checkpoint("initial state")

average_cycle_times = []

NR_REPLICATIONS = 50
SIMULATION_DURATION = 40000
WARMUP_TIME = 20000
for _ in range(NR_REPLICATIONS):
    reporter = ProcessReporter(WARMUP_TIME)
    shop.restore_checkpoint("initial state")
    shop.simulate(SIMULATION_DURATION, reporter)
    print("iteration", _)

    average_cycle_times.append(reporter.total_cycle_time / reporter.nr_completed)

plt.boxplot(average_cycle_times)
plt.xticks([1], labels=["1 cassier"])
plt.ylabel("average cycle time (min)")
plt.show()