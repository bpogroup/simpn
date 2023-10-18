from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import EventLogReporter
from simpn.prototypes import start_event, task, end_event, intermediate_event

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
to_check_queue = shop.add_var("to check queue")
queue = shop.add_var("queue")
queue_length = shop.var("queue.count")
done = shop.add_var("done")
to_leave = shop.add_var("to leave")

# Define resources.
cassier = shop.add_var("cassier")
cassier.put("r1")

# Define events.
start_event(shop, [], [to_check_queue], "start", lambda: exp(1/9))

# Check the queue length
def check_queue_length(c, ql):
    if ql < 5: # If it is less than 5 customers in the queue, the customer goes into the queue
        return [SimToken(c), None]
    else: # If it is more than 5 customers in the queue, the customer leaves
        return [None, SimToken(c)]
shop.add_event([to_check_queue, queue_length], [queue, to_leave], check_queue_length)

task(shop, [queue, cassier], [done, cassier], "scan_groceries", lambda c, r: [SimToken((c, r), exp(1/9))])

end_event(shop, [done], [], "complete")
end_event(shop, [to_leave], [], "leave")


# Run the simulation.
reporter = EventLogReporter("./temp/simulation_limited_queue_space.csv")
shop.simulate(24*60, reporter)
reporter.close()
