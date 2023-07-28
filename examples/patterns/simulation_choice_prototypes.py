from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, choice

shop = SimProblem()

to_scan_groceries = shop.add_var("to_scan_groceries")
to_choose = shop.add_var("to_choose")
chosen = shop.add_var("chosen")
to_use_atm = shop.add_var("to_use_atm")
done = shop.add_var("done")

cassier = shop.add_var("cassier")
atm = shop.add_var("atm")

cassier.put("r1")
atm.put("a1")

def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_scan_groceries, cassier], [to_choose, cassier], "scan_groceries", start_scan_groceries)

def choose(c):
  return [SimToken((c[0], uniform(1,100)))]
choice(shop, [to_choose], [to_use_atm, done], "choose", choose, [lambda c: c[1] < 25, lambda c: c[1] >= 25])

def start_use_atm(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_use_atm, atm], [done, atm], "use_atm", start_use_atm)

def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_scan_groceries], "arrive", interarrival_time)

reporter = EventLogReporter("./temp/simulation_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()

