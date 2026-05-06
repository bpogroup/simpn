from simpn.simulator import SimProblem, SimToken, SimTokenValue, SimVar
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter
import simpn.prototypes as prototype
from simpn.visualisation.base import Visualisation


"""
Simulates the datastore functionality from the ER paper.

Example is:
- two types of patients T1, T2.
- two doctors D1, D2 with names.
- Patients arrive according to an exponential distribution with mean 5 minutes (12 per hour). They are 50/50 T1/T2.
- It takes on average 8 minutes to treat a patient (we can treat 7.5 per hour per resource = 15 per hour).
- Different doctor/ patient combinations have different treatment times. (D1, T1) is 6 minutes, (D1, T2) is 9 minutes, (D2, T1) is 10 minutes, (D2, T2) is 7 minutes.
"""


# Instantiate a simulation problem.
hospital = SimProblem()

# Define queues and other 'places' in the process.
waiting = prototype.BPMNFlow(hospital, "waiting")
done = prototype.BPMNFlow(hospital, "done")

# Define resources and resource data
doctors = prototype.BPMNLane(hospital, "doctor")
doctor_data = prototype.DataStore(hospital, "doctor_data")
doctors.put("D1")
doctor_data.update_data("D1", "Dr. Smith")
doctors.put("D2")
doctor_data.update_data("D2", "Dr. Johnson")

# Define patient data
patient_data = prototype.DataStore(hospital, "patient_data")

# Define start event with patient type data
def arrival_time():
  return exp(12/60)

def arrival_behavior(id):
  patient_type = "T1" if uniform(0, 1) < 0.5 else "T2"
  patient_data.update_data(id, patient_type)
  return SimToken(id)

prototype.BPMNStartEvent(hospital, [], [waiting], "arrival", arrival_time, arrival_behavior)

def treat_behavior(patient, doctor):
  patient_type = patient_data.read_data(patient)[1]
  if (doctor, patient_type) == ("D1", "T1"):
    return [SimToken((patient, doctor), delay=uniform(4, 8))]
  elif (doctor, patient_type) == ("D1", "T2"):
    return [SimToken((patient, doctor), delay=uniform(7, 11))]
  elif (doctor, patient_type) == ("D2", "T1"):
    return [SimToken((patient, doctor), delay=uniform(8, 12))]
  elif (doctor, patient_type) == ("D2", "T2"):
    return [SimToken((patient, doctor), delay=uniform(5, 9))]
  raise ValueError("Invalid doctor/ patient type combination. This should not happen if the model is correct.")

prototype.BPMNTask(hospital, [waiting, doctors], [done, doctors], "treat", treat_behavior)

prototype.BPMNEndEvent(hospital, [done], [], "complete")

# Simulate with visualization
v = Visualisation(hospital)
v.show()

