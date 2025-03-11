from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = agency.add_var("waiting")
done = agency.add_var("done")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")

# Define events.
def interarrival_time():
  return exp(4)*60

prototype.BPMNStartEvent(agency, [], [waiting], "arrive", interarrival_time)

def start(c, r):
  return [SimToken((c, r), delay=uniform(10, 15))]

prototype.BPMNTask(agency, [waiting, employee], [done, employee], "answer_call", start)

prototype.BPMNEndEvent(agency, [done], [], "complete")

# Simulate with an EventLogReporter.
reporter = EventLogReporter("./temp/agency.csv")
agency.simulate(40*60, reporter)
reporter.close()