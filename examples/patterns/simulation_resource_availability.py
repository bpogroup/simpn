from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue")
done = shop.add_var("done")

time = shop.var("time")

# Define resources and resource state variables.
cassier = shop.add_var("cassier") # the variable that contains available cassiers
cassier.put(("r1", 0)) # cassier r1 last returned from a break at t=0
cassier_break = shop.add_var("cassier_break") # the variable that contains cassiers who are on a break
cassier_break_check = shop.add_var("break_check") # the variable that contains cassiers for whom we must check if they go on break

# Define events.
prototype.BPMNStartEvent(shop, [], [scan_queue], "start", lambda: 1)

# Note: after the task is done, we send cassiers for the 'break check'
prototype.BPMNTask(shop, [scan_queue, cassier], [done, cassier_break_check], "scan_groceries", lambda c, r: [SimToken((c, r), delay=1)])

# The break check is basically a choice
def check_break(c, time):
    if time > c[1] + 2: # if it is more than 2 time units since the cassier last took a break, send the cassier on a break
        return [SimToken(c, delay=2)]
    else: # if it was less than or equal to 2 time units, send the cassier back to work
        return [SimToken(c)]
shop.add_event([cassier_break_check, time], [cassier], check_break)

prototype.BPMNEndEvent(shop, [done], [], "complete")

# Run the simulation.
shop.simulate(5, SimpleReporter())

# The arrival and processing time were made deterministic for the example
# We see that at t=3, the resource goes on a break, such that the next scan_groceries<task:start> event after t=3 is only at t=5, not at t=3