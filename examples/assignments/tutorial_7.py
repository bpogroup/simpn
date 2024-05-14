import matplotlib.pyplot as plt 
from simpn.simulator import SimProblem, SimToken
from simpn.reporters import EventLogReporter
from random import expovariate as exp
from random import uniform
import simpn.prototypes as prototype

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
to_deferred_choice = agency.add_var("to deferred choice")
waiting = agency.add_var("waiting")
to_leave = agency.add_var("to leave")
done = agency.add_var("done")
to_left = agency.add_var("to left")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")
employee.put("e2")

# Define events.
prototype.BPMNStartEvent(agency, [], [to_deferred_choice], "arrive", lambda: exp(7)*60)

agency.add_event([to_deferred_choice], [waiting, to_leave], lambda c: [SimToken(c), SimToken(c, delay=5)], "deferred_choice")

prototype.BPMNTask(agency, [waiting, employee], [done, employee], "answer_call", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

agency.add_event([to_leave, waiting], [to_left], lambda c1, c2: [SimToken(c1)], "leave", guard=lambda c1, c2: c1==c2)

prototype.BPMNEndEvent(agency, [done], [], "complete")

prototype.BPMNEndEvent(agency, [to_left], [], "left")

# Simulate once with a visualisation.
reporter = EventLogReporter("./temp/agency_leaving.csv")
agency.simulate(40*60, reporter)
reporter.close()