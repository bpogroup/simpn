from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter, SimpleReporter
from simpn.prototypes import start_event, task, end_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
waiting = shop.add_var("waiting")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")

# Define events.
start_event(shop, [], [waiting], "arrive", lambda: exp(1/10))

task(shop, [waiting, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), exp(1/9))])

end_event(shop, [done], [], "complete")

# Simulate once with a simple reporter.
shop.simulate(24*60, SimpleReporter())
# Simulate once with an EventLogReporter.
reporter = EventLogReporter("./temp/simulation_simple_prototypes.csv")
shop.simulate(24*60, reporter)
reporter.close()

# Writing down start/completion events for each task is tedious.
# For that reason we have a convenience function that does that for us (the task function).
# All that the task function does is take the information it is provided and create start and complete events.
# So do not think of it as a single event, but rather as something that creates two events.
# We also introduce BPMN start and and events. These generate single events. However, they use a notation that is subsequently used
# by the EventLogReporter to generate a log that can be mined.