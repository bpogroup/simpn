"""
A module to create some dummy problems for testing.
"""

from simpn.simulator import SimProblem, SimToken, SimTokenValue
from simpn.helpers import Place, Transition, BPMN


def create_dummy_pn():
    from random import uniform

    problem = SimProblem()

    class Start(Place):
        model = problem
        name = "start"
        amount = 5

    class Resource(Place):
        model = problem
        name = "resource"
        amount = 1

    class Action(Transition):
        model = problem
        name = "Task One"
        incoming = ["start", "resource"]
        outgoing = ["end", "resource"]

        def behaviour(c, r):
            return [SimToken(c, delay=1), SimToken(r, delay=uniform(1, 5))]

    return problem


def create_dummy_bpmn(structured=False):
    from random import uniform, choice

    problem = SimProblem()
    instance_types = ["gold", "silver", "bronze"]

    class Start(BPMN):
        type = "start"
        model = problem
        name = "issue created"
        outgoing = ["issue"]

        def interarrival_time():
            return 0.2

        def behaviour(id):
            if structured:
                return SimToken(SimTokenValue(id, type=choice(instance_types)))
            else:
                return SimToken((id))

    class Employee(BPMN):
        type = "resource-pool"
        model = problem
        name = "employee"
        amount = 2

    problem.var("employee").visualize_edges = False

    class ConsiderIssue(BPMN):
        type = "task"
        model = problem
        name = "Consider Issue"
        incoming = ["issue", "employee"]
        outgoing = ["considered", "employee"]

        def behaviour(c, r):
            return [SimToken((c, r), delay=0.2)]

    class ChoiceSplit(BPMN):
        type = "gat-ex-split"
        model = problem
        name = "Hard or Easy?"
        incoming = ["considered"]
        outgoing = ["hard issue", "easy issue"]

        def choice(c):
            pick = uniform(0, 100)

            if pick <= 50:
                return [SimToken(c), None]
            else:
                return [None, SimToken(c)]

    class HandleIssue(BPMN):
        type = "task"
        model = problem
        name = "Handle Issue"
        incoming = ["easy issue", "employee"]
        outgoing = ["e-solved", "employee"]

        def behaviour(c, r):
            return [SimToken((c, r), delay=0.2)]

    class ComplexParallel(BPMN):
        type = "gat-para-split"
        model = problem
        name = "parallel-split"
        incoming = ["hard issue"]
        outgoing = ["h-t1", "h-t2"]

    class ComplexReport(BPMN):
        type = "task"
        model = problem
        name = "Create Report"
        incoming = ["h-t1", "employee"]
        outgoing = ["para-join-1", "employee"]

        def behaviour(c, r):
            return [SimToken((c, r), delay=uniform(0.5, 2))]

    class ComplexOffer(BPMN):
        type = "task"
        model = problem
        name = "Offer Counter"
        incoming = ["h-t2", "employee"]
        outgoing = ["para-join-2", "employee"]

        def behaviour(c, r):
            return [SimToken((c, r), delay=uniform(0.25, 1))]

    class ComplexParallelJoin(BPMN):
        type = "gat-para-join"
        model = problem
        name = "parallel-join"
        incoming = ["para-join-1", "para-join-2"]
        outgoing = ["h-solved"]

        def behaviour(l, r):
            return [
                SimToken(
                    l,
                )
            ]

    class ChoiceJoin(BPMN):
        type = "gat-ex-join"
        model = problem
        name = "Choice-Join"
        incoming = ["e-solved", "h-solved"]
        outgoing = ["close"]

    class CloseIssue(BPMN):
        type = "task"
        model = problem
        name = "Close Issue"
        incoming = ["close", "employee"]
        outgoing = ["closed", "employee"]

        def behaviour(c, r):
            return [SimToken((c, r), delay=uniform(0.25, 0.75))]

    class IssueHandled(BPMN):
        type = "end"
        model = problem
        name = "Issue Handled"
        incoming = ["closed"]

    return problem


def create_linear_process(structured: bool = False):
    from random import uniform, choice

    problem = SimProblem()
    instance_types = ["gold", "silver", "bronze"]

    class Start(BPMN):
        type = "start"
        model = problem
        name = "issue created"
        outgoing = ["issue"]

        def interarrival_time():
            return 0.1

        def behaviour(id):
            if structured:
                return SimToken(SimTokenValue(id, type=choice(instance_types)))
            else:
                return SimToken((id))

    class Employees(BPMN):
        type = "resource-pool"
        model = problem
        name = "employees"
        amount = 5

    class One(BPMN):
        type = "task"
        model = problem
        name = "One"
        incoming = ["issue", "employees"]
        outgoing = ["one", "employees"]

        def behaviour(tok, res):
            return [SimToken((tok, res), delay=uniform(0.25, 0.5))]

    class Two(BPMN):
        type = "task"
        model = problem
        name = "Two"
        incoming = ["one", "employees"]
        outgoing = ["two", "employees"]

        def behaviour(tok, res):
            return [SimToken((tok, res), delay=uniform(0.25, 0.5))]

    class End(BPMN):
        type = "end"
        model = problem
        name = "Finished"
        incoming = ["ending"]

    class Three(BPMN):
        type = "task"
        model = problem
        name = "Three"
        incoming = ["two", "employees"]
        outgoing = ["ending", "employees"]

        def behaviour(tok, res):
            return [SimToken((tok, res), delay=uniform(0.25, 0.5))]

    return problem


if __name__ == "__main__":
    from simpn.visualisation import Visualisation
    from simpn.priorities import NearestToCompletionPriority

    problem = create_linear_process()
    problem.set_binding_priority(NearestToCompletionPriority())
    vis = Visualisation(problem)

    vis.show()
