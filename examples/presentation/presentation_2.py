from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = prototype.BPMNFlow(agency, "waiting")
done = prototype.BPMNFlow(agency, "done")

# Define resources.
employee = agency.add_var("cassier")
employee.put("r1")

# Define events.
prototype.BPMNStartEvent(agency, [], [waiting], "arrive", lambda: exp(1/10))

prototype.BPMNTask(agency, [waiting, employee], [done, employee], "scan", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNEndEvent(agency, [done], [], "complete")

# Simulate with an EventLogReporter.
v = Visualisation(agency, "./temp/presentation_2.layout")
v.show()
v.save_layout("./temp/presentation_2.layout")