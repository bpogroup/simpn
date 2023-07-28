from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, end_event

shop = SimProblem()

to_deferred_choice = shop.add_var("to_deferred_choice")
to_scan_groceries = shop.add_var("to_scan_groceries")
to_leave = shop.add_var("to_leave")
cassier = shop.add_var("cassier")
left = shop.add_var("left")
to_remove = shop.add_var("to_remove")
done = shop.add_var("done")

cassier.put("r1")

def interarrival_time():
  return exp(1/10)
start_event(shop, [], [to_deferred_choice], "customer_arrived", interarrival_time)


shop.add_event([to_deferred_choice], [to_scan_groceries, to_leave], lambda c: [SimToken(c), SimToken(c, 15)], "deferred_choice")

shop.add_event([to_scan_groceries, to_leave], [left], lambda c, l: [SimToken(c)], "leave", guard=lambda c1, c2: c1==c2)

end_event(shop, [left], [], "left")


def start_scan_groceries(c, r):
  return [SimToken((c, r), exp(1/9))]
task(shop, [to_scan_groceries, cassier], [to_remove, cassier], "scan_groceries", start_scan_groceries)


def remove(c, r):
  print("removed", c)
  return [SimToken(c)]
shop.add_event([to_remove, to_leave], [done], remove, guard=lambda c1, c2: c1==c2)


end_event(shop, [done], [], "done")

reporter = EventLogReporter("./temp/simulation_deferred_choice.csv")
shop.simulate(24*60, reporter)
reporter.close()
