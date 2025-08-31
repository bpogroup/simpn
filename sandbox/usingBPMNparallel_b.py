import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.helpers import BPMN
from simpn.visualisation import Visualisation


my_problem = SimProblem()

# define resources and flows
class Resources(BPMN):
    type="resource-pool"
    model = my_problem
    amount = 2
    name = "resources"

class Starting(BPMN):
    type="flow"
    name="start_to_and_split"
    model = my_problem

class SplitA(BPMN):
    type="flow"
    name="and_split_to_a"
    model = my_problem

class SplitB(BPMN):
    type="flow"
    name="and_split_to_b"
    model = my_problem

class JoinA(BPMN):
    type="flow"
    name="a_to_join"
    model = my_problem

class JoinB(BPMN):
    type="flow"
    name="b_to_join"
    model = my_problem

class EndingFlow(BPMN):
    type="flow"
    name="join_to_end"
    model = my_problem

# define helper classes to represent the process
class Start(BPMN):
    type="start"
    model=my_problem
    name="arrive"
    outgoing=["start_to_and_split"]

    def interarrival_time():
        return random.expovariate(1)

class ParallelSplit(BPMN):
    type="gat-para-split"
    model=my_problem
    incoming=["start_to_and_split"]
    outgoing=["and_split_to_a", "and_split_to_b"]
    name="and split"

class TaskA(BPMN):
    type="task"
    model=my_problem
    incoming=["and_split_to_a", "resources"]
    outgoing=["a_to_join", "resources"]
    name="Task A"

    def behaviour(c, r):
        return [SimToken((c, r), delay=1)]
    
class TaskB(BPMN):
    type="task"
    model=my_problem
    incoming=["and_split_to_b", "resources"]
    outgoing=["b_to_join", "resources"]
    name="Task B"

    def behaviour(c, r):
        return [SimToken((c, r), delay=2)]
    
class ParallelJoin(BPMN):
    type="gat-para-join"
    model=my_problem
    incoming=["a_to_join", "b_to_join"]
    outgoing=["join_to_end"]
    name="and join"

class End(BPMN):
    type="end"
    model=my_problem
    incoming=["join_to_end"]
    name="end"

# prototype.BPMNParallelJoinGateway(my_problem, [a_to_join, b_to_join], [join_to_end], "and join")
# prototype.BPMNEndEvent(my_problem, [join_to_end], [], name="end")

vis = Visualisation(my_problem, "./temp/parallel_layout.txt")
vis.show()
vis.save_layout("./temp/parallel_layout.txt")