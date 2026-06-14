from typing import List
from os.path import join

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pygame.event import Event

from simpn.simulator import SimProblem, SimToken
from random import expovariate as exp
from simpn.reporters import WarmupReporter
from simpn.visualisation.events import EventType
from simpn.visualisation.model_panel_mods import GraphingPanel, RecorderModule
from simpn.visualisation.events import check_event
from simpn.visualisation import Visualisation
from simpn.helpers import BPMN

RECORD = False


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
            "Warm up Arrival Times",
            "The average cycle times over time.",
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
        axes.set_xlabel("arrival time (min)", fontsize=8)
        axes.set_ylabel("cycle time (min)", fontsize=8)

        figure.subplots_adjust(left=0.17, right=0.90, bottom=0.25, top=0.9)

        return figure


# Instantiate a simulation problem.
shop = SimProblem()


# Define queues and other 'places' in the process.
class Done(BPMN):
    type = "flow"
    model = shop
    name = "done"


class Waiting(BPMN):
    type = "flow"
    model = shop
    name = "waiting"


# Define helper classes for simulation
class Cassiers(BPMN):
    type = "resource-pool"
    model = shop
    name = "cassier"
    amount = 1


class Start(BPMN):
    type = "start"
    model = shop
    name = "arrive"
    amount = 1
    outgoing = ["waiting"]

    def interarrival_time():
        return exp(1 / 10)


class Scan(BPMN):
    type = "task"
    model = shop
    name = "scan_groceries"
    incoming = ["waiting", "cassier"]
    outgoing = ["done", "cassier"]

    def behaviour(c, r):
        return [SimToken((c, r), delay=exp(1 / 9))]


class End(BPMN):
    type = "end"
    model = shop
    name = "complete"
    incoming = ["done"]


shop.store_checkpoint("initial state")

# Simulate once with a warmup reporter.
reporter = WarmupReporter()
graph_panel = WarmUpGraphPanel(reporter)
mods = [
    graph_panel
]

if RECORD:
    recorder = RecorderModule(join(".", "temp", "presentation_4b.gif"), include_ui=True)
    mods.append(recorder)

vis = Visualisation(shop, extra_modules=mods)
for _ in range(15):
    vis.main_window.simulation_panel.faster_simulation()
vis.main_window.simulation_panel.start_simulation()
vis.show()

shop.simulate(20000, reporter)

plt.plot(reporter.times, reporter.average_cycle_times, color="blue")
plt.xlabel("arrival time (min)", fontsize=8)
plt.xticks(range(0, 20001, 5000))
plt.yticks(fontsize=8)
plt.xticks(range(0, 20001, 5000), fontsize=8)
plt.ylabel("cycle time (min)", fontsize=8)
plt.show()
