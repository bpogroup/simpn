from simpn.simulator import SimProblem

# Instantiate a simulation problem.
shop = SimProblem()

# Define queues and other 'places' in the process.
arrival = shop.add_var("arrival")
waiting = shop.add_var("waiting")
busy = shop.add_var("busy")

arrival.put(1)

# Define resources.
resource = shop.add_var("resource")
resource.put("r1")

# Define events.
from simpn.simulator import SimToken
from random import expovariate as exp

def start(c, r):
  return [SimToken((c, r), delay=exp(1/0.8))]

shop.add_event([waiting, resource], [busy], start)

def complete(b):
  return [SimToken(b[1], delay=0)]

shop.add_event([busy], [resource], complete)

def arrive(a):
  return [SimToken(a+1, delay=exp(1)), SimToken(a)]

shop.add_event([arrival], [arrival, waiting], arrive)

# Run the simulation.
from simpn.reporters import Reporter

class TimesReporter(Reporter):
    
  def __init__(self):
    self.arrival_times = dict()
    self.start_times = dict()
    self.complete_times = dict()
    self.total_wait_time = 0
    self.total_proc_time = 0
    
  def callback(self, timed_binding):
      (binding, time, event) = timed_binding
      if event.get_id() == "arrive":
          customer_id = binding[0][1].value
          self.arrival_times[customer_id] = time
      elif event.get_id() == "start":
          customer_id = binding[0][1].value
          self.start_times[customer_id] = time
          self.total_wait_time += time - self.arrival_times[customer_id]          
      elif event.get_id() == "complete":
          customer_id = binding[0][1].value[0]
          self.complete_times[customer_id] = time
          self.total_proc_time += time - self.start_times[customer_id]

  def mean_waiting_time(self):
      return self.total_wait_time / len(self.start_times)

  def mean_processing_time(self):
      return self.total_proc_time / len(self.complete_times)
  
  def mean_cycle_time(self):
      return self.mean_waiting_time() + self.mean_processing_time()
  
my_reporter = TimesReporter()

shop.simulate(1000, my_reporter)

print(my_reporter.mean_cycle_time())
print(my_reporter.mean_waiting_time())
print(my_reporter.mean_processing_time())

