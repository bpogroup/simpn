from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import Replicator
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
waiting = shop.add_var("waiting")
waiting2 = shop.add_var("waiting2")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("c1")
cassier.put("c2")

# Define events.
prototype.BPMNStartEvent(shop, [], [waiting], "arrive", lambda: exp(1/10))

prototype.BPMNTask(shop, [waiting, cassier], [waiting2, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/8))])

prototype.BPMNTask(shop, [waiting2, cassier], [done, cassier], "bag_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/8))])

prototype.BPMNEndEvent(shop, [done], [], "complete")

replicator = Replicator(shop, duration=1000, warmup=100, nr_replications=10)
results = replicator.run()
print(results)