import random
from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation

def binding_priority(bindings):
    print(bindings)
    return bindings[0]

production_line = SimProblem(binding_priority = binding_priority)

# Define the variables that make up the state-space of the system
arrival = production_line.add_var("arrival")
queue_1 = production_line.add_var("q1", priority=lambda token: -token.value["value"])
resource = production_line.add_var("r1")
#finished = production_line.add_var("finished")

# Define the events that can change the state-space of the system
def job_arrival(arrival):
    # Generate a new arrival with uniform value distribution
    random_value = random.randint(100, 1000)
    job = arrival["job"]+1
    new_arrival = {"job": job, "value": random_value}

    # Increased arrival delay to be closer to processing time
    return [SimToken(new_arrival, delay=5.0), SimToken(arrival, delay=5.0)]

def job_handling_guard(q, r):
    a_queue = arrival.queue.marking[0].value
    q_queue = queue_1.queue.marking[0].value
    enabled_q_queue = [token for token in q_queue if token.time <= production_line.clock]

    value_a = a_queue[0].value["value"]
    
    value_q = max([token.value["value"] for token in q_queue])

    if len(enabled_q_queue)>0:
        enabled_value_q = max([token.value["value"] for token in enabled_q_queue])
    else:
        enabled_value_q = 0
    print(f"value_a: {value_a}, enabled_value_q: {enabled_value_q}, value_q: {value_q}")
    print(value_a < 1.5* enabled_value_q and value_q==enabled_value_q)
    return value_a < 1.5* enabled_value_q and value_q==enabled_value_q

production_line.add_event([arrival], [arrival, queue_1], job_arrival, name="job_arrival")
production_line.add_event([queue_1, resource], [resource], 
                          behavior= lambda q, r: [SimToken(r, delay=7)],
                          guard= job_handling_guard,
                          name="job_handling")

# Describe the initial state of the system
arrival.put({"job": 5, "value": 804}, time=20)
resource.put({"worker_id": 1})
queue_1.put({'job':3, 'value': 932}, time=15)
queue_1.put({'job':2, 'value': 522}, time=10)
queue_1.put({'job':4, 'value': 253}, time=20)
queue_1.put({'job':1, 'value': 100}, time=5)
production_line.clock = 15

# Visualise the simulation problem.
v = Visualisation(production_line)
v.show()
