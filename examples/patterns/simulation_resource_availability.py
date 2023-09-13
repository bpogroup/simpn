from simpn.simulator import SimProblem, SimToken
from simpn.reporters import SimpleReporter
from simpn.prototypes import start_event, task, end_event

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
start_event(shop, [], [scan_queue], "start", lambda: 1)

# Note: after the task is done, we send cassiers for the 'break check'
task(shop, [scan_queue, cassier], [done, cassier_break_check], "scan_groceries", lambda c, r: [SimToken((c, r), 1)])

# The break check is basically a choice
# if it is more than 2 time units since the cassier last took a break, send the cassier on a break
shop.add_event([cassier_break_check, time], [cassier_break], lambda c, time: [SimToken(c)], guard=lambda c, time: time > c[1] + 2, name="check_break")
# if it was less than or equal to 2 time units, send the cassier back to work
shop.add_event([cassier_break_check, time], [cassier], lambda c, time: [SimToken(c)], guard=lambda c, time: time <= c[1] + 2, name="check_no_break")

# send cassiers on a break back after 2 time units
# (since this only adds a delay, it can also be integrated with the cassier break check)
shop.add_event([cassier_break], [cassier], lambda c: [SimToken(c, 2)], name="send_back_from_break")

end_event(shop, [done], [], "complete")

# Run the simulation.
shop.simulate(5, SimpleReporter())

# The arrival and processing time were made deterministic for the example
# We see that at t=3, the resource goes on a break, such that the next scan_groceries<task:start> event after t=3 is only at t=5, not at t=3