from simpn.simulator import SimProblem

model = SimProblem()

S_arrival = model.add_var("S_arrival")
T_waiting = model.add_var("T_waiting")
R_idle = model.add_var("R_idle")
T_busy = model.add_var("T_busy")
E_waiting = model.add_var("E_waiting")

R_idle.put("r1")
S_arrival.put(1)

from simpn.simulator import SimToken
from random import expovariate as exp

def Tstart(c, r):
    return [SimToken((c, r), delay=exp(1/0.8))]

model.add_event([T_waiting, R_idle], [T_busy], Tstart)

def Tcomplete(b):
    return [SimToken(b[0]), SimToken(b[1])]

model.add_event([T_busy], [E_waiting, R_idle], Tcomplete)

def Sarrive(a):
    return [SimToken(a+1, delay=exp(1)), SimToken('c'+str(a))]

model.add_event([S_arrival], [S_arrival, T_waiting], Sarrive)

from simpn.reporters import SimpleReporter

model.simulate(2.5, SimpleReporter())