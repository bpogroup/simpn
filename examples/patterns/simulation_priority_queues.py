from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import start_event, task, end_event
from random import randint
from random import expovariate as exp
from simpn.reporters import EventLogReporter

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue", priority=lambda token: token.value[1])
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")

# Define events.
start_event(shop, [], [scan_queue], "customer_arrived", lambda: exp(1/10), behavior=lambda: [SimToken(randint(1, 2))])

task(shop, [scan_queue, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

end_event(shop, [done], [], "done")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_priority_queues.csv")
shop.simulate(24*60, reporter)
reporter.close()
