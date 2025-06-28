import inspect
from sortedcontainers import SortedList
import simpn.visualisation as vis


class SimVar:
    """
    A simulation variable SimVar has an identifier and a marking.
    A simulation variable can have multiple values. These values are available at particular times.
    For example, a variable van have the value 1 at time 0 (denoted as 1@0) and also 2@0.
    These values are also called tokens. Multiple tokens are called a marking of the variable.
    The marking is represented as a sorted list, which keeps tokens in the order of their priority, by default this is their timestamp.
    The functions put and remove, put and remove tokens in such a way that the order is maintained.

    :param _id: the identifier of the SimVar.
    :param priority: a function that takes a token as input and returns a value that is used to sort the tokens in the order in which they will be processed (lower values first). The default is processing in the order of the time of the token.
    """

    def __init__(self, _id, priority=lambda token: token.time):
        self._id = _id
        self.marking = SortedList(key=priority)
        self.checkpoints = dict()
        self.queue = SimVarQueue(self)
        self.visualize = True

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
        self.marking.add(token)

    def remove_token(self, token):
        """
        Removes a token value (once) from the SimVar.

        :param token: the token value to remove from the SimVar.
        """
        if token in self.marking:
            self.marking.remove(token)
        else:
            raise LookupError("No token '" + token + "' at place '" + str(self) + "'.")          
    
    def get_id(self):
        return self._id
    
    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()

    def store_checkpoint(self, name):
        """
        Stores a checkpoint of the SimVar marking with the given name. The checkpoint can be restored later with restore_checkpoint.
        """
        self.checkpoints[name] = [token.copy() for token in self.marking]
    
    def restore_checkpoint(self, name):
        """
        Restores the SimVar marking from the checkpoint with the given name.
        """
        if name in self.checkpoints:
            self.marking.clear()
            for token in self.checkpoints[name]:
                self.add_token(token)
        else:
            raise LookupError("No checkpoint '" + name + "' at place '" + str(self) + "'.")

    def get_visualisation(self):
        return vis.PlaceViz(self)

    def set_invisible(self):
        self.visualize = False

class SimVarQueue(SimVar):
    """
    A simulation variable that contains the queue of tokens from another SimVar.
    The identifier of this SimVar is <simvar_id>.queue, where simvar_id is the _id of the SimVar of which it contains the queue.
    Regular SimVar have a queue property that refers to their SimVarQueue variable.
    """
    QUEUE_SUFFIX = ".queue"
    
    def __init__(self, simvar):
        self._id = simvar._id + SimVarQueue.QUEUE_SUFFIX
        self.simvar = simvar

    @property
    def marking(self):
        token = SimToken(list(self.simvar.marking), 0)
        return [token]

    def put(self, value, time=0):
        pass

    def add_token(self, token, count=1):
        # adding a queue token means adding an entire queue.
        if count != 1:
            raise TypeError(self._id + ": the queue is placed back multiple times (count != 1). However, there can only be one queue.")
        # we check if the token is a list of tokens (i.e. a queue) and if so, we add all tokens in the queue.
        try:
            for t in token:
                if not isinstance(t, SimToken):
                    raise TypeError(self._id + ": something went wrong placing the queue back with value " + str(token) + ". Element " + str(t) + " does not appear to be a token, but the queue must be a list of tokens. Maybe you just added a value, not a token?")
                self.simvar.add_token(t)
        except:
            raise TypeError(self._id + ": something went wrong placing the queue back with value " + str(token) + ".")

    def remove_token(self, token):
        # removing a queue token means removing the queue.
        # However, the queue object should remain intact, because that is the same object that is passed as a token.
        # Therefore, we set the marking to a new empty list.
        self.simvar.marking = SortedList(key=self.simvar.marking.key)

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()	
    

class SimVarTime(SimVar):
    """
    A simulation variable that contains the simulation time.
    This variable only always has a single token value, which is the simulation time.
    The identifier of this SimVar is 'time', which consequently is a reserved name.
    """
    TIME_ID = "time"
    
    def __init__(self, problem):
        self._id = SimVarTime.TIME_ID
        self.checkpoints = dict()
        self.problem = problem
        self.visualize = True

    @property
    def marking(self):
        token = SimToken(self.problem.clock)
        return SortedList([token])

    def put(self, value, time=0):
        pass

    def add_token(self, token, count=1):
        pass

    def remove_token(self, token):
        pass

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()


class SimEvent:
    """
    A simulation event SimEvent that can happen when tokens are available on all of its
    incoming SimVar and its guard evaluates to True. When it happens, it consumes a token from each
    of its incoming SimVar and produces a token on each of its outgoing places according to `behavior`.
    The behavior takes just the values of the SimVar as input, but produces tokens as output: values with a delay.
    The delay can also be 0, meaning the token is produced with 0 delay.
    For example, consider the event with `incoming` `SimVar` [a, b] that have 2@1 and 2@1.
    The event has `outgoing` `SimVar` [c, d], behavior lambda a, b: [(a + b)@+1, (a - b)@+2].
    This event can happen for a = 2@1 and b = 2@1. Thus, it will happen at time 1, generating
    [3@+1, 1@+2] according to its behavior. Therefore, after the event has happened, c and d
    will have the tokens 3@2 and 1@3.

    :param _id: the identifier of the event.
    :param incoming: a list of incoming SimVar of the event.
    :param outgoing: a list of outgoing SimVar of the event
    :param guard: a function that takes as many parameters as there are incoming SimVar. The function must evaluate to True or False for all possible values of SimVar. The event can only happen for values for which the guard function evaluates to True.
    :param behavior: a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many elements as there are outgoing SimVar. The elements must be tokens that carry the resulting values and the delay with which these values become available. When the event happens, the function is performed on the incoming SimVar and the result of the function is put on the outgoing SimVar with the corresponding delays.
    """

    def __init__(self, _id, guard=None, behavior=None, incoming=None, outgoing=None):
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
        self.visualize = True

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

    def set_behavior(self, behavior):
        """
        Set the behavior.

        :param behavior: the behavior to set.
        """
        self.behavior = behavior

    def get_id(self):
        return self._id

    def __str__(self):
        return self._id

    def __repr__(self):
        return self.__str__()

    def get_visualisation(self):
        return vis.TransitionViz(self)

    def set_invisible(self):
        self.visualize = False

class SimToken:
    """
    A token SimToken, which is a possible value of a SimVar. A token has a value and the time at which this value is available in a SimVar.
    When the SimToken is used as the return value of an event behavior, the delay can be used. This represents the delay with which the value will be available.
    The value will then be available at <time of event> + <delay>.

    :param value: the value of the token.
    :param time: the time at which the value is available. 
    :param delay: should only be used when returning the token from an event behavior. The value represents the delay. The token will then be available as <time of event> + <delay>.

    """
    def __init__(self, value, time=0, delay=0):
        self.value = value
        self.time = time
        self.delay = delay

    def __eq__(self, token):
        return self.value == token.value and self.time == token.time

    def __lt__(self, token):
        if isinstance(token.value, dict) and isinstance(self.value, dict):
            return self.time < token.time or (self.time == token.time and list(self.value.values()) < list(token.value.values()))
        elif isinstance(token.value, (str, int, float, complex, bool)) and isinstance(self.value, (str, int, float, complex, bool)):
            return self.time < token.time or (self.time == token.time and self.value < token.value)
        elif isinstance(token.value, (list, tuple)) and isinstance(self.value, (list, tuple)):
            return self.time < token.time or (self.time == token.time and str(self.value) < str(token.value)) #relied on string just to impose a strict ordering
        elif isinstance(self.value, dict) and isinstance(token.value, (str, int, float, complex, bool, list, tuple)):
            return self.time < token.time or (self.time == token.time and list(self.value.values()) < [token.value])
        elif isinstance(self.value, (str, int, float, complex, bool, list, tuple)) and isinstance(token.value, dict):
            return self.time < token.time or (self.time == token.time and [self.value] < list(token.value.values()))
        elif isinstance(self.value, (list, tuple)) and isinstance(token.value, (str, int, float, complex, bool)):
            return self.time < token.time or (self.time == token.time and self.value < [token.value])
        elif isinstance(self.value, (str, int, float, complex, bool)) and isinstance(token.value, (list, tuple)):
            return self.time < token.time or (self.time == token.time and [self.value] < token.value)
        else:
            raise TypeError("Unsupported comparison between '{}' and '{}'".format(type(self.value), type(token.value)))

    def __hash__(self):
        return (self.value, self.time).__hash__()

    def __str__(self):
        result = str(self.value)
        if self.time is not None:
            result += "@" + str(self.time)
        return result

    def __repr__(self):
        return self.__str__()
    
    def copy(self):
        return SimToken(self.value, self.time)


class SimProblem:
    """
    A simulation problem SimProblem, which consists of a collection of simulation variables SimVar and a collection of simulation events SimEvent.
    The simulation has a time and a marking of SimVar. A marking is an assignment of values to SimVar variables (also see SimVar).
    The difference between a normal Python variable and a SimVar is that: (1) a SimVar can have multiple values; and (2) these values have a simulation time
    at which they become available. A SimEvent is a function that takes SimVar values as input and produces SimVar values (also see SimEvent). The difference with normal
    Python functions is that events can happen whenever its incoming SimVar parameters have a value. If a SimVar parameter has multiple values,
    it can happen on any of these values.

    :param debugging: if set to True, produces more information for debugging purposes (defaults to True).
    :param binding_priority: a function that takes a list of binding as input and returns the binding that will be selected in case there are multiple possible bindings to fire.
    """
    def __init__(self, debugging=True, binding_priority=lambda bindings: bindings[0]):
        self.places = []
        self.events = []
        self.prototypes = []
        self.id2node = dict()
        self.clock = 0
        self._debugging = debugging
        self.clock_checkpoints = dict()
        self.binding_priority = binding_priority

    def __str__(self):
        result = ""
        result += "P={"
        for i in range(len(self.places)):
            result += str(self.places[i])
            if i < len(self.places) - 1:
                result += ","
        result += "}\n"
        result += "T={"
        for i in range(len(self.events)):
            result += str(self.events[i])
            if self.events[i].guard is not None:
                result += "[" + self.events[i].guard.__name__ + "]"
            result += ":" + self.events[i].behavior.__name__
            if i < len(self.events) - 1:
                result += ","
        result += "}\n"
        arcs = []
        for t in self.events:
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
                mstr = str(p) + ":["
                ti = 0
                for token in p.marking:
                    mstr += str(token)
                    if ti < len(p.marking) - 1:
                        mstr += ", "
                    ti += 1
                markings.append(mstr + "]")
        result += "M={"
        for i in range(len(markings)):
            result += markings[i]
            if i < len(markings) - 1:
                result += ","
        result += "}"                
        return result

    def add_var(self, name, priority=lambda token: token.time):
        """
        Creates a new SimVar with the specified name as identifier. Adds the SimVar to the problem and returns it.

        :param name: a name for the SimVar.
        :param priority: a function that takes a token as input and returns a value that is used to sort the tokens in the order in which they will be processed (lower values first). The default is processing in the order of the time of the token.
        :return: a SimVar with the specified name as identifier.
        """
        # Generate and add SimVar
        result = SimVar(name, priority=priority)
        self.add_prototype_var(result)
        return result
    def add_place(*args, **kwargs):
        """
        Adds a SimVar to the problem. This function is a wrapper around add_var for people with a Petri-net background.
        """
        self = args[0]
        return self.add_var(*(args[1:]), **kwargs)

    def add_prototype_var(self, var):
        """
        Adds the SimVar to the problem. This function should only be used for prototypes.
        """
        # Check name
        name = var.get_id()
        if name in self.id2node:
            raise TypeError("Node with name " + name + " already exists. Names must be unique.")
        if name.endswith(SimVarQueue.QUEUE_SUFFIX):
            raise TypeError("Cannot create SimVar with name " + name + ". Names ending with " + SimVarQueue.QUEUE_SUFFIX + " are reserved for SimVar queues. They are automatically generated.")
        if name == SimVarTime.TIME_ID:
            raise TypeError("Cannot create SimVar with name " + name + ". " + SimVarTime.TIME_ID + " is reserved for the time variable. If you just want to get the time variable, use the .var() method instead.")

        # Add SimVar
        self.places.append(var)
        self.id2node[name] = var

    def add_prototype_event(self, event):
        """
        Adds the SimEvent to the problem. This function should only be used for prototypes.        
        """
        # Check name
        name = event.get_id()
        if name in self.id2node:
            raise TypeError("Node with name " + name + " already exists. Names must be unique.")

        # Add SimEvent
        self.events.append(event)
        self.id2node[name] = event


    def var(self, name):
        """
        Returns the SimVar with the given name.
        Raises an error if no such SimVar exists.

        :param name: the name of the SimVar.
        :return: the SimVar with the given name or an Error.
        """
        if name in self.id2node:
            if isinstance(self.id2node[name], SimVar):
                return self.id2node[name]
            else:
                raise TypeError(name + " is not a SimVar.")
        elif name == SimVarTime.TIME_ID:
            # Generate and add SimVarTime
            time_var = SimVarTime(self)
            self.places.append(time_var)
            self.id2node[time_var._id] = time_var
            return time_var
        else:
            raise LookupError("SimVar " + name + ": does not exist.")
    def place(*args, **kwargs):
        """
        Returns the SimVar with the given name. This function is a wrapper around var for people with a Petri-net background.
        """
        self = args[0]
        return self.var(*(args[1:]), **kwargs)

    def store_checkpoint(self, name):
        """
        Stores the state of the simulator as a checkpoint with the given name. The checkpoint can be restored later with restore_checkpoint.
        """
        for p in self.places:
            p.store_checkpoint(name)
        self.clock_checkpoints[name] = self.clock

    def restore_checkpoint(self, name):
        """
        Restores the state of the simulator to the checkpoint with the given name.
        """
        if name not in self.clock_checkpoints:
            raise LookupError("No checkpoint '" + name + "'.")
        for p in self.places:
            p.restore_checkpoint(name)
        self.clock = self.clock_checkpoints[name]

    def add_event(self, inflow, outflow, behavior, name=None, guard=None):
        """
        Creates a new SimEvent with the specified parameters (also see SimEvent). Adds the SimEvent to the problem and returns it.

        :param inflow: a list of incoming SimVar of the event.
        :param outflow: a list of outgoing SimVar of the event/
        :param behavior: a function that takes as many parameters as there are incoming SimVar. The function must return a list with as many elements as there are outgoing SimVar. When the event happens, the function is performed on the incoming SimVar and the result of the function is put on the outgoing SimVar.
        :param name: the identifier of the event.
        :param guard: a function that takes as many parameters as there are incoming SimVar. The function must evaluate to True or False for all possible values of SimVar. The event can only happen for values for which the guard function evaluates to True.
        :return: a SimEvent with the specified parameters.
        """

        # Check name
        t_name = name
        if t_name is None:
            if behavior.__name__ == "<lambda>":
                raise TypeError("Event name must be set or procedure behavior function must be named.")
            else:
                t_name = behavior.__name__
        if t_name in self.id2node:
            raise TypeError("Event " + t_name + ": node with the same name already exists. Names must be unique.")

        # Check inflow
        c = 0
        for i in inflow:
            if not isinstance(i, SimVar):
                raise TypeError("Event " + t_name + ": inflow with index " + str(c) + " is not a SimVar.")
            c += 1

        # Check outflow
        c = 0
        for o in outflow:
            if not isinstance(o, SimVar):
                raise TypeError("Event " + t_name + ": outflow with index " + str(o) + " is not a SimVar.")
            c += 1

        # Check behavior function
        if not callable(behavior):
            raise TypeError("Event " + t_name + ": the behavior must be a function. (Maybe you made it a function call, exclude the brackets.)")
        parameters = inspect.signature(behavior).parameters
        num_mandatory_params = sum(
            1 for p in parameters.values()
            if p.kind not in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD] # count all parameters which are not "*args" or "**kwargs"
        )
        if num_mandatory_params > len(inflow):
            raise TypeError("Event " + t_name + ": the behavior function must take as many parameters as there are input variables.")

        # Check constraint
        if guard is not None:
            if not callable(guard):
                raise TypeError("Event " + t_name + ": the constraint must be a function. (Maybe you made it a function call, exclude the brackets.)")
            parameters = inspect.signature(guard).parameters
            num_mandatory_params = sum(
                1 for p in parameters.values()
                if p.kind not in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD] # count all parameters which are not "*args" or "**kwargs"
            )
            if num_mandatory_params > len(inflow):
                raise TypeError("Event " + t_name + ": the constraint function must take as many parameters as there are input variables.")

        # Check queue operations: if the inflow is only queue vars, but the outflow is not, we post a warning.
        inflow_queues = all([isinstance(i, SimVarQueue) for i in inflow])
        outflow_queues = all([isinstance(o, SimVarQueue) for o in outflow])
        if inflow_queues and not outflow_queues:
            print("WARNING: Event " + t_name + ": has only queue variables in the inflow, but not in the outflow. This may lead to unexpected behavior, because queues do not have time, so the outflow tokens are produced at time=0.")

        # Generate and add SimEvent
        result = SimEvent(t_name, guard=guard, behavior=behavior, incoming=inflow, outgoing=outflow)
        self.events.append(result)
        self.id2node[t_name] = result

        return result
    def add_transition(*args, **kwargs):
        """
        Creates a new SimEvent with the specified parameters. This function is a wrapper around add_event for people with a Petri-net background.
        """
        self = args[0]
        return self.add_event(*(args[1:]), **kwargs)

    def add_prototype(self, prototype):
        if len(prototype.places) == 0 and len(prototype.events) == 0:
            raise TypeError("Prototype " + prototype.name + ": does not have any variables or events. That should not be possible, please notify the developer.")
        for place in prototype.places:
            if place not in self.places:
                raise TypeError("Prototype " + prototype.name + ": did not add all its places to the model. That should not be possible, please notify the developer.")
        for event in prototype.events:
            if event not in self.events:
                raise TypeError("Prototype " + prototype.name + ": did not add all its events to the model. That should not be possible, please notify the developer.")
        if prototype.get_id() in self.id2node:
            raise TypeError("Prototype " + prototype.name + ": node with the same name already exists. Names must be unique.")
        self.prototypes.append(prototype)

    def set_binding_priority(self, func):
        """
        Sets the binding priority function.

        :param func: a function that takes a list of binding as input and returns the binding that will be selected in case there are multiple possible bindings to fire.
        """
        self.binding_priority = func

    @staticmethod
    def tokens_combinations(event):
        """
        Creates a list of token combinations that are available to the specified event.
        These are combinations of tokens that are on the incoming SimVar of the event.
        For example, if a event has incoming SimVar a and b with tokens 1@0 on a and 2@0, 3@0 on b,
        the possible combinations are [(a, 1@0), (b, 2@0)] and [(a, 1@0), (b, 3@0)]

        :param event: the event to return the token combinations for.
        :return: a list of lists, each of which is a token combination.
        """
        # create all possible combinations of incoming token values
        bindings = [[]]
        for place in event.incoming:
            new_bindings = []
            for token in place.marking:  # get set of colors in incoming place
                for binding in bindings:
                    new_binding = binding.copy()
                    new_binding.append((place, token))
                    new_bindings.append(new_binding)
            bindings = new_bindings
        return bindings

    def event_bindings(self, event):
        """
        Calculates the set of bindings that enables the given event.
        Each binding is a tuple ([(place, token), (place, token), ...], time) that represents a single enabling binding.
        A binding is
        a possible token combination (see token_combinations), for which the event's
        guard function evaluates to True. In case there is no guard function, any combination is also a binding.
        The time is the time at which the latest token is available.
        For example, if a event has incoming SimVar a and b with tokens 1@2 on a and 2@3, 3@1 on b,
        the possible bindings are ([(a, 1@2), (b, 2@3)], 3) and ([(a, 1@2), (b, 3@1)], 2)

        :param event: the event for which to calculate the enabling bindings.
        :return: list of tuples ([(place, token), (place, token), ...], time)
        """
        if len(event.incoming) == 0:
            raise Exception("Though it is strictly speaking possible, we do not allow events like '" + str(self) + "' without incoming arcs.")

        bindings = self.tokens_combinations(event)

        # a binding must have all incoming places
        nr_incoming_places = len(event.incoming)
        new_bindings = []
        for binding in bindings:
            if len(binding) == nr_incoming_places:
                new_bindings.append(binding)
        bindings = new_bindings

        # if a event has a guard, only bindings are enabled for which the guard evaluates to True
        result = []
        for binding in bindings:
            variable_values = []
            time = None
            for (place, token) in binding:
                variable_values.append(token.value)
                if time is None or token.time > time:
                    time = token.time
            enabled = True
            if event.guard is not None:
                try:
                    enabled = event.guard(*variable_values)
                except Exception as e:
                    raise TypeError("Event " + event + ": guard generates exception for values " + str(variable_values) + ".") from e
                if self._debugging and not isinstance(enabled, bool):
                    raise TypeError("Event " + event + ": guard does evaluate to a Boolean for values " + str(variable_values) + ".")
            if enabled:
                result.append((binding, time))
        return result

    def bindings(self):
        """
        Calculates the set of timed bindings that is enabled over all events in the problem.
        Each binding is a tuple ([(place, token), (place, token), ...], time, event) that represents a single enabling binding.
        If no timed binding is enabled at the current clock time, updates the current clock time to the earliest time at which there is.
        :return: list of tuples ([(place, token), (place, token), ...], time, event)
        """
        timed_bindings = []
        min_enabling_time = None
        for t in self.events:
            for (binding, time) in self.event_bindings(t):
                timed_bindings.append((binding, time, t))
                if min_enabling_time is None or time < min_enabling_time:
                    min_enabling_time = time
        # timed bindings are only enabled if they have time <= clock
        # if there are no such bindings, set the clock to the earliest time at which there are
        if min_enabling_time is not None and min_enabling_time > self.clock:
            self.clock = min_enabling_time
            # We now also need to update the bindings, because the SimVarTime may have changed and needs to be updated.
            # TODO This is inefficient, because we are recalculating all bindings, while we only need to recalculate the ones that have SimVarTime in their inflow.
            timed_bindings = [] 
            for t in self.events:
                for (binding, time) in self.event_bindings(t):
                    timed_bindings.append((binding, time, t))

        # now return the untimed bindings + the timed bindings that have time <= clock
        return [(binding, time, t) for (binding, time, t) in timed_bindings if time <= self.clock]

    def fire(self, timed_binding):
        """
        Fires the specified timed binding.
        Binding is a tuple ([(place, token), (place, token), ...], time, event)
        """
        (binding, time, event) = timed_binding

        # process incoming places:
        variable_assignment = []
        for (place, token) in binding:
            # remove tokens from incoming places
            place.remove_token(token)
            # assign values to the variables on the arcs
            variable_assignment.append(token.value)

        # calculate the result of the behavior of the event
        try:
            result = event.behavior(*variable_assignment)
        except Exception as e:
            raise TypeError("Event " + str(event) + ": behavior function generates exception for values " + str(variable_assignment) + ".") from e
        if self._debugging:
            if type(result) != list:
                raise TypeError("Event " + str(event) + ": behavior function does not generate a list for values " + str(variable_assignment) + ".")
            if len(result) != len(event.outgoing):
                raise TypeError("Event " + str(event) + ": behavior function does not generate as many values as there are output variables for values " + str(variable_assignment) + ".")
            i = 0
            for r in result:
                if r is not None:
                    if isinstance(event.outgoing[i], SimVarQueue):
                        if not isinstance(r, list):
                            raise TypeError("Event " + str(event) + ": does not generate a queue for variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ".")
                    else:
                        if not isinstance(r, SimToken):
                            raise TypeError("Event " + str(event) + ": does not generate a token for variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ".")
                        if not (type(r.delay) is int or type(r.delay) is float):
                            raise TypeError("Event " + str(event) + ": does not generate a numeric value for the delay of variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ".")
                        if not (type(r.time) is int or type(r.time) is float):
                            raise TypeError("Event " + str(event) + ": does not generate a numeric value for the time of variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ".")
                i += 1

        for i in range(len(result)):
            if result[i] is not None:
                if isinstance(event.outgoing[i], SimVarQueue):
                    event.outgoing[i].add_token(result[i])
                else:
                    if result[i].time > 0 and result[i].delay == 0:
                        raise TypeError("Deprecated functionality: Event " + str(event) + ": generates a token with a delay of 0, but a time > 0, for variable " + str(event.outgoing[i]) + " for values " + str(variable_assignment) + ". It seems you are using the time of the token to represent the delay.")
                    token = SimToken(result[i].value, time=self.clock + result[i].delay)
                    event.outgoing[i].add_token(token)

    def step(self):
        """
        Executes a single step of the simulation.
        If multiple events can happen, one is selected at random.
        Returns the binding that happened, or None if no event could happen.
        """
        bindings = self.bindings()
        if len(bindings) > 0:
            timed_binding = self.binding_priority(bindings)
            self.fire(timed_binding)
            return timed_binding
        return None

    def simulate(self, duration, reporter=None):
        """
        Executes a simulation run for the problem for the specified duration.
        A simulation run executes events until this is no longer possible, or until the specified duration.
        If at any moment multiple events can happen, one is selected at random.
        At the end of the simulation run, the problem is in the state that is the result of the run.
        If the reporter is set, its callback function is called with parameters (binding, time, event)
        each time a event happens (for a binding at a moment in simulation time).

        :param duration: the duration of the simulation.
        :param reporter: a class that implements a callback function, which is called each time a event happens. reporter can also be a list of reporters, in which case the callback function of each reporter is called.
        """
        active_model = True
        while self.clock <= duration and active_model:
            bindings = self.bindings()
            if len(bindings) > 0:
                timed_binding = self.binding_priority(bindings)
                self.fire(timed_binding)
                if reporter is not None:
                    if type(reporter) == list:
                        for r in reporter:
                            r.callback(timed_binding)
                    else:
                        reporter.callback(timed_binding)
            else:
                active_model = False


def event(sim_problem: SimProblem, inflow: list, outflow: list, guard=None):
    """
    A decorator that can be used to turn a Python function into a SimEvent.
    The event will be added to the specified sim_problem.
    If they do not yet exist, SimVar will be added for each parameter of the Python function and for each element in outflow.
    The parameters of the function will be treated as inflow variables of the SimEvent (by name).
    The elements of outflow must be names of SimVar and will be treated as outflow variables of the SimEvent (by name).
    The name of the SimEvent will be the name of the Python function.

    :param sim_problem: the SimProblem to which to add the SimEvent.
    :param inflow: a list of names of inflow variables. Just there for documentation purposes, it is not being used.
    :param outflow: a list of names of outflow variables.
    :param guard: an optional guard for the SimEvent.
    :return: the Python function.
    """
    def decorator_event(func):
        parameters = inspect.signature(func).parameters
        for parameter in list(parameters.keys()) + outflow:
            if parameter not in sim_problem.id2node:
                sim_problem.add_var(parameter)
        inflow_svars = [sim_problem.id2node[parameter] for parameter in parameters]
        outflow_svars = [sim_problem.id2node[parameter] for parameter in outflow]
        sim_problem.add_event(inflow_svars, outflow_svars, func, guard=guard)
        return func
    return decorator_event
