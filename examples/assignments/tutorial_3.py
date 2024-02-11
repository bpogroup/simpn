import matplotlib.pyplot as plt 
from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation
from random import expovariate as exp
from random import uniform
from simpn.prototypes import start_event, task, end_event

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = agency.add_var("waiting")
done = agency.add_var("done")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")
employee.put("e2")

# Define events.
start_event(agency, [], [waiting], "arrive", lambda: exp(7)*60)

task(agency, [waiting, employee], [done, employee], "answer_call", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

end_event(agency, [done], [], "complete")

# Simulate once with a visualisation.
visualisation = Visualisation(agency)
visualisation.show()
