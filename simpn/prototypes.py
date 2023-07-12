def start_event(model, inflow, outflow, behavior, name, constraint, delay):
    # Process name
    a_name = name
    if a_name is not None:
        if behavior is not None and behavior.__name__ != "<lambda>" and behavior.__name__ != name:
            raise TypeError("Start event transition " + a_name + ": behavior function name and procedure name must be the same.")
    elif behavior is not None and behavior.__name__ != "<lambda>":
        a_name = behavior.__name__
    else:
        raise TypeError("Start event transition name must be set or behavior function must be named.")

    # Process other variables
    if len(inflow) != 0:
        raise TypeError("Start event transition " + a_name + ": cannot have any inflow.")
    if len(outflow) != 1:
        raise TypeError("Start event transition " + a_name + ": must have exactly one outflow.")

    invar_name = a_name + "_timer"
    invar = model.add_svar(invar_name)
    if behavior is None:
        result = model.add_stransition([invar], [invar, outflow[0]], lambda a: [(a[0] + 1,), (a[0],)], name=a_name + "<start_event>", delay=lambda a: [delay()[0], 0])
    else:
        result = model.add_stransition([invar], [invar, outflow[0]], lambda a: [(a[0]+1,), (a[0], behavior()[0])], name=a_name+"<start_event>", delay=lambda a: [delay()[0], 0])
    invar.put((0,))

    return result


def task(model, inflow, outflow, behavior, name, constraint, delay):
    # Process name
    if name is None:
        raise TypeError("Task transition name must be set.")

    # Process behavior
    if behavior is not None:
        raise TypeError("Task transition " + name + ": must not have a behavior.")

    # Process delay
    if delay is None:
        raise TypeError("Task transition " + name + ": must have a delay.")

    # Process other variables
    if len(inflow) != 2:
        raise TypeError("Task transition " + name + ": must have two input parameters; the first for cases and the second for resources.")
    if len(outflow) != 2:
        raise TypeError("Task transition " + name + ": must have two output parameters; the first for cases and the second for resources.")

    busyvar_name = name + "_busy"
    start_transition_name = name + "<task:start>"
    complete_transition_name = name + "<task:complete>"
    busyvar = model.add_svar(busyvar_name)
    model.add_stransition(inflow, [busyvar], lambda c, r: [(c, r)], name=start_transition_name, delay=delay, guard=constraint)
    complete_transition = model.add_stransition([busyvar], outflow, lambda b: [b[0], b[1]], name=complete_transition_name)

    return complete_transition


def event(model, inflow, outflow, behavior, name, constraint, delay):
    # Process name
    if name is None:
        raise TypeError("Event transition name must be set.")

    # Process behavior
    if behavior is not None:
        raise TypeError("Event transition " + name + ": must not have a behavior.")

    # Process delay
    if delay is None:
        raise TypeError("Event transition " + name + ": must have a delay.")

    # Process other variables
    if len(inflow) != 1:
        raise TypeError("Event transition " + name + ": must have one input parameter for cases.")
    if len(outflow) != 1:
        raise TypeError("Event transition " + name + ": must have one output parameter for cases.")

    transition = model.add_stransition(inflow, outflow, lambda c: [c], name=name, delay=delay, guard=constraint)

    return transition


def intermediate_event(model, inflow, outflow, behavior, name, constraint, delay):
    return event(model, inflow, outflow, behavior, name + "<intermediate_event>", constraint, delay)


def end_event(model, inflow, outflow, behavior, name, constraint, delay):

    # Process delay
    if delay is not None:
        raise TypeError("End event transition " + name + ": must not have a delay.")

    return event(model, inflow, outflow, behavior, name + "<end_event>", constraint, [0])
