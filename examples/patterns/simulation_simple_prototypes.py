from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import start_event, task, end_event

shop = SimProblem()

to_scan_groceries = shop.add_var("to_scan_groceries")
done = shop.add_var("done")

cassier = shop.add_var("cassier")
cassier.put("r1")


start_event(shop, [], [to_scan_groceries], "start", lambda: exp(1/10))

task(shop, [to_scan_groceries, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), exp(1/9))])

end_event(shop, [done], [], "complete")

reporter = EventLogReporter("./temp/simulation_simple_prototypes.csv")
shop.simulate(24*60, reporter)
reporter.close()
