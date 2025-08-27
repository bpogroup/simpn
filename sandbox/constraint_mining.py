from simpn.simulator import SimProblem, SimToken
from simpn.visualisation import Visualisation
import random

problem = SimProblem()

v_arrival = problem.add_var("arrival")
v_queue = problem.add_var("queue")
v_resources = problem.add_var("resources")
v_ready = problem.add_var("ready")

v_arrival.put((3, 855), time = 10)
v_queue.put((1, 100))
v_queue.put((2, 118), time = 5)
v_resources.put("r1")

def pre_process(job):
    job_nr, value = job
    return [SimToken((job_nr+1, random.randint(100, 1000)), delay=5), SimToken(job, delay=5)]
problem.add_event([v_arrival], [v_arrival, v_queue], pre_process)

def handle(job, resource):
    return [SimToken(job, delay=7), SimToken(resource, delay=7)]
problem.add_event([v_queue, v_resources], [v_ready, v_resources], handle)

v = Visualisation(problem, layout_algorithm="sugiyama", grid_spacing=100, node_spacing=200, layout_file="./temp/layout_constraint.txt")
v.show()
v.save_layout("./temp/layout_constraint.txt")
