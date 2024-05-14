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

# Simulate once with a warmup reporter.
reporter = WarmupReporter()
shop.simulate(200000, reporter)

plt.plot(reporter.times, reporter.average_cycle_times, color="blue")
plt.xlabel("arrival time (min)")
plt.xticks(range(0, 200001, 50000))
plt.ylabel("cycle time (min)")
plt.show()

# Simulate with and without warmup.
reporter_w = ProcessReporter(25000)
reporter_wo = ProcessReporter()

shop.restore_checkpoint("initial state")

shop.simulate(50000, [reporter_w, reporter_wo])

print("With warmup:")
reporter_w.print_result()
print("Without warmup:")
reporter_wo.print_result()
