from simpn.simulator import SimProblem
from simpn.visualisation import Visualisation
from random import expovariate as exp
from simpn.prototypes_queueing import QueueingGenerator, QueueingQueue, QueueingServer, QueueingSink, QueueingChoice

# Instantiate a simulation problem.
queueing_network = SimProblem()

# Model the storage elements.
q1 = QueueingQueue(queueing_network, "q1")
q2 = QueueingQueue(queueing_network, "q2")
q3 = QueueingQueue(queueing_network, "q3")

pre_choice = queueing_network.add_var("pre_choice")

sink2 = QueueingSink(queueing_network, "sink2")
sink3 = QueueingSink(queueing_network, "sink3")

# Model the flow elements.
g1 = QueueingGenerator(queueing_network, [], [q1], "g1", lambda: exp(1/10))

s1 = QueueingServer(queueing_network, [q1], [pre_choice], "s1", lambda: exp(1/9))

choice = QueueingChoice(queueing_network, [pre_choice], [q2, q3], "choice", [50, 50])

s2 = QueueingServer(queueing_network, [q2], [sink2], "s2", lambda: exp(1/9))

s3 = QueueingServer(queueing_network, [q3], [sink3], "s3", lambda: exp(1/9))

# Visualise the simulation problem.
m = Visualisation(queueing_network)
m.show()