from simpn.simulator import SimProblem
from simpn.simulator import SimToken
from random import expovariate as exp, uniform as uniform
from simpn.reporters import EventLogReporter
from simpn.prototypes import task, start_event, end_event

shop = SimProblem()

to_choose = shop.add_var("to_choose")
cassier_1_queue = shop.add_var("cassier_1_queue")
cassier_2_queue = shop.add_var("cassier_2_queue")
done = shop.add_var("done")

cassier_1 = shop.add_var("cassier_1")
cassier_2 = shop.add_var("cassier_2")

cassier_1.put("c1")
cassier_2.put("c2")

cassier_1_queue_count = shop.var("cassier_1_queue.count")
cassier_2_queue_count = shop.var("cassier_2_queue.count")

shop.add_event([to_choose, cassier_1_queue_count, cassier_2_queue_count], [cassier_1_queue], lambda x, c1c, c2c: [SimToken(x)], guard = lambda x, c1c, c2c: c1c < c2c, name="choose cassier 1")
shop.add_event([to_choose, cassier_1_queue_count, cassier_2_queue_count], [cassier_2_queue], lambda x, c1c, c2c: [SimToken(x)], guard = lambda x, c1c, c2c: c1c >= c2c, name="choose cassier 2")

task(shop, [cassier_1_queue, cassier_1], [done, cassier_1], "scan_groceries_1", lambda c, r: [SimToken((c, r), exp(1/9))])
task(shop, [cassier_2_queue, cassier_2], [done, cassier_2], "scan_groceries_2", lambda c, r: [SimToken((c, r), exp(1/9))])

def interarrival_time():
  return exp(1/6)
start_event(shop, [], [to_choose], "arrive", interarrival_time)

end_event(shop, [done], [], "leave")

reporter = EventLogReporter("./temp/simulation_multiple_queues.csv")
shop.simulate(24*60, reporter)
reporter.close()

