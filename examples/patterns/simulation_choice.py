from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event

shop = SimProblem()

to_scan = shop.add_var("to_scan")
to_choice = shop.add_var("to_choice")
chosen = shop.add_var("chosen")
to_atm = shop.add_var("to_atm")
done = shop.add_var("done")

cashier = shop.add_var("cashier")
atm = shop.add_var("atm")

cashier.put("r1")
atm.put("a1")

def start_scan(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_scan, cashier], [to_choice, cashier], "scan", start_scan)

def choose(c):
  return [SimToken((c[0], uniform(1,100)))]
shop.add_event([to_choice], [chosen], choose)

def pass_customer(c):
  return [SimToken(c)]

shop.add_event([chosen], [to_atm], pass_customer, name="choose_atm", guard=lambda c: c[1] < 25)
shop.add_event([chosen], [done], pass_customer, name="choose_home", guard=lambda c: c[1] >= 25)

def start_atm(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_atm, atm], [done, atm], "atm", start_atm)

def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_scan], "arrive", interarrival_time)

reporter = EventLogReporter("./temp/simulation_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()

