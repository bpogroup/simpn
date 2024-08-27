import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.reporters import EventLogReporter

my_problem = SimProblem()

resource = my_problem.add_place("resource")
resource.put(1)
resource.put(2)

arrived = prototype.BPMNFlow(my_problem, "arrived")
completed = prototype.BPMNFlow(my_problem, "completed")

prototype.BPMNStartEvent(my_problem, [], [arrived], "arrive", lambda: random.expovariate(1))
prototype.BPMNTask(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=0.75)])
prototype.BPMNEndEvent(my_problem, [completed], [], name="done")

my_problem.simulate(1000, EventLogReporter("./temp/prototypes_log.csv", separator=";"))