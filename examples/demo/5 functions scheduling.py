import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation

my_problem = SimProblem()

resource = my_problem.add_place("resource")
resource.put(1)
resource.put(2)

schedule_time = my_problem.add_place("schedule_time")
schedule_time.put(5, 5)

arrived = prototype.BPMNFlow(my_problem, "arrived")
scheduled = prototype.BPMNFlow(my_problem, "scheduled")
completed = prototype.BPMNFlow(my_problem, "completed")

prototype.BPMNStartEvent(my_problem, [], [arrived], "arrive", lambda: random.expovariate(1))
prototype.BPMNTask(my_problem, [scheduled, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=0.75)])
prototype.BPMNEndEvent(my_problem, [completed], [], name="done")

def fifo_scheduler(_, customers):
    schedule = []
    for customer in customers:
        schedule.append(customer)
    return [[], schedule]
my_problem.add_transition([schedule_time, arrived.queue], [arrived.queue, scheduled.queue], fifo_scheduler)

vis = Visualisation(my_problem, "./temp/scheduler_layout.txt")
vis.show()
vis.save_layout("./temp/scheduler_layout.txt")