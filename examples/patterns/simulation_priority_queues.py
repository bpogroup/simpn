from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from random import randint
from random import expovariate as exp
from simpn.reporters import EventLogReporter

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue", priority=lambda token: token.value[1])
to_done = shop.add_var("to done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")

# Define events.
prototype.BPMNStartEvent(shop, [], [scan_queue], "customer_arrived", lambda: exp(1/10), behavior=lambda: [SimToken(randint(1, 2))])

prototype.BPMNTask(shop, [scan_queue, cassier], [to_done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNEndEvent(shop, [to_done], [], "done")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_priority_queues.csv")
shop.simulate(24*60, reporter)
reporter.close()
