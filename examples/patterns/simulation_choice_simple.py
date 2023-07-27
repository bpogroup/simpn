from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event

shop = SimProblem()

to_scan = shop.add_var("to_scan")
to_choice = shop.add_var("to_choice")
to_atm = shop.add_var("to_atm")
done = shop.add_var("done")

cashier = shop.add_var("cashier")
atm = shop.add_var("atm")

cashier.put("r1")
atm.put("a1")

def start_scan(c, r):
  return [SimToken((c, r), exp(1/9))]
scan = task(shop, [to_scan, cashier], [to_choice, cashier], "scan", start_scan)

def choose(c):
  return [SimToken((c[0], uniform(1,100)))]
shop.add_event([to_choice], [to_atm], choose)

def start_atm(c, r):
  return [SimToken((c, r), exp(1/9))]
def guard_atm(c, r):
  return c[1] < 25
atm = task(shop, [to_atm, atm], [done, atm], "atm", start_atm, guard=guard_atm)

def interarrival_time():
  return exp(1/10)
arrive = start_event(shop, [], [to_scan], "arrive", interarrival_time)

reporter = EventLogReporter("./temp/simulation_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()

