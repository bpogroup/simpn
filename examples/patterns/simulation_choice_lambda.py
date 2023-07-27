from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, basic_event

shop = SimProblem()

to_scan = shop.add_var("to_scan")
to_choice = shop.add_var("to_choice")
to_atm = shop.add_var("to_atm")
done = shop.add_var("done")

cashier = shop.add_var("cashier")
atm = shop.add_var("atm")

cashier.put("r1")
atm.put("a1")

task(shop, [to_scan, cashier], [to_choice, cashier], "scan", lambda c, r: [SimToken((c, r), exp(1/9))])

basic_event(shop, [to_choice], [to_atm], "choose", lambda c: [SimToken((c[0], uniform(1,100)))])

task(shop, [to_atm, atm], [done, atm], "atm", lambda c, r: [SimToken((c, r), exp(1/9))], guard=lambda c, r: c[1] < 25)

start_event(shop, [], [to_scan], "arrive", lambda: exp(1/10))

reporter = EventLogReporter("./temp/simulation_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()

