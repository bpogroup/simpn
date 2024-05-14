import matplotlib.pyplot as plt 
from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation
from random import expovariate as exp
from random import uniform
import simpn.prototypes as prototype

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
to_choice = agency.add_var("to choice")
waiting = agency.add_var("waiting")
done = agency.add_var("done")
to_left = agency.add_var("to left")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")
employee.put("e2")

# Define events.
def check_free(customer, employee_queue):
    if len(employee_queue) > 0:
        return [SimToken(customer), None, employee_queue]
    else:
        return [None, SimToken(customer), employee_queue]

prototype.BPMNStartEvent(agency, [], [to_choice], "arrive", lambda: exp(7)*60)

agency.add_event([to_choice, employee.queue], [waiting, to_left, employee.queue], check_free)

prototype.BPMNTask(agency, [waiting, employee], [done, employee], "answer_call", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

prototype.BPMNEndEvent(agency, [done], [], "complete")

prototype.BPMNEndEvent(agency, [to_left], [], "left")

# Simulate once with a visualisation.
visualisation = Visualisation(agency)
visualisation.show()
