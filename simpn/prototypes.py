import inspect
from simpn.simulator import SimToken
from simpn.immutabletypes import pn_list


def start_event(model, inflow, outflow, name, interarrival_time, behavior=None):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN start event.
    Adds it to the specified model. The start event generates new cases with the specified interarrival_time.
    Cases are places on the outflow SimVar. The cases will be a tuple (unique_number, case_data).
    Case_data will be generated according to the specified behavior, or unspecified if behavior==None.

    :param model: the SimProblem to which the start event composition must be added.
    :param inflow: parameter is only here for consistency, must be [].
    :param outflow: a list with a single SimVar in which the cases will be placed.
    :param name: the name of the start event.
    :param interarrival_time: the interarrival time with which events are generated. Can be a numeric value or a function that produces a numeric value, such as a sampling function from a random distribution.
    :param behavior: an optional behavior describing how case_data is produced.
    :return: the SimEvent that generates the cases.
    """
    # Process other variables
    if len(inflow) != 0:
        raise TypeError("Start event " + name + ": cannot have any inflow.")
    if len(outflow) != 1:
        raise TypeError("Start event " + name + ": must have exactly one outflow.")
    if not callable(interarrival_time) and not type(interarrival_time) is int and not type(interarrival_time) is float:
        raise TypeError("Start event " + name + ": must either have a value or a function as interarrival_time.")
    interarrival_time_f = interarrival_time
    if type(interarrival_time) is int or type(interarrival_time) is float:
        interarrival_time_f = lambda: interarrival_time

    invar_name = name + "_timer"
    invar = model.add_var(invar_name)
    if behavior is None:
        result = model.add_event([invar], [invar, outflow[0]], lambda a: [SimToken(a + 1, interarrival_time_f()), SimToken((a,))], name=name + "<start_event>")
    else:
        if not callable(behavior):
            raise TypeError("Start event " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        if len(inspect.signature(behavior).parameters) != 0:
            raise TypeError("Start event " + name + ": the behavior function must not have many parameters.")
        result = model.add_event([invar], [invar, outflow[0]], lambda a: [SimToken(a + 1, interarrival_time_f()), SimToken((a, behavior()[0].value))], name=name + "<start_event>")
    invar.put(0)

    return result


def basic_event(model, inflow, outflow, name, behavior, guard=None):
    """
    Just here for uniformity. Generates a simple event that can normally be created using model.add_event.
    The parameters are the same as for model.add_event and will simply be passed to that function.

    :return: the SimEvent that completes the task.
    """
    model.add_event(inflow, outflow, behavior, name=name, guard=guard)


def task(model, inflow, outflow, name, behavior, guard=None):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN task.
    Adds it to the specified model. The task must have two inflow and two outflow SimVar.
    The first SimVar represents the case that must be processed by the task and the second the resource.
    The behavior specifies how the task may change the case data.
    It also specifies the processing time of the task in the form of a SimToken delay.
    The behavior must take two input parameters according to the inflow and produces a single outflow, which is a tuple (case, resource)@delay.

    :param model: the SimProblem to which the task composition must be added.
    :param inflow: a list with two SimVar: a case SimVar and a resource SimVar.
    :param outflow: a list with two SimVar: a case SimVar and a resource SimVar.
    :param name: the name of the task.
    :param behavior: the behavior function, which takes two input parameters according to the inflow and produces a single outflow, which is a tuple (case, resource)@delay.
    :param guard: an optional guard that specifies which combination of case and resource is allowed. The guard must take two input parameters according to the inflow.
    :return: the SimEvent that completes the task.
    """

    # Process other variables
    if len(inflow) != 2:
        raise TypeError("Task event " + name + ": must have two input parameters; the first for cases and the second for resources.")
    if len(outflow) != 2:
        raise TypeError("Task event " + name + ": must have two output parameters; the first for cases and the second for resources.")
    if not callable(behavior):
        raise TypeError("Task event " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
    if len(inspect.signature(behavior).parameters) != 2:
        raise TypeError("Task event " + name + ": the behavior function must have two parameters.")

    busyvar_name = name + "_busy"
    start_event_name = name + "<task:start>"
    complete_event_name = name + "<task:complete>"
    busyvar = model.add_var(busyvar_name)
    model.add_event(inflow, [busyvar], behavior, name=start_event_name, guard=guard)
    complete_event = model.add_event([busyvar], outflow, lambda b: [SimToken(b[0]), SimToken(b[1])], name=complete_event_name)

    return complete_event


def choice(model, inflow, outflow, name, behavior, guards):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN choice.
    Adds it to the specified model. The choice must have one incoming SimVar and multiple outgoing SimVar.
    The incoming SimVar represents the case arriving at the choice.
    The outgoing SimVar represent the case leaving according to the possible choices.
    The behavior specifies how the task may change the case data.
    There must be a list of guards, as many as there are outgoing SimVar. Each guard represents the condition according to which a
    particular choice is made.

    :param model: the SimProblem to which the choice composition must be added.
    :param inflow: a list with one SimVar.
    :param outflow: a list with multiple SimVar. One for each possible choice.
    :param name: the name of the choice.
    :param behavior: the behavior function which can modify the case data.
    :param guards: a list with multiple guards. One for each possible choice.
    """

    # Process other variables
    if len(inflow) != 1:
        raise TypeError("Choice event " + name + ": must have one inflow variable.")
    if len(outflow) < 2:
        raise TypeError("Choice event " + name + ": must have at least two outflow variables representing the possible choices.")
    if not callable(behavior):
        raise TypeError("Choice event " + name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
    if len(inspect.signature(behavior).parameters) != 1:
        raise TypeError("Choice event " + name + ": the behavior function must have one parameters for the inflow variable.")
    if type(guards) is not list or len(guards) != len(outflow):
        raise TypeError("Choice event " + name + ": there must be a list of guards; as many as there are outflow parameters.")
    for guard in guards:
        if not callable(guard):
            raise TypeError("Choice event " + name + ": the guards must be functions. (Maybe you made it a function call, exclude the brackets.)")
        if len(inspect.signature(guard).parameters) != 1:
            raise TypeError("Choice event " + name + ": the guards must have one parameters for the inflow variable.")

    chosenvar = model.add_var(name + "_chosen")
    choose_event = model.add_event(inflow, [chosenvar], behavior, name=name)

    for i in range(len(outflow)):
        model.add_event([chosenvar], [outflow[i]], lambda c: [SimToken(c)], name="choose_" + outflow[i]._id, guard=guards[i])

    return choose_event


def intermediate_event(model, inflow, outflow, name, behavior, guard=None):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN intermediate event.
    The intermediate event can make changes to the data of a case and can generate waiting time for the case.

    :param model: the SimProblem to which the event composition must be added.
    :param inflow: a list with one SimVar: a case SimVar.
    :param outflow: a list with one SimVar: a case SimVar.
    :param name: the name of the event.
    :param behavior: specifies the changes that the intermediate event makes to the data and the delay that the intermediate event may lead to.
    :param guard: an optional guard that specifies under which condition the intermediate event can happen.
    :return: the SimEvent that represents the event.
    """
    if len(inflow) != 1:
        raise TypeError("Event " + name + ": must have one input parameter for cases.")
    if len(outflow) != 1:
        raise TypeError("Event " + name + ": must have one output parameter for cases.")

    return model.add_event(inflow, outflow, behavior, name=name + "<intermediate_event>", guard=guard)


def end_event(model, inflow, outflow, name):
    """
    Generates a composition of SimVar and SimEvent that represents a BPMN end event.

    :param model: the SimProblem to which the event composition must be added.
    :param inflow: a list with one SimVar: a case SimVar.
    :param outflow: parameter is only here for consistency, must be [].
    :param name: the name of the event.
    :return: the SimEvent that represents the event.
    """
    if len(inflow) != 1:
        raise TypeError("Event " + name + ": must have one input parameter for cases.")
    if len(outflow) != 0:
        raise TypeError("Event " + name + ": must not have output parameters.")

    return model.add_event(inflow, outflow, lambda c: [], name=name + "<end_event>")
