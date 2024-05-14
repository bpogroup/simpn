from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
to_choose = agency.add_var("to_choose")
waiting_europe = agency.add_var("waiting_europe")
waiting_international = agency.add_var("waiting_international")
done_europe = agency.add_var("done_europe")
done_international = agency.add_var("done_international")

# Define resources.
employee_europe = agency.add_var("employee_europe")
employee_europe.put("ee")
employee_international = agency.add_var("employee_international")
employee_international.put("ei")

# Define events.
def arrival_type():
    if uniform(0, 1) <= 0.7:
        return [SimToken("europe")]
    else:
        return [SimToken("international")]

def choose_task(c):
    if c[1] == "europe":
        return [SimToken(c), None]
    else:
        return [None, SimToken(c)]

prototype.BPMNStartEvent(agency, [], [to_choose], "arrive", lambda: exp(7)*60, behavior=arrival_type)

agency.add_event([to_choose], [waiting_europe, waiting_international], choose_task)

prototype.BPMNTask(agency, [waiting_europe, employee_europe], [done_europe, employee_europe], "answer_call_europe", lambda c, r: [SimToken((c, r), delay=uniform(8, 12))])

prototype.BPMNTask(agency, [waiting_international, employee_international], [done_international, employee_international], "answer_call_international", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

prototype.BPMNEndEvent(agency, [done_europe], [], "complete_europe")

prototype.BPMNEndEvent(agency, [done_international], [], "complete_international")

# Simulate with an EventLogReporter.
reporter = EventLogReporter("./temp/agency_two_tasks.csv")
agency.simulate(40*60, reporter)
reporter.close()