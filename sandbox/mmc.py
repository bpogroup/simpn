import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.reporters import ProcessReporter
import math

LAMBDA = 30
MU = 60/4
C = 3
rho = LAMBDA/(C * MU)
PIW = ((C*rho)**C)/math.factorial(C) / ((1-rho) * sum([((C*rho)**n)/math.factorial(n) for n in range(0, C)]) + ((C*rho)**C)/math.factorial(C))
EB = 1/MU
EB2 = 2/(MU**2)
ER = EB2/(2*EB)
EW = PIW * (1/(1-rho)) * ER/C

print("EB", EB, 4/6)
print("rho", rho, 2/3)
print("PIW", PIW, 4/9)
print("EB2", EB2, 2/225)
print("ER", ER, 1/15)
print("EW", EW, 4/135)
print()
print(round(EW, 3), "should be similar to Avg. waiting time below.")
print(round(EB, 3), "should be similar to Avg. processing time below.")
print()

my_problem = SimProblem()

arrived = my_problem.add_var("arrived")
resource = my_problem.add_var("resource")
completed = my_problem.add_var("completed")

prototype.BPMNStartEvent(my_problem, [], [arrived], "arrive", lambda: random.expovariate(LAMBDA))
prototype.BPMNTask(my_problem, [arrived, resource], [completed, resource], "task", lambda a, r: [SimToken((a, r), delay=random.expovariate(MU))])
prototype.BPMNEndEvent(my_problem, [completed], [], name="done")

for i in range(C):
    resource.put(i)

reporter = ProcessReporter()
my_problem.simulate(1000, reporter)
reporter.print_result()
