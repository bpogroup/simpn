from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, end_event

shop = SimProblem()

to_split = shop.add_var("to_split")
to_scan_groceries = shop.add_var("to_scan_groceries")
to_use_atm = shop.add_var("to_use_atm")
from_scan_groceries = shop.add_var("from_scan_groceries")
from_use_atm = shop.add_var("from_use_atm")
to_done = shop.add_var("to_done")

cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_split], "arrive", interarrival_time)


shop.add_event([to_split], [to_scan_groceries, to_use_atm], lambda c: [SimToken(c), SimToken(c)], name="split")


def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_scan_groceries, cassier], [from_scan_groceries, cassier], "scan_groceries", start_scan_groceries)

def start_use_atm(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_use_atm, atm], [from_use_atm, atm], "use_atm", start_use_atm)


shop.add_event([from_scan_groceries, from_use_atm], [to_done], lambda c1, c2: [SimToken(c1)], name="join")


end_event(shop, [to_done], [], "done")

reporter = EventLogReporter("./temp/simulation_parallellism.csv")
shop.simulate(24*60, reporter)
reporter.close()

