from simpn.helpers import BPMN
from simpn.prototypes import BPMNFlow
from simpn.simulator import SimProblem, SimToken, SimTokenValue
from simpn.visualisation import Visualisation

from simpn.priorities import FirstClassPriority
from simpn.priorities import WeightedFirstClassPriority
from simpn.priorities import NearestToCompletionPriority

import random
from os.path import join, exists
from enum import Enum, auto

LAYOUT_FILE = join(".", "temp", "priorities_for_bps.layout")
PRIORITY = 3


class CustomerType(Enum):
    NEW = auto()
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()

    @staticmethod
    def pick_type():
        r = random.random()
        if r < 0.5:
            return CustomerType.NEW
        elif r < 0.7:
            return CustomerType.BRONZE
        elif r < 0.9:
            return CustomerType.SILVER
        else:
            return CustomerType.GOLD

    @staticmethod
    def convert_new():
        r = random.random()
        if r < 0.33:
            return CustomerType.BRONZE
        elif r < 0.66:
            return CustomerType.SILVER
        else:
            return CustomerType.GOLD

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return self.__str__()


def employee_speed(base_time, employee: SimTokenValue):
    return random.expovariate(1 / base_time) / employee.work_speed


match PRIORITY:
    case 1:
        class_priority = FirstClassPriority(
            class_attr="type",
            priority_ordering=[
                CustomerType.GOLD,
                CustomerType.SILVER,
                CustomerType.BRONZE,
            ],
        )
    case 2:
        class_priority = WeightedFirstClassPriority(
            class_attr="type",
            weights={
                CustomerType.GOLD: 10,
                CustomerType.SILVER: 5,
                CustomerType.BRONZE: 2.5,
            },
        )
    case 3:
        class_priority = NearestToCompletionPriority()
    case _:
        raise ValueError("Unknown PRIORITY value: {}".format(PRIORITY))


model = SimProblem(binding_priority=class_priority)


class EmployeePool(BPMN):
    model = model
    name = "employees"
    type = "resource-pool"
    amount = 0


employees = model.var("employees")
for i in range(5):
    employees.put(
        SimTokenValue("employee-{i}".format(i=i + 1), work_speed=random.uniform(2, 5))
    )
employees.set_invisible_edges()

match PRIORITY:
    case 1 | 2:
        BPMNFlow(
            model,
            "considering",
            priority=class_priority.find_priority,
        )
    case 3:
        BPMNFlow(
            model,
            "considering",
        )


class Start(BPMN):
    model = model
    name = "started-process"
    type = "start"
    outgoing = ["considering"]

    def interarrival_time():
        return random.expovariate(4)

    def behaviour(identifier: str):
        val = SimTokenValue(identifier)
        val.type = CustomerType.pick_type()
        return SimToken(val)


class Investigate(BPMN):
    model = model
    name = "Investigate"
    type = "task"
    incoming = ["considering", "employees"]
    outgoing = ["deciding", "employees"]

    def behaviour(case: SimTokenValue, employee: SimTokenValue):
        work_time = employee_speed(15, employee)

        new_case = case.clone()
        if new_case.type == CustomerType.NEW:
            new_case.type = CustomerType.convert_new()
            work_time += employee_speed(5, employee)
        new_case.started = model.var("time").marking[0].value

        return [SimToken((new_case, employee), delay=work_time)]


class DecisionXorSplit(BPMN):
    model = model
    type = "gat-ex-split"
    incoming = ["deciding"]
    outgoing = [
        "handling-bronze",
        "handling-silver",
        "handling-gold",
    ]
    name = "What type of customer?"

    def choice(val: SimTokenValue):
        if val.type == CustomerType.BRONZE:
            return [SimToken(val), None, None]
        elif val.type == CustomerType.SILVER:
            return [None, SimToken(val), None]
        elif val.type == CustomerType.GOLD:
            return [None, None, SimToken(val)]
        else:
            raise ValueError("Unknown customer type: {}".format(val.type))


class InvoiceBronze(BPMN):
    model = model
    type = "task"
    incoming = ["handling-bronze", "employees"]
    outgoing = ["invoiced-bronze", "employees"]
    name = "Invoice Bronze"

    def behaviour(val, res):
        work_time = employee_speed(10, res)
        return [SimToken((val, res), delay=work_time)]


class PickPackageForSilver(BPMN):
    model = model
    type = "task"
    incoming = ["handling-silver", "employees"]
    outgoing = ["picked-silver", "employees"]
    name = "Pick Package for Silver"

    def behaviour(val, res):
        work_time = employee_speed(10, res)
        return [SimToken((val, res), delay=work_time)]


class InvoiceSilver(BPMN):
    model = model
    type = "task"
    incoming = ["picked-silver", "employees"]
    outgoing = ["invoiced-silver", "employees"]
    name = "Invoice Silver"

    def behaviour(val, res):
        work_time = employee_speed(5, res)
        return [SimToken((val, res), delay=work_time)]


class CallGoldCustomer(BPMN):
    model = model
    type = "task"
    incoming = ["handling-gold", "employees"]
    outgoing = ["called-customer", "employees"]
    name = "Calling Customer"

    def behaviour(val, res):
        attempts = random.randint(1, 5)
        work_time = attempts * employee_speed(2, res)
        return [SimToken((val, res), delay=work_time)]


class PickPackageGold(BPMN):
    model = model
    type = "task"
    incoming = ["called-customer", "employees"]
    outgoing = ["picked-gold", "employees"]
    name = "Pick Package for Gold"

    def behaviour(val, res):
        work_time = employee_speed(20, res)
        return [SimToken((val, res), delay=work_time)]


class InvoiceGold(BPMN):
    model = model
    type = "task"
    incoming = ["picked-gold", "employees"]
    outgoing = ["invoiced-gold", "employees"]
    name = "Invoice Gold"

    def behaviour(val, res):
        work_time = employee_speed(10, res)
        return [SimToken((val, res), delay=work_time)]


class InvoiceXorJoin(BPMN):
    model = model
    type = "gat-ex-join"
    incoming = ["invoiced-gold", "invoiced-silver", "invoiced-bronze"]
    outgoing = ["invoiced-customer"]
    name = "Customer Join"


class HandledCustomer(BPMN):
    model = model
    type = "end"
    incoming = ["invoiced-customer"]
    name = "Handled Customer"


if exists(LAYOUT_FILE):
    vis = Visualisation(model, layout_file=LAYOUT_FILE)
else:
    vis = Visualisation(model)

model.set_binding_priority(class_priority)
vis.show()
vis.save_layout(join(".", "temp", "priorities_for_bps.layout"))
