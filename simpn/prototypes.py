def arrival(model, inflow, outflow, behavior, name, constraint, delay):
    # Process name
    a_name = name
    if a_name is not None:
        if behavior.__name__ != "<lambda>" and behavior.__name__ != name:
            raise TypeError("Arrival transition " + a_name + ": behavior function name and procedure name must be the same.")
    elif behavior.__name__ != "<lambda>":
        a_name = behavior.__name__
    else:
        raise TypeError("Arrival transition name must be set or behavior function must be named.")

    # Process other variables
    if len(inflow) != 0:
        raise TypeError("Arrival transition " + a_name + ": cannot have any inflow.")
    if len(outflow) != 1:
        raise TypeError("Arrival transition " + a_name + ": must have exactly one outflow.")

    invar_name = a_name + "_timer"
    invar = model.add_svar(invar_name)
    result = model.add_stransition([invar], [invar, outflow[0]], lambda a: [0, behavior()[0]], name=a_name, delay=lambda a: [delay()[0], 0])
    invar.put('dummy')

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
    start_transition_name = name + "_start"
    complete_transition_name = name + "_complete"
    busyvar = model.add_svar(busyvar_name)
    model.add_stransition(inflow, [busyvar], lambda c, r: [(c, r)], name=start_transition_name, delay=delay, guard=constraint)
    complete_transition = model.add_stransition([busyvar], outflow, lambda b: [b[0], b[1]], name=complete_transition_name)

    return complete_transition
