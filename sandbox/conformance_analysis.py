import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.reporters import EventLogReporter
from simpn.analysis import Conformance

def problem(probability_of_a):
    my_problem = SimProblem()

    resource = my_problem.add_var("resource")
    resource.put(1)
    resource.put(2)

    start_to_xor_split = prototype.BPMNFlow(my_problem, "start_to_xor_plit")
    xor_split_to_a = prototype.BPMNFlow(my_problem, "xor_split_to_a")
    xor_split_to_b = prototype.BPMNFlow(my_problem, "xor_split_to_b")
    a_to_join = prototype.BPMNFlow(my_problem, "a_to_join")
    b_to_join = prototype.BPMNFlow(my_problem, "b_to_join")
    join_to_end = prototype.BPMNFlow(my_problem, "join_to_end")

    def choice_behavior(c):
        if random.random() <= probability_of_a:
            return [SimToken(c), None]
        else:
            return [None, SimToken(c)]

    prototype.BPMNStartEvent(my_problem, [], [start_to_xor_split], "arrive", lambda: random.expovariate(1))
    prototype.BPMNExclusiveSplitGateway(my_problem, [start_to_xor_split], [xor_split_to_a, xor_split_to_b], "xor split", behavior=choice_behavior)
    prototype.BPMNTask(my_problem, [xor_split_to_a, resource], [a_to_join, resource], "task a", lambda a, r: [SimToken((a, r), delay=0.4)])
    prototype.BPMNTask(my_problem, [xor_split_to_b, resource], [b_to_join, resource], "task b", lambda a, r: [SimToken((a, r), delay=0.5)])
    prototype.BPMNExclusiveJoinGateway(my_problem, [a_to_join, b_to_join], [join_to_end], "xor join")
    prototype.BPMNEndEvent(my_problem, [join_to_end], [], name="end")

    return my_problem


# create problems
problem_50_50 = problem(0.5)
problem_75_25 = problem(0.75)
problem_0_100 = problem(0.0)

# create logs (and reset the problems to their initial state)
problem_50_50.store_checkpoint("initial_state")
problem_75_25.store_checkpoint("initial_state")
problem_0_100.store_checkpoint("initial_state")
problem_50_50.simulate(1000, EventLogReporter("./temp/problem_50_50.csv", separator=";"))
problem_75_25.simulate(1000, EventLogReporter("./temp/problem_75_25.csv", separator=";"))
problem_0_100.simulate(1000, EventLogReporter("./temp/problem_0_100.csv", separator=";"))
problem_50_50.restore_checkpoint("initial_state")
problem_75_25.restore_checkpoint("initial_state")
problem_0_100.restore_checkpoint("initial_state")

# do various conformance analyses
cc = Conformance(problem_50_50, "./temp/problem_50_50.csv", separator=";")
print("Conformance of 50_50 problem to 50_50 log:")
print(f"Fitness: {cc.calculate_fitness():.2f}")
print(f"Precision: {cc.calculate_precision():.2f}")

cc = Conformance(problem_0_100, "./temp/problem_50_50.csv", separator=";")
print("Conformance of 0_100 problem to 50_50 log:")
print(f"Fitness: {cc.calculate_fitness():.2f}")
print(f"Precision: {cc.calculate_precision():.2f}")

cc = Conformance(problem_0_100, "./temp/problem_75_25.csv", separator=";")
print("Conformance of 0_100 problem to 75_25 log:")
print(f"Fitness: {cc.calculate_fitness():.2f}")
print(f"Precision: {cc.calculate_precision():.2f}")

cc = Conformance(problem_75_25, "./temp/problem_0_100.csv", separator=";")
print("Conformance of 75_25 problem to 0_100 log:")
print(f"Fitness: {cc.calculate_fitness():.2f}")
print(f"Precision: {cc.calculate_precision():.2f}")
