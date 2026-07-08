from simpn.simulator import DecProblem, SimToken
from random import expovariate as exp
from random import uniform
import simpn.prototypes as prototype
from simpn.visualisation.base import Visualisation


"""
Implements the case scheduling example from the ER paper.

Process is:
- arrival start event -> intermediate event: time for appointment -> bloodwork -> complete end event
- patients have an appointment_time attribute that is None initially.
- two lab_staff exist.
- Patients arrive according to an exponential distribution with mean 6 minutes (10 per hour).
- Patients wait for theit appointment time to arrive, then they are sent for bloodwork.
- It takes 5-15 minutes to perform bloodwork on a patient (we can treat 6 per hour per resource = 12 per hour).

Decision is:
- Decision moment: when a patient is waiting for 'time for appointment' and appointment_time is None
- Decision: assign an appointment time to the patient (between 0 and 60 minutes from now).
- Policy: this is just a simple example, so we assign an appointment time 1 minute from the current time. 
"""


# --------------------------
# PROCESS MODEL
# --------------------------

# Instantiate the problem.
hospital = DecProblem()

# Define queues and other 'places' in the process.
waiting_for_appointment = prototype.BPMNFlow(hospital, "waiting_for_appointment")
waiting_for_bloodwork = prototype.BPMNFlow(hospital, "waiting_for_bloodwork")
done = prototype.BPMNFlow(hospital, "done")

# Define resources and resource data
lab_staff = prototype.BPMNLane(hospital, "lab_staff")
lab_staff_data = prototype.DataStore(hospital, "lab_staff_data", str) # we only need to store the name of the lab staff, so we use a single string attribute
lab_staff.put("L1")
lab_staff_data.update_data("L1", "Lab Tech 1")
lab_staff.put("L2")
lab_staff_data.update_data("L2", "Lab Tech 2")

# Define patient data
patient_data = prototype.DataStore(hospital, "patient_data", has_appointment=bool, appointment_time=float) # we store whether the patient has an appointment and the appointment time (in minutes from now)

# Define start event with patient type data
def arrival_time():
  return exp(10/60)

def arrival_behavior(id):
  patient_data.update_data(id, has_appointment=False, appointment_time=0)
  return SimToken(id)

prototype.BPMNStartEvent(hospital, [], [waiting_for_appointment], "arrives", arrival_time, arrival_behavior)

# Define the intermediate event: time for appointment
def time_for_appointment_guard(patient_id):
    patient_info = patient_data.read_data(patient_id)
    return patient_info.has_appointment

prototype.BPMNIntermediateEvent(hospital, [waiting_for_appointment], [waiting_for_bloodwork], "time for appointment", lambda patient: [SimToken(patient)], time_for_appointment_guard)

# Define the bloodwork task
def bloodwork_behavior(patient_id, lab_staff_id):
    return [SimToken((patient_id, lab_staff_id), delay=uniform(5, 15))]

prototype.BPMNTask(hospital, [waiting_for_bloodwork, lab_staff], [done, lab_staff], "Blood Work", bloodwork_behavior, None)

# Define end event
prototype.BPMNEndEvent(hospital, [done], [], "complete")


# --------------------------
# DECISION MODEL
# --------------------------

# The decision moment: there is a patient waiting for 'time for appointment' and appointment_time is None
def scheduling_decision_guard(patient_id):
  patient_info = patient_data.read_data(patient_id)
  return not patient_info.has_appointment

# The decision: assign an appointment time
# The policy: assign an appointment time 1 minute from the current time
def scheduling_decision_behavior(patient_id):
  waiting_time_until_appointment = 1
  appointment_time = hospital.clock + waiting_time_until_appointment
  patient_info = patient_data.read_data(patient_id)
  patient_info.appointment_time = appointment_time
  patient_info.has_appointment = True
  patient_data.update_data(patient_id, patient_info)
  # we also set the delay of the token, such that it is actually controlled
  return [SimToken(patient_id, delay=waiting_time_until_appointment)]

# Now add the decision event to the simulator as a global event
decision = hospital.add_decision([waiting_for_appointment], [waiting_for_appointment], scheduling_decision_behavior, "Scheduling Decision", scheduling_decision_guard)
decision.set_invisible() # we make it invisible


# --------------------------
# SIMULATION
# --------------------------

v = Visualisation(hospital, layout_file="./temp/bpo_scheduling.layout")
v.show()
v.save_layout("./temp/bpo_scheduling.layout")