import random
import inspect
import copy


class SimVar:
    """
    A simulation variable SimVar has an identifier and a marking.
    A simulation variable can have multiple values. These values are available at particular times.
    For example, a variable van have the value 1 at time 0 (denoted as 1@0) and also 2@0.
    These values are also called tokens. Multiple tokens are called a marking of the variable.
    The marking is represented as a dictionary of tokens -> the number of each token.
    For example, {1@0: 1, 2@0: 1} represents the situation above, in which there is one token
    with value 1 at time 0 and one with value 2 at time 0.

    :param _id: the identifier of the SimVar.
    :param marking: the marking of the SimVar.
    """

    def __init__(self, _id, marking=None):
        self._id = _id
        if marking is None:
            self.marking = dict()
        else:
            self.marking = copy.deepcopy(marking)

    def put(self, value, time=0):
        """
        Put a token value in the SimVar at a particular time.

        :param value: the value to put in the SimVar.
        :param time: the time to make this value available at.
        """
        token = SimToken(value, time)
        self.add_token(token)

    def add_token(self, token, count=1):
        """
        Adds a token value in the SimVar.

        :param token: the token value to put in the SimVar.
        :param count: the number of times to put the token value in the SimVar (defaults to 1 time).
        """
        if token not in self.marking:
            self.marking[token] = count
        else:
            self.marking[token] += count

    def remove_token(self, token):
        """
        Removes a token value (once) from the SimVar.

        :param token: the token value to remove from the SimVar.
        """
        if token in self.marking:
            self.marking[token] -= 1
        else:
            raise LookupError("No token '" + token + "' at place '" + str(self) + "'.")
        if self.marking[token] == 0:
            del self.marking[token]

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()


class SimTransition:
    """
    A simulation transition SimTransition that can happen when tokens are available on all of its
    incoming SimVar and its guard evaluates to True. When it happens, it consumes a token from each
    of its incoming SimVar and produces a token on each of its outgoing places according to `behavior`.
    If the transition also has a `delay`, it will produce the tokens on the outgoing places according to that delay.
    For example, consider the transition with `incoming` `SimVar` [a, b] that have 2@1 and 2@1.
    The transition has `outgoing` `SimVar` [c, d], behavior lambda a, b: [a + b, a - b], and
    delay [1, 2]. This transition can happen for a = 2@1 and b = 2@1. Thus, it will happen at time 1, generating
    [3, 1] according to its behavior with delays [1, 2]. Therefore, after the transition has happened, c and d
    will have the tokens 3@2 and 1@3.

    :param _id: the identifier of the transition.
    :param incoming: a list of incoming SimVar of the transition.
    :param outgoing: a list of outgoing SimVar of the transition
    :param guard: a function that takes as many parameters as there are incoming SimVar. The function must evaluate to True or False for all possible values of SimVar. The transition can only happen for values for which the guard function evaluates to True.
    :param behavior: a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many elements as there are outgoing SimVar. When the transition happens, the function is performed on the incoming SimVar and the result of the function is put on the outgoing SimVar.
    :param delay: A list with as many numeric elements as there are outgoing SimVar, or a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many numeric values as there are outgoing SimVar. The values that are created by the behavior of the transition are put on the outgoing SimVar with the corresponding delay.
    """

    def __init__(self, _id, guard=None, behavior=None, delay=None, incoming=None, outgoing=None):
        self._id = _id
        self.guard = guard
        if incoming is None:
            self.incoming = []
        else:
            self.incoming = incoming
        if outgoing is None:
            self.outgoing = []
        else:
            self.outgoing = outgoing
        self.behavior = behavior
        self.delay = delay

    def set_guard(self, func):
        """
        Set the guard function.

        :param func: a function with as many input parameters as there are incoming SimVar, which generates a list with as many elements as there are outgoing SimVar.
        """
        self.guard = func

    def set_inflow(self, incoming):
        """
        Set the incoming SimVar.

        :param incoming: a list of SimVar.
        """
        self.incoming = incoming

    def set_outflow(self, outgoing):
        """
        Set the outgoing SimVar.

        :param outgoing: a list of SimVar.
        """
        self.outgoing = outgoing

    def set_delay(self, delay):
        """
        Set the delay.

        :param delay: either a list with as many numeric elements as there are outgoing SimVar, or a function with as many input parameters as there are incoming SimVar, which generates a list with as many numeric elements as there are outgoing SimVar.
        """
        self.delay = delay

    def get_id(self):
        return self._id

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()


class SimToken:
    """
    A token SimToken, which is a possible value of a SimVar. A token has a value and the time at which this value is available in a SimVar.

    :param value: the value of the token.
    :param time: the time at which the value is available.
    """
    def __init__(self, value, time=None):
        self.value = value
        self.time = time

    def __eq__(self, token):
        return self.value == token.value and self.time == token.time

    def __lt__(self, token):
        return (self.value, self.time) < (token.value, token.time)

    def __hash__(self):
        return (self.value, self.time).__hash__()

    def __str__(self):
        result = str(self.value)
        if self.time is not None:
            result += "@" + str(self.time)
        return result

    def __repr__(self):
        return self.__str__()


class SimProblem:
    """
    A simulation problem SimProblem, which consists of a collection of simulation variables SimVar and a collection of simulation transitions SimTransition.
    The simulation has a time and a marking of SimVar. A marking is an assignment of values to SimVar variables (also see SimVar).
    The difference between a normal Python variable and a SimVar is that: (1) a SimVar can have multiple values; and (2) these values have a simulation time
    at which they become available. A SimTransition is a function that takes SimVar values as input and produces SimVar values (also see SimTransition). The difference with normal
    Python functions is that transitions can happen whenever its incoming SimVar parameters have a value. If a SimVar parameter has multiple values,
    it can happen on any of these values.

    :param debugging: if set to True, produces more information for debugging purposes (defaults to True).
    """
    def __init__(self, debugging=True):
        self.places = []
        self.transitions = []
        self.id2node = dict()
        self.clock = 0
        self._debugging = debugging

    def __str__(self):
        result = ""
        result += "P={"
        for i in range(len(self.places)):
            result += str(self.places[i])
            if i < len(self.places) - 1:
                result += ","
        result += "}\n"
        result += "T={"
        for i in range(len(self.transitions)):
            result += str(self.transitions[i])
            if self.transitions[i].guard is not None:
                result += "[" + self.transitions[i].guard.__name__ + "]"
            result += ":" + self.transitions[i].behavior.__name__
            if self.transitions[i].delay is not None:
                result += "@"
                if isinstance(self.transitions[i].delay, list):
                    result += str(self.transitions[i].delay)
                else:
                    result += self.transitions[i].delay.__name__
            if i < len(self.transitions) - 1:
                result += ","
        result += "}\n"
        arcs = []
        for t in self.transitions:
            for p in t.incoming:
                arcs.append("(" + str(p) + "," + str(t) + ")")
            for p in t.incoming:
                arcs.append("(" + str(t) + "," + str(p) + ")")
        result += "A={"
        for i in range(len(arcs)):
            result += arcs[i]
            if i < len(arcs) - 1:
                result += ","
        result += "}\n"
        markings = []
        for p in self.places:
            if len(p.marking) > 0:
                mstr = str(p) + ":"
                ti = 0
                for (token, count) in p.marking.items():
                    mstr += str(count) + "`" + str(token) + "`"
                    if ti < len(p.marking) - 1:
                        mstr += "++"
                    ti += 1
                markings.append(mstr)
        result += "M={"
        for i in range(len(markings)):
            result += markings[i]
            if i < len(markings) - 1:
                result += ","
        result += "}"                
        return result

    def add_svar(self, name):
        """
        Creates a new SimVar with the specified name as identifier. Adds the SimVar to the problem and returns it.

        :param name: a name for the SimVar.
        :return: a SimVar with the specified name as identifier.
        """
        # Check name
        if name in self.id2node:
            raise TypeError("Node with name " + name + " already exists. Names must be unique.")

        # Generate and add SimVar
        result = SimVar(name)
        self.places.append(result)
        self.id2node[name] = result

        return result

    def add_stransition(self, inflow, outflow, behavior, name=None, guard=None, delay=None, prototype=None):
        """
        Creates a new SimTransition with the specified parameters (also see SimTransition). Adds the SimTransition to the problem and returns it.
        If a prototype is passed (also see package prototypes), multiple transitions and simulation variables may be added to the model, according to the prototype.

        :param name: the identifier of the transition.
        :param inflow: a list of incoming SimVar of the transition.
        :param outflow: a list of outgoing SimVar of the transition/
        :param guard: a function that takes as many parameters as there are incoming SimVar. The function must evaluate to True or False for all possible values of SimVar. The transition can only happen for values for which the guard function evaluates to True.
        :param behavior: a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many elements as there are outgoing SimVar. When the transition happens, the function is performed on the incoming SimVar and the result of the function is put on the outgoing SimVar.
        :param delay: A list with as many numeric elements as there are outgoing SimVar, or a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many numeric values as there are outgoing SimVar. The values that are created by the behavior of the transition are put on the outgoing SimVar with the corresponding delay.
        :param prototype: a function that generates a composition of transitions and simulation variables rather than a single transition, the generated composition uses the same inflow and outflow SimVar and may use any of the other parameters as specified by the prototype.
        :return: a SimTransition with the specified parameters.
        """
        if prototype is not None:
            return prototype(self, inflow, outflow, behavior, name, guard, delay)

        # Check name
        t_name = name
        if t_name is not None:
            if behavior.__name__ != "<lambda>" and behavior.__name__ != t_name:
                raise TypeError("Transition " + t_name + ": behavior function name and procedure name must be the same.")
        elif behavior.__name__ != "<lambda>":
            t_name = behavior.__name__
        else:
            raise TypeError("Transition name must be set or procedure behavior function must be named.")
        if t_name in self.id2node:
            raise TypeError("Transition " + t_name + ": node with the same name already exists. Names must be unique.")

        # Check inflow
        c = 0
        for i in inflow:
            if not isinstance(i, SimVar):
                raise TypeError("Transition " + t_name + ": inflow with index " + str(c) + " is not a SimVar.")
            c += 1

        # Check outflow
        c = 0
        for o in outflow:
            if not isinstance(o, SimVar):
                raise TypeError("Transition " + t_name + ": outflow with index " + str(o) + " is not a SimVar.")
            c += 1

        # Check behavior function
        if not callable(behavior):
            raise TypeError("Transition " + t_name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        parameters = inspect.signature(behavior).parameters
        if len(parameters) != len(inflow):
            raise TypeError("Transition " + t_name + ": the behavior function must take as many parameters as there are input variables.")

        # Check constraint
        if guard is not None:
            if not callable(guard):
                raise TypeError("Transition " + t_name + ": the constraint must be a function. (Maybe you made it a function call, exclude the brackets.)")
            parameters = inspect.signature(guard).parameters
            if len(parameters) != len(inflow):
                raise TypeError("Transition " + t_name + ": the constraint function must take as many parameters as there are input variables.")

        # Check delay function
        if type(delay) == list:
            if len(delay) != len(outflow):
                raise TypeError("Transition " + t_name + ": if delay is a list, it must be have as many elements as there are output variables.")
            c = 0
            for d in delay:
                if not type(d) is int and not type(d) is float:
                    raise TypeError("Transition " + t_name + ": if delay is a list, it must be a list of numbers.")
                c += 1
        elif callable(delay):
            parameters = inspect.signature(delay).parameters
            if len(parameters) != len(inflow):
                raise TypeError("Transition " + t_name + ": if the delay is a function, it must take as many parameters as there are input variables.")
        elif delay is not None:
            raise TypeError("Procedure " + t_name + ": the delay must either be a list of numeric values or a function that evaluates to a list of numeric values.")

        # Generate and add SimTransition
        result = SimTransition(t_name, guard=guard, behavior=behavior, delay=delay, incoming=inflow, outgoing=outflow)
        self.transitions.append(result)
        self.id2node[t_name] = result

        return result

    @staticmethod
    def tokens_combinations(transition):
        """
        Creates a list of token combinations that are available to the specified transition.
        These are combinations of tokens that are on the incoming SimVar of the transition.
        For example, if a transition has incoming SimVar a and b with tokens 1@0 on a and 2@0, 3@0 on b,
        the possible combinations are [(a, 1@0), (b, 2@0)] and [(a, 1@0), (b, 3@0)]

        :param transition: the transition to return the token combinations for.
        :return: a list of lists, each of which is a token combination.
        """
        # create all possible combinations of incoming token values
        bindings = [[]]
        for place in transition.incoming:
            new_bindings = []
            for token in place.marking.keys():  # get set of colors in incoming place
                for binding in bindings:
                    new_binding = binding.copy()
                    new_binding.append((place, token))
                    new_bindings.append(new_binding)
            bindings = new_bindings
        return bindings

    def transition_bindings(self, transition):
        """
        Calculates the set of bindings that enables the given transition.
        Each binding is a tuple ([(place, token), (place, token), ...], time) that represents a single enabling binding.
        A binding is
        a possible token combination (see token_combinations), for which the transition's
        guard function evaluates to True. In case there is no guard function, any combination is also a binding.
        The time is the time at which the latest token is available.
        For example, if a transition has incoming SimVar a and b with tokens 1@2 on a and 2@3, 3@1 on b,
        the possible bindings are ([(a, 1@2), (b, 2@3)], 3) and ([(a, 1@2), (b, 3@1)], 2)

        :param transition: the transition for which to calculate the enabling bindings.
        :return: list of tuples ([(place, token), (place, token), ...], time)
        """
        if len(transition.incoming) == 0:
            raise Exception("Though it is strictly speaking possible, we do not allow transitions like '" + str(self) + "' without incoming arcs.")

        bindings = self.tokens_combinations(transition)

        # a binding must have all incoming places
        nr_incoming_places = len(transition.incoming)
        new_bindings = []
        for binding in bindings:
            if len(binding) == nr_incoming_places:
                new_bindings.append(binding)
        bindings = new_bindings

        # if a transition has a guard, only bindings are enabled for which the guard evaluates to True
        result = []
        for binding in bindings:
            variable_values = []
            time = None
            for (place, token) in binding:
                variable_values.append(token.value)
                if time is None or token.time > time:
                    time = token.time
            enabled = True
            if transition.guard is not None:
                try:
                    enabled = transition.guard(*variable_values)
                except Exception as e:
                    raise TypeError("Transition " + transition + ": guard generates exception for values " + str(variable_values) + ".") from e
                if self._debugging and not isinstance(enabled, bool):
                    raise TypeError("Transition " + transition + ": guard does evaluate to a Boolean for values " + str(variable_values) + ".")
            if enabled:
                result.append((binding, time))
        return result

    def bindings(self):
        """
        Calculates the set of timed bindings that is enabled over all transitions in the problem.
        Each binding is a tuple ([(place, token), (place, token), ...], time, transition) that represents a single enabling binding.
        If no timed binding is enabled at the current clock time, updates the current clock time to the earliest time at which there is.
        :return: list of tuples ([(place, token), (place, token), ...], time, transition)
        """
        untimed_bindings = []
        timed_bindings = []
        for t in self.transitions:
            for (binding, time) in self.transition_bindings(t):
                if time is None:
                    untimed_bindings.append((binding, time, t))
                else:
                    timed_bindings.append((binding, time, t))
        # timed bindings are only enabled if they have time <= clock
        # if there are no such bindings, set the clock to the earliest time at which there are
        timed_bindings.sort(key=lambda b: b[1])
        if len(timed_bindings) > 0 and timed_bindings[0][1] > self.clock:
            self.clock = timed_bindings[0][1]
        # now return the untimed bindings + the timed bindings that have time <= clock
        return untimed_bindings + [(binding, time, t) for (binding, time, t) in timed_bindings if time <= self.clock]

    def fire(self, timed_binding):
        """
        Fires the specified timed binding.
        Binding is a tuple ([(place, token), (place, token), ...], time, transition)
        """
        (binding, time, transition) = timed_binding

        # process incoming places:
        variable_assignment = []
        for (place, token) in binding:
            # remove tokens from incoming places
            place.remove_token(token)
            # assign values to the variables on the arcs
            variable_assignment.append(token.value)

        # calculate the result of the behavior of the transition
        try:
            result = transition.behavior(*variable_assignment)
        except Exception as e:
            raise TypeError("Transition " + str(transition) + ": behavior function generates exception for values " + str(variable_assignment) + ".") from e
        if self._debugging:
            if type(result) != list:
                raise TypeError("Transition " + str(transition) + ": behavior function generates does not generate a list for values " + str(variable_assignment) + ".")
            if len(result) != len(transition.outgoing):
                raise TypeError("Transition " + str(transition) + ": behavior function does not generate as many values as there are output variables for values " + str(variable_assignment) + ".")
        delay = [0] * len(transition.outgoing)
        if transition.delay is not None:
            if callable(transition.delay):
                try:
                    delay = transition.delay(*variable_assignment)
                except Exception as e:
                    raise TypeError("Transition " + str(transition) + ": delay function generates exception for values " + str(variable_assignment) + ".") from e
                if self._debugging:
                    if type(delay) != list:
                        raise TypeError("Transition " + str(transition) + ": delay function generates does not generate a list for values " + str(variable_assignment) + ".")
                    if len(delay) != len(transition.outgoing):
                        raise TypeError("Transition " + str(transition) + ": delay function does not generate as many values as there are output variables for values " + str(variable_assignment) + ".")
                    c = 0
                    for d in delay:
                        if not type(d) is int and not type(d) is float:
                            raise TypeError("Transition " + str(transition) + ": delay function generates non-numeric output at output variable " + str(transition.outgoing[c]) + " for values " + str(variable_assignment) + ".")
                        c += 1
            else:
                delay = transition.delay

        for i in range(len(result)):
            token = SimToken(result[i], time=self.clock + delay[i])
            transition.outgoing[i].add_token(token)

    def simulate(self, duration, reporter=None):
        """
        Executes a simulation run for the problem for the specified duration.
        A simulation run executes transitions until this is no longer possible, or until the specified duration.
        If at any moment multiple transitions can happen, one is selected at random.
        At the end of the simulation run, the problem is in the state that is the result of the run.
        If the reporter is set, its callback function is called with parameters (binding, time, transition)
        each time a transition happens (for a binding at a moment in simulation time).

        :param duration: the duration of the simulation.
        :param reporter: a class that implements a callback function, which is called each time a transition happens.
        """
        active_model = True
        while self.clock <= duration and active_model:
            bindings = self.bindings()
            if len(bindings) > 0:
                timed_binding = random.choice(bindings)
                self.fire(timed_binding)
                if reporter is not None:
                    reporter.callback(timed_binding)
            else:
                active_model = False
