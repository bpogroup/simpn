from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
scan_queue = shop.add_var("scan queue")
to_choose = shop.add_var("to choose")
chosen = shop.add_var("chosen")
atm_queue = shop.add_var("atm queue")
done = shop.add_var("done")

# Define resources.
cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

# Define events.
task(shop, [scan_queue, cassier], [to_choose, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), exp(1/9))])

shop.add_event([to_choose], [chosen], lambda c: [SimToken((c[0], uniform(1,100)))], name="choose")
shop.add_event([chosen], [atm_queue], lambda c: [SimToken(c)], name="choose_use_atm", guard=lambda c: c[1] < 25)
shop.add_event([chosen], [done], lambda c: [SimToken(c)], name="choose_go_home", guard=lambda c: c[1] >= 25)

task(shop, [atm_queue, atm], [done, atm], "use_atm", lambda c, r: [SimToken((c, r), exp(1/9))])

start_event(shop, [], [scan_queue], "arrive", lambda: exp(1/10))

# Run the simulation.
reporter = EventLogReporter("./temp/simulation_choice_lambda.csv")
shop.simulate(24*60, reporter)
reporter.close()

# Explain that we can use lambda functions more broadly to make everything more compact

