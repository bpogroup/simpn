from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import start_event, task, end_event, intermediate_event

shop = SimProblem()

to_check_queue = shop.add_var("to_check_queue")
queue = shop.add_var("queue")
queue_length = shop.var("queue.count")
done = shop.add_var("done")
to_leave = shop.add_var("to_leave")

cassier = shop.add_var("cassier")
cassier.put("r1")


start_event(shop, [], [to_check_queue], "start", lambda: exp(1/9))

# Check the queue length
# If it is less than 5 customers in the queue, the customer goes into the queue
shop.add_event([to_check_queue, queue_length], [queue], lambda x, l: [SimToken(x)], guard=lambda x, l: l < 5, name="go_to_queue")
# If it is more than 5 customers in the queue, the customer leaves
shop.add_event([to_check_queue, queue_length], [to_leave], lambda x, l: [SimToken(x)], guard=lambda x, l: l >= 5, name="go_to_leave")

task(shop, [queue, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), exp(1/9))])

end_event(shop, [done], [], "complete")
end_event(shop, [to_leave], [], "leave")


reporter = EventLogReporter("./temp/simulation_limited_queue_space.csv")
shop.simulate(24*60, reporter)
reporter.close()
