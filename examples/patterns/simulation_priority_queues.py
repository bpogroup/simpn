from simpn.simulator import SimProblem, SimToken
from simpn.prototypes import start_event, task, end_event
from random import randint
from random import expovariate as exp
from simpn.reporters import EventLogReporter

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
def priority(token):
    return token.value[1]
scan_queue = shop.add_var("scan queue", priority=priority)
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")

# Define events.
def interarrival_time():
  return exp(1/10)
start_event(shop, [], [scan_queue], "customer_arrived", interarrival_time, behavior=lambda: [SimToken(randint(1, 2))])

def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
scan_groceries = task(shop, [scan_queue, cassier], [done, cassier], "scan_groceries", start_scan_groceries)

end_event(shop, [done], [], "done")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_priority_queues.csv")
shop.simulate(24*60, reporter)
reporter.close()
