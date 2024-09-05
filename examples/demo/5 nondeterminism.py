from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

bank = SimProblem()

resources = bank.add_place("employees")
customers = bank.add_place("customers")
busy = bank.add_place("busy")
completed = bank.add_place("completed")

bank.add_transition([customers, resources], [busy], lambda c, r: [SimToken((c, r), delay=0.75 if r[-1]==c[-1] else 1.25)], "start_processing")
bank.add_transition([busy], [completed, resources], lambda b: [SimToken(b[0]), SimToken(b[1])], "end_processing")

resources.put("type 2")
resources.put("type 1")
for i in range(4):
    customers.put("type " + str(i%2+1))

Vis = Visualisation(bank, "./temp/nondeterminism_layout.txt")
Vis.show()
Vis.save_layout("./temp/nondeterminism_layout.txt")

# In this case, we can add a simple guard to ensure that the customer is processed by the right employee.
# However, if the relation is much more complicated, or even depends on the state of the system,
# that becomes infeasible.
# As an example, consider 