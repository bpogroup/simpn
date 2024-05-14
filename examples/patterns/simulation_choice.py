from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue")
to_choose = shop.add_var("to choose")
atm_queue = shop.add_var("atm queue")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

# Define events.
prototype.BPMNTask(shop, [scan_queue, cassier], [to_choose, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

def choose(c):
    percentage = uniform(1,100)
    if percentage <= 25:
        return [SimToken(c), None]
    else:
        return [None, SimToken(c)]
shop.add_event([to_choose], [atm_queue, done], choose)

prototype.BPMNTask(shop, [atm_queue, atm], [done, atm], "use_atm", lambda c, r: [SimToken((c, r), delay=exp(1/9))])

prototype.BPMNStartEvent(shop, [], [scan_queue], "arrive", lambda: exp(1/10))

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()