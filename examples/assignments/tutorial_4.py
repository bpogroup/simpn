import matplotlib.pyplot as plt 
from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import WarmupReporter, ProcessReporter
import simpn.prototypes as prototype

# Instantiate a simulation problem.
agency = SimProblem()

# Define queues and other 'places' in the process.
waiting = agency.add_var("waiting")
done = agency.add_var("done")

# Define resources.
employee = agency.add_var("employee")
employee.put("e1")
employee.put("e2")

# Define events.
prototype.BPMNStartEvent(agency, [], [waiting], "arrive", lambda: exp(7)*60)

prototype.BPMNTask(agency, [waiting, employee], [done, employee], "answer_call", lambda c, r: [SimToken((c, r), delay=uniform(10, 15))])

prototype.BPMNEndEvent(agency, [done], [], "complete")

# Store the initial state of the simulator.
agency.store_checkpoint("initial state")

NR_REPLICATIONS = 20
SIMULATION_DURATION = 40*60
WARMUP_TIME = 20*60

# Simulate once with a warmup reporter.
reporter = WarmupReporter()
agency.simulate(SIMULATION_DURATION, reporter)

plt.plot(reporter.times, reporter.average_cycle_times, color="blue")
plt.xlabel("arrival time (min)")
plt.xticks(range(0, SIMULATION_DURATION, 10*60))
plt.ylabel("cycle time (min)")
plt.show()

# Reset the simulator to the initial state.
agency.restore_checkpoint("initial state")

# Simulate with and without warmup time.
reporter_w = ProcessReporter(WARMUP_TIME)
reporter_wo = ProcessReporter()

agency.simulate(SIMULATION_DURATION, [reporter_w, reporter_wo])

print("With warmup:")
reporter_w.print_result()
print("Without warmup:")
reporter_wo.print_result()

# Reset the simulator to the initial state.
agency.restore_checkpoint("initial state")

# Simulate with replications and warmup time.
average_cycle_times = []
for _ in range(NR_REPLICATIONS):
    reporter = ProcessReporter(WARMUP_TIME)
    agency.restore_checkpoint("initial state")
    agency.simulate(SIMULATION_DURATION, reporter)
    print("iteration", _)

    average_cycle_times.append(reporter.total_wait_time / reporter.nr_completed)

plt.boxplot(average_cycle_times)
plt.xticks([1], labels=["2 employees"])
plt.ylabel("average cycle time (min)")
plt.show()