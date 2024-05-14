from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = agency.add_var("waiting")
to_choose = agency.add_var("to_choose")
done_europe = agency.add_var("done_europe")
done_international = agency.add_var("done_international")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")
employee.put("e2")

# Define events.
def arrival_type():
    if uniform(0, 1) <= 0.7:
        return [SimToken("europe")]
    else:
        return [SimToken("international")]

def process_different_types(customer, resource):
    if customer[1] == "europe":
        return [SimToken((customer, resource), delay=uniform(8, 12))]
    else:
        return [SimToken((customer, resource), delay=uniform(10, 15))]

def choose_end_event(c):
    if c[1] == "europe":
        return [SimToken(c), None]
    else:
        return [None, SimToken(c)]

prototype.BPMNStartEvent(agency, [], [waiting], "arrive", lambda: exp(7)*60, behavior=arrival_type)

prototype.BPMNTask(agency, [waiting, employee], [to_choose, employee], "answer_call", process_different_types)

agency.add_event([to_choose], [done_europe, done_international], choose_end_event)

prototype.BPMNEndEvent(agency, [done_europe], [], "complete_europe")

prototype.BPMNEndEvent(agency, [done_international], [], "complete_international")

# Simulate with an EventLogReporter.
reporter = EventLogReporter("./temp/agency_two_types.csv")
agency.simulate(40*60, reporter)
reporter.close()