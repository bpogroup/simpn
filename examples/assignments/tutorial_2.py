from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import start_event, task, end_event

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = agency.add_var("waiting")
done = agency.add_var("done")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")

# Define events.
start_event(agency, [], [waiting], "arrive", lambda: exp(4)*60)

task(agency, [waiting, employee], [done, employee], "answer_call", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

end_event(agency, [done], [], "complete")

# Simulate with an EventLogReporter.
reporter = EventLogReporter("./temp/agency.csv")
agency.simulate(40*60, reporter)
reporter.close()