import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.visualisation import Visualisation


my_problem = SimProblem()

resource = my_problem.add_var("resource")
resource.put(1)
resource.put(2)

arrive2taskA = prototype.BPMNFlow(my_problem, "arrive->taskA")
taskA2choice = prototype.BPMNFlow(my_problem, "taskA->choice")
choice2taskB = prototype.BPMNFlow(my_problem, "choice->taskB")
choice2taskC = prototype.BPMNFlow(my_problem, "choice->taskC")
taskB2join = prototype.BPMNFlow(my_problem, "taskB->join")
taskC2join = prototype.BPMNFlow(my_problem, "taskC->join")
join2end = prototype.BPMNFlow(my_problem, "join->end")

prototype.BPMNStartEvent(my_problem, [], [arrive2taskA], "arrive", lambda: random.expovariate(1))
prototype.BPMNTask(my_problem, [arrive2taskA, resource], [taskA2choice, resource], "Task A", lambda a, r: [SimToken((a, r), delay=0.75)])
def choice_func(case):
    # Simulate a 50% chance of going to task B or task C
    if random.random() < 0.5:
        return [SimToken(case), None]
    else:
        return [None, SimToken(case)]
prototype.BPMNExclusiveSplitGateway(my_problem, [taskA2choice], [choice2taskB, choice2taskC], "Choice", choice_func)
prototype.BPMNTask(my_problem, [choice2taskB, resource], [taskB2join, resource], "Task B", lambda a, r: [SimToken((a, r), delay=0.5)])
prototype.BPMNTask(my_problem, [choice2taskC, resource], [taskC2join, resource], "Task C", lambda a, r: [SimToken((a, r), delay=0.5)])
prototype.BPMNExclusiveJoinGateway(my_problem, [taskB2join, taskC2join], [join2end], "Join")
prototype.BPMNEndEvent(my_problem, [join2end], [], "End")

vis = Visualisation(my_problem, "./temp/bpmn_layout.txt")
vis.show()
vis.save_layout("./temp/bpmn_layout.txt")