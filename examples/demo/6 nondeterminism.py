from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

shop = SimProblem()

resources = shop.add_place("resources")
customers = shop.add_place("customers")
busy = shop.add_place("busy")
completed = shop.add_place("completed")

shop.add_transition([customers, resources], [busy], lambda c, r: [SimToken((c, r), delay=0.75 if r=="cassier1" else 1.25)], "start_processing")
shop.add_transition([busy], [completed, resources], lambda b: [SimToken(b[0]), SimToken(b[1])], "end_processing")

resources.put("cassier1")
resources.put("cassier2")
for i in range(4):
    customers.put(f"c{i}")

Vis = Visualisation(shop, "./temp/nondeterminism_layout.txt")
Vis.show()
Vis.save_layout("./temp/nondeterminism_layout.txt")