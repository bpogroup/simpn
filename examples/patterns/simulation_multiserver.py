from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
for i in range(1, 6):
    cassier.put("r" + str(i))

# Define events.
prototype.BPMNStartEvent(shop, [], [scan_queue], "start", lambda: exp(1/2))

prototype.BPMNTask(shop, [scan_queue, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNEndEvent(shop, [done], [], "complete")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_multiserver.csv")
shop.simulate(24*60, reporter)
reporter.close()
