from typing import List
from os.path import join

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pygame.event import Event

from simpn.simulator import DecProblem, SimToken
from random import expovariate as exp
from random import uniform
from simpn.reporters import EventLogReporter, ProcessReporter, WarmupReporter
import simpn.prototypes as prototype
from simpn.visualisation.base import Visualisation
from simpn.visualisation.events import check_event
from simpn.visualisation.model_panel_mods import GraphingPanel, RecorderModule
from simpn.visualisation.events import EventType


"""
Implements the resource allocation example from the ER paper.

Process is:
- arrival start event -> treat task -> complete end event
- two types of patients T1, T2 can arrive.
- two doctors D1, D2 exist with names for the treat task.
- Patients arrive according to an exponential distribution with mean 5 minutes (12 per hour). They are 50/50 T1/T2.
- It takes on average 8 minutes to treat a patient (we can treat 7.5 per hour per resource = 15 per hour).
- Different doctor/ patient combinations have different treatment times. (D1, T1) is 6 minutes, (D1, T2) is 9 minutes, (D2, T1) is 10 minutes, (D2, T2) is 7 minutes.

Decision is:
- The decision moment is when there are unassigned patients and unassigned doctors.
- The decision is to assign one of the unassigned patients to one of the unassigned doctors.
"""


# --------------------------
# PROCESS MODEL
# --------------------------

# Instantiate the problem.
hospital = DecProblem()

# Define queues and other 'places' in the process.
waiting = prototype.BPMNFlow(hospital, "waiting")
done = prototype.BPMNFlow(hospital, "done")

# Define resources and resource data
doctors = prototype.BPMNLane(hospital, "oncologist")
doctor_data = prototype.DataStore(hospital, "oncologists")
doctors.put("D1")
doctor_data.update_data("D1", "Dr. Smith")
doctors.put("D2")
doctor_data.update_data("D2", "Dr. Johnson")

# Define patient data
patient_data = prototype.DataStore(hospital, "patients")

# Define start event with patient type data
def arrival_time():
  return exp(12/60)

def arrival_behavior(id):
  patient_type = "T1" if uniform(0, 1) < 0.5 else "T2"
  patient_data.update_data(id, patient_type)
  return SimToken(id)

prototype.BPMNStartEvent(hospital, [], [waiting], "arrives", arrival_time, arrival_behavior)

# Define the assignment variable X_{d, p} that indicates whether doctor d is assigned to patient p.
assignments = hospital.add_var("assignments")
assignments.set_invisible_edges() # we make the edges invisible, though strictly speaking the treat task depends on it, I just think it looks cleaner to not mix the BPMN with the Petri net edges

# Define the treatment task with doctor/ patient type dependent processing times
def treat_behavior(patient, doctor, assignment):
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

# The 'controlled behavior' is that only doctor/ patient combinations that are assigned (i.e., for which X_{d, p} = 1) can actually be used.
def treat_guard(patient, doctor, assignment):
  return (patient, doctor) == assignment

prototype.BPMNTask(hospital, [waiting, doctors, assignments], [done, doctors], "Examination", treat_behavior, treat_guard)

# Define end event
prototype.BPMNEndEvent(hospital, [done], [], "complete")


# --------------------------
# DECISION MODEL
# --------------------------

# The decision moment: there are unassigned patients and unassigned doctors
def assignment_decision_guard(state):
  return len(state.waiting) > 0 and len(state.oncologist) > 0

# The decision: since this is a simulation model, we model 'imperatively' rather than declaratively. We do so by modeling a decision policy that is executed at the decision moment.
# The policy: choose an assignment in order of preference (D1, T1) > (D2, T2) > (D1, T2) > (D2, T1)
def assignment_decision_behavior(state):
  best_assignment = None
  best_assignment_value = None # lower is better: (D1, T1) = 1, (D2, T2) = 2, (D1, T2) = 3, (D2, T1) = 4
  for o in state.oncologist:
    for p in state.waiting:
      o_id = o.value
      p_id = p.value
      p_type = patient_data.read_data(p_id)[1]
      if (o_id, p_type) == ("D1", "T1"):
        assignment_value = 1
      elif (o_id, p_type) == ("D2", "T2"):
        assignment_value = 2
      elif (o_id, p_type) == ("D1", "T2"):
        assignment_value = 3
      elif (o_id, p_type) == ("D2", "T1"):
        assignment_value = 4
      else:
        raise ValueError("Invalid doctor/ patient type combination. This should not happen if the model is correct.")
      if best_assignment is None or assignment_value < best_assignment_value:
        best_assignment = (p_id, o_id)
        best_assignment_value = assignment_value
  state.assignments.add(SimToken(best_assignment))
  return []

# Now add the decision event to the simulator as a global event
decision = hospital.add_global_decision(assignment_decision_behavior, assignment_decision_guard, name="Assignment Decision")
decision.set_invisible() # we make it invisible


# --------------------------
# SIMULATION
# --------------------------

class WarmUpGraphPanel(GraphingPanel):
    """
    Adds a grapher for the given reporter.
    """

    def __init__(self, reporter: WarmupReporter) -> None:
        super().__init__(
            25,
            25,
            300,
            150,
            "Mean Cycle Times",
            "(mean cycle time over time)"
        )
        self._reporter = reporter

    def listen_to(self) -> List[EventType]:
        return super().listen_to() + [EventType.BINDING_FIRED]

    def handle_event(self, event: Event) -> bool:
        super().handle_event(event)
        if check_event(event, EventType.BINDING_FIRED):
            reporter.callback(event.fired)
        return True

    def create_figure(self, figure: Figure) -> Figure | None:
        figure.patch.set_alpha(0.0)
        axes = figure.add_subplot(111)
        axes.patch.set_alpha(0.0)
        axes.tick_params(axis="both", labelsize=8)

        axes.plot(reporter.times, reporter.average_cycle_times, color="blue")
        axes.set_xlabel("time (min)", fontsize=8)
        axes.set_ylabel("cycle time (min)", fontsize=8)

        figure.subplots_adjust(left=0.17, right=0.90, bottom=0.25, top=0.9)

        return figure

reporter = WarmupReporter()
graph_panel = WarmUpGraphPanel(reporter)
recorder = RecorderModule(join(".", "temp", "example.mp4"), format="mp4", include_ui=True)
v = Visualisation(hospital, extra_modules=[graph_panel, recorder])
v.show()