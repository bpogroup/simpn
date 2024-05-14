from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
to_choose = shop.add_var("to choose")
waiting_1 = shop.add_var("cassier 1 queue")
waiting_2 = shop.add_var("cassier 2 queue")
done = shop.add_var("done")

# Define resources.
cassier_1 = shop.add_var("cassier 1")
cassier_2 = shop.add_var("cassier 2")

cassier_1.put("c1")
cassier_2.put("c2")

# Define events.
prototype.BPMNStartEvent(shop, [], [to_choose], "arrive", lambda: exp(1/6))

def choose(c, c1_queue, c2_queue):
  if len(c1_queue) < len(c2_queue):
    c1_queue.append(SimToken(c))
  else:
    c2_queue.append(SimToken(c))
  return [c1_queue, c2_queue]
shop.add_event([to_choose, waiting_1.queue, waiting_2.queue], [waiting_1.queue, waiting_2.queue], choose)

prototype.BPMNTask(shop, [waiting_1, cassier_1], [done, cassier_1], "scan_groceries_1", lambda c, r: [SimToken((c, r), delay=exp(1/9))])
prototype.BPMNTask(shop, [waiting_2, cassier_2], [done, cassier_2], "scan_groceries_2", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNEndEvent(shop, [done], [], "leave")

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_multiple_queues.csv")
shop.simulate(24*60, reporter)
reporter.close()

