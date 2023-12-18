import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype


class SequenceReporter:
    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        if event.get_id().endswith("<task:start>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            print(case_id)


my_problem = SimProblem()

arrived = my_problem.add_var("arrived")
resource = my_problem.add_var("resource")
completed = my_problem.add_var("completed")

prototype.start_event(my_problem, [], [arrived], "arrive", lambda: random.expovariate(1), behavior=lambda: [SimToken(random.randint(1, 2))])
prototype.task(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=0.75)])  # unordered execution
# prototype.task_fifo(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=0.75)], guard=lambda c, r: c[1] == r)  # ordered execution with guard
# prototype.task_fifo(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=0.75)])  # ordered execution
prototype.end_event(my_problem, [completed], [], name="done")

resource.put(1)


my_problem.simulate(40, SequenceReporter())
