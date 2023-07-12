import random
from simpn.simulator import SimProblem
import simpn.prototypes as prototype
from simpn.reporters import ProcessReporter, SimpleReporter

repairs_workshop = SimProblem()

arrived = repairs_workshop.add_svar("arrived")
inspected = repairs_workshop.add_svar("inspected")
ordered = repairs_workshop.add_svar("ordered")
received = repairs_workshop.add_svar("received")
repaired = repairs_workshop.add_svar("repaired")
completed = repairs_workshop.add_svar("completed")

engineers = repairs_workshop.add_svar("engineers")
engineers.put("Engineer 1")
engineers.put("Engineer 2")
pos = repairs_workshop.add_svar("purchase officers")
pos.put("PO 1")
pos.put("PO 2")

arrive = repairs_workshop.add_stransition([], [arrived], lambda: "Case", name="arrive", delay=lambda: [random.expovariate(2)], prototype=prototype.start_event)
inspect = repairs_workshop.add_stransition([arrived, engineers], [inspected, engineers], None, name="inspect", delay=lambda c, r: [random.uniform(0.3, 0.7)], prototype=prototype.task)
order = repairs_workshop.add_stransition([inspected, pos], [ordered, pos], None, name="order", delay=lambda c, r: [random.uniform(0.3, 0.7)], prototype=prototype.task)
await_parts = repairs_workshop.add_stransition([ordered], [received], None, name="await parts", delay=lambda c: [random.uniform(0, 10)], prototype=prototype.intermediate_event)
repair = repairs_workshop.add_stransition([received, engineers], [repaired, engineers], None, name="repair", delay=lambda c, r: [random.uniform(0.3, 0.7)], prototype=prototype.task)
complete = repairs_workshop.add_stransition([repaired], [completed], None, name="complete", prototype=prototype.end_event)

reporter = ProcessReporter()
sim_run = repairs_workshop.simulate(5000, reporter=reporter)
reporter.print_result()
