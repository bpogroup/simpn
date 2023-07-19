import random
from simpn.simulator import SimProblem, SimToken
import simpn.prototypes as prototype
from simpn.reporters import ProcessReporter

repairs_workshop = SimProblem()

arrived = repairs_workshop.add_var("arrived")
inspected = repairs_workshop.add_var("inspected")
ordered = repairs_workshop.add_var("ordered")
received = repairs_workshop.add_var("received")
repaired = repairs_workshop.add_var("repaired")
completed = repairs_workshop.add_var("completed")

engineers = repairs_workshop.add_var("engineers")
engineers.put("Engineer 1")
engineers.put("Engineer 2")
pos = repairs_workshop.add_var("purchase officers")
pos.put("PO 1")
pos.put("PO 2")

arrive = prototype.start_event(repairs_workshop, [], [arrived], "arrive", lambda: random.expovariate(2))
inspect = prototype.task(repairs_workshop, [arrived, engineers], [inspected, engineers], "inspect", lambda c, r: [SimToken((c, r), random.uniform(0.3, 0.7))])
order = prototype.task(repairs_workshop, [inspected, pos], [ordered, pos], "order", lambda c, r: [SimToken((c, r), random.uniform(0.3, 0.7))])
await_parts = prototype.intermediate_event(repairs_workshop, [ordered], [received], "await parts", lambda c: [SimToken(c, random.uniform(0, 10))])
repair = prototype.task(repairs_workshop, [received, engineers], [repaired, engineers], "repair", lambda c, r: [SimToken((c, r), random.uniform(0.3, 0.7))])
complete = prototype.end_event(repairs_workshop, [repaired], [], "complete")

reporter = ProcessReporter()
sim_run = repairs_workshop.simulate(5000, reporter=reporter)
reporter.print_result()
