from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
to_deferred_choice = shop.add_var("to deferred choice")
scan_queue = shop.add_var("scan queue")
to_leave = shop.add_var("to leave")
left = shop.add_var("left")
to_remove = shop.add_var("to remove")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")

cassier.put("r1")

# Define events.
def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_deferred_choice], "customer_arrived", interarrival_time)


shop.add_event([to_deferred_choice], [scan_queue, to_leave], lambda c: [SimToken(c), SimToken(c, 15)], "deferred_choice")

shop.add_event([scan_queue, to_leave], [left], lambda c, l: [SimToken(c)], "leave", guard=lambda c1, c2: c1==c2)

end_event(shop, [left], [], "left")


def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [scan_queue, cassier], [to_remove, cassier], "scan_groceries", start_scan_groceries)


def remove(c, r):
  return [SimToken(c)]
shop.add_event([to_remove, to_leave], [done], remove, guard=lambda c1, c2: c1==c2)


end_event(shop, [done], [], "done")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_deferred_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()
