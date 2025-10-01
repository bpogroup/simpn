"""
This module describes a set of meta classes that allow for subclassing 
to create a simulation using the prototypes for a BPMN model.

To use these helper classes, import one of the desired prototype helpers,
or import `BPMN` to use the general class which will route to the desired
helper class for a prototype.
"""

from simpn.prototypes import *
from simpn.simulator import SimProblem

from typing import List, Literal, Union
from abc import abstractmethod

class HelperBPMNTask(BPMNTask):
    """
    A helper class to create a `BPMNTask` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields and functions. After the defintion is created a new 
    prototype instance will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `outgoing`:
        A list of `SimVar` to pull tokens from to trigger the task.
    :fieldname `outgoing`:
        A list of `SimVar` to depack the tokens returned by the behaviour
        function into.

    ^^^
    Required class functions
    ^^^
    :fieldname `behaviour`:
        A function determines how long each token is held by the BPMNTask.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    @staticmethod
    def __create__(cls, **kwargs):
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or outgoing is None or name is None:
            # Don't register the abstract base class
            if cls.__name__ == 'HelperBPMNTask':
                return
            raise ValueError("You must define static class variables: model, incoming, outgoing, and name in your HelperBPMNTask subclass.")
        # Fetch static/class methods
        behaviour = getattr(cls, 'behaviour', None)
        if behaviour is None or not callable(behaviour):
            raise NotImplementedError("You must implement a static/class method 'behaviour(*args)' in your HelperBPMNTask subclass.")
        guard = getattr(cls, 'guard', None)
        outgoing_behaviour = getattr(cls, 'outgoing_behaviour', None)
        # If not implemented, set to None
        if guard is not None and not callable(guard):
            guard = None
        if outgoing_behaviour is not None and not callable(outgoing_behaviour):
            outgoing_behaviour = None
        # Register the task with the model by instantiating the subclass
        HelperBPMNTask(model, incoming, outgoing, name, behaviour, guard=guard, outgoing_behavior=outgoing_behaviour)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Fetch static/class variables
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or outgoing is None or name is None:
            # Don't register the abstract base class
            if cls.__name__ == 'HelperBPMNTask':
                return
            raise ValueError("You must define static class variables: model, incoming, outgoing, and name in your HelperBPMNTask subclass.")
        # Fetch static/class methods
        behaviour = getattr(cls, 'behaviour', None)
        if behaviour is None or not callable(behaviour):
            raise NotImplementedError("You must implement a static/class method 'behaviour(*args)' in your HelperBPMNTask subclass.")
        guard = getattr(cls, 'guard', None)
        outgoing_behaviour = getattr(cls, 'outgoing_behaviour', None)
        # If not implemented, set to None
        if guard is not None and not callable(guard):
            guard = None
        if outgoing_behaviour is not None and not callable(outgoing_behaviour):
            outgoing_behaviour = None
        # Register the task with the model by instantiating the subclass
        cls(model, incoming, outgoing, name, behaviour, guard=guard, outgoing_behavior=outgoing_behaviour)

    @staticmethod
    @abstractmethod
    def behaviour(*args):
        pass

class HelperBPMNStart(BPMNStartEvent):
    """
    A helper class to create a `BPMNStartEvent` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields and functions. After the defintion is created a new 
    prototype instance will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `outgoing`:
        A list of `SimVar` that to put tokens into once the arrival time
        occurs.

    ^^^
    Required class functions
    ^^^
    :fieldname `interarrival_time`:
        A function that returns the delay between the next token arrival.
    """
    model = None
    outgoing = None
    name = None
    amount = None

    @staticmethod
    def __create__(cls, **kwargs):
        model = getattr(cls, 'model', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        amount = getattr(cls, 'amount', 1)
        behaviour = getattr(cls, 'behaviour', None)
        if model is None or outgoing is None or name is None:
            if cls.__name__ == 'HelperBPMNStart':
                return
            raise ValueError("You must define static class variables: model, outgoing, and name in your HelperBPMNStart subclass.")
        interarrival_time = getattr(cls, 'interarrival_time', None)
        if interarrival_time is None or not callable(interarrival_time):
            raise NotImplementedError("You must implement a static/class method 'interarrival_time()' in your HelperBPMNStart subclass.")
        # Register the start event with the model by instantiating BPMNStartEvent
        HelperBPMNStart(model, [], outgoing, name, interarrival_time, behaviour)

    def __init_subclass__(cls, **kwargs):
        model = getattr(cls, 'model', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        amount = getattr(cls, 'amount', 1)
        if model is None or outgoing is None or name is None:
            if cls.__name__ == 'HelperBPMNStart':
                return
            raise ValueError("You must define static class variables: model, outgoing, and name in your HelperBPMNStart subclass.")
        interarrival_time = getattr(cls, 'interarrival_time', None)
        if interarrival_time is None or not callable(interarrival_time):
            raise NotImplementedError("You must implement a static/class method 'interarrival_time()' in your HelperBPMNStart subclass.")
        # Register the start event with the model by instantiating BPMNStartEvent
        cls(model, [], outgoing, name, interarrival_time)

    @staticmethod
    @abstractmethod
    def interarrival_time():
        pass

class HelperBPMNEnd(BPMNEndEvent):
    """
    A helper class to create a `BPMNEndEvent` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields and functions. After the defintion is created a new 
    prototype instance will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `incoming`:
        A list of `SimVar` that require tokens to trigger the event.
    """
    model = None
    incoming = None
    name = None

    @staticmethod
    def __create__(cls, **kwargs):
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or name is None:
            if cls.__name__ == 'HelperBPMNEnd':
                return
            raise ValueError("You must define static class variables: model, outgoing, and name in your HelperBPMNStart subclass.")
        # Register the start event with the model by instantiating BPMNStartEvent
        HelperBPMNEnd(model, incoming, [], name)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or name is None:
            if cls.__name__ == 'HelperBPMNEnd':
                return
            raise ValueError("You must define static class variables: model, outgoing, and name in your HelperBPMNStart subclass.")
        # Register the start event with the model by instantiating BPMNStartEvent
        cls(model, incoming, [], name)

class HelperBPMNIntermediateEvent(BPMNIntermediateEvent):
    """
    A helper class to create a `BPMNIntermediateEvent` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields and functions. After the defintion is created a new 
    prototype instance will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `incoming`:
        A list of `SimVar` that require tokens to trigger the event.
    :fieldname `outgoing`:
        A list of `SimVar` to place the tokens into.

    ^^^
    Required class functions
    ^^^
    :fieldname `behaviour`:
        A function that takes tokens matching the length of `incoming` and
        returns a list of tokens to place into `outgoing` places.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    @staticmethod
    def __create__(cls, **kwargs):
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or outgoing is None or name is None:
            if cls.__name__ == 'HelperBPMNIntermediateEvent':
                return
            raise ValueError("You must define static class variables: model, incoming, outgoing, and name in your HelperBPMNIntermediateEvent subclass.")
        behaviour = getattr(cls, 'behaviour', None)
        if behaviour is None or not callable(behaviour):
            raise NotImplementedError("You must implement a static/class method 'behaviour(*args)' in your HelperBPMNIntermediateEvent subclass.")
        # Register the intermediate event with the model by instantiating BPMNIntermediateEvent
        HelperBPMNIntermediateEvent(model, incoming, outgoing, name, behaviour)


    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        incoming = getattr(cls, 'incoming', None)
        outgoing = getattr(cls, 'outgoing', None)
        name = getattr(cls, 'name', None)
        if model is None or incoming is None or outgoing is None or name is None:
            if cls.__name__ == 'HelperBPMNIntermediateEvent':
                return
            raise ValueError("You must define static class variables: model, incoming, outgoing, and name in your HelperBPMNIntermediateEvent subclass.")
        behaviour = getattr(cls, 'behaviour', None)
        if behaviour is None or not callable(behaviour):
            raise NotImplementedError("You must implement a static/class method 'behaviour(*args)' in your HelperBPMNIntermediateEvent subclass.")
        # Register the intermediate event with the model by instantiating BPMNIntermediateEvent
        cls(model, incoming, outgoing, name, behaviour)

    @staticmethod
    @abstractmethod
    def behaviour(*args):
        pass

class HelperBPMNExclusiveSplit(BPMNExclusiveSplitGateway):
    """
    A helper class to create a `BPMNExclusiveSplitGateway` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields. After the defintion is created a new prototype instance
    will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `incoming`:
        A list of `SimVar` with a single place to pull tokens from.
    :fieldname `outgoing`:
        A list of possible `SimVar` to place the tokens into.

    ^^^
    Required class functions
    ^^^
    :fieldname `choice`:
        A function that takes a token from `incoming` and
        returns a list of the same length of `outgoing` where 
        some elements are `None` and some are tokens place into `outgoing` 
        places.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    @staticmethod
    def __create__(cls, **kwargs):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        if not hasattr(cls, "choice"):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define a 'choice' method.")
        # Register the gateway automatically
        HelperBPMNExclusiveSplit(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
            cls.choice,
            **kwargs
        )

    def __init_subclass__(cls):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        if not hasattr(cls, "choice"):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define a 'choice' method.")
        # Register the gateway automatically
        cls(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
            cls.choice
        )

    @staticmethod
    @abstractmethod
    def choice(c):
        pass

class HelperBPMNExclusiveJoin(BPMNExclusiveJoinGateway):
    """
    A helper class to create a `BPBPMNExclusiveJoinGatewayMN` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields. After the defintion is created a new prototype instance
    will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `incoming`:
        A list of possible `SimVar` to pull tokens from for joining.
    :fieldname `outgoing`:
        A list of `SimVar` with a single element to place the joined tokens into.
    """
    model = None
    incoming = None
    outgoing = None
    name = None

    @staticmethod
    def __create__(cls, **kwargs):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        # Register the gateway automatically
        HelperBPMNExclusiveJoin(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name
        )

    def __init_subclass__(cls):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        # Register the gateway automatically
        cls(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name
        )

class HelperResourcePool:
    """
    A helper subclass instance to make a resource pool within the simulation.
    Basically, adds a SimVar place with an `amount` of tokens for use. But, 
    uses a thin wrapper around SimVar for visualiusation of the place and edges.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields. After the defintion is created a new prototype instance
    will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `amount`:
        The amount of tokens to initially place in this resource pool. Tokens
        are generated using the name of the place plus an integer identifier
    """
    name:str=None 
    model:SimProblem=None 
    amount:int=None

    def __create__(cls, **kwargs):
        if any(hasattr(cls, attr) and getattr(cls, attr) is None for attr in ["name","model","amount"]):
            raise ValueError('Missing values for the following key attributes: ["name","model","amount"]')
        place = cls.model.add_place(cls.name)
        for i in range(cls.amount):
            place.put(f"{cls.name}-{i+1}") 
        place._resource_pool = True

    def __init_subclass__(cls, **kwargs):
        if not all(hasattr(cls, name) and getattr(cls, name) is not None for name in ["name","model","amount"]):
            raise ValueError('Missing values for the following key attributes: ["name","model","amount"]')
        place = cls.model.add_place(cls.name)
        for i in range(cls.amount):
            place.put(f"{cls.name}-{i+1}")
        place._resource_pool = True

class HelperBPMNFlow(BPMNFlow):
    """
    A helper class to create a `BPMNFlow` prototype. Which is a `SimVar`
    with a different visualisation

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields. After the defintion is created a new prototype instance
    will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    
    ^^^
    Optional class fields
    ^^^
    :fieldname `amount`:
    The amount of tokens to initially place in this resource pool. Tokens
    are generated using the name of the place plus an integer identifier
    """

    def __create__(cls, **kwargs):
        if any(hasattr(cls, attr) and getattr(cls, attr) is None for attr in ["name","model"]):
            raise ValueError('Missing values for the following key attributes: ["name","model"]')
        place = BPMNFlow(cls.model, cls.name)
        if hasattr(cls, 'amount'):
            for i in range(cls.amount):
                place.put(f"{cls.name}-{i+1}") 

    def __init_subclass__(cls, **kwargs):
        if not all(hasattr(cls, name) and getattr(cls, name) is not None for name in ["name","model"]):
            raise ValueError('Missing values for the following key attributes: ["name","model"]')
        place = BPMNFlow(cls.model, cls.name)
        if hasattr(cls, 'amount'):
            for i in range(cls.amount):
                place.put(f"{cls.name}-{i+1}") 

class HelperBPMNParallelSplit(BPMNParallelSplitGateway):
    """
    A helper class to create a `BPMNParallelSplitGateway` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields. After the defintion is created a new prototype instance
    will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `incoming`:
        A list of `SimVar` with a single place to pull tokens from.
    :fieldname `outgoing`:
        A list of  `SimVar` to place 'copied' tokens into.
    """

    @staticmethod
    def __create__(cls, **kwargs):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        BPMNParallelSplitGateway(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
            **kwargs
        )

    def __init_subclass__(cls):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        # Register the gateway automatically
        cls(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
        )

class HelperBPMNParallelJoin(BPMNParallelJoinGateway):
    """
    A helper class to create a `BPMNParallelJoinGateway` prototype.

    ---
    Usage
    ---
    Create a new class definition that inherits from this class with the
    following fields. After the defintion is created a new prototype instance
    will be recorded in the simulation problem.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    :fieldname `incoming`:
        A list of `SimVar` that each require one copy of a token to trigger
        the join.
    :fieldname `outgoing`:
        A list of a single `SimVar` to place the reocmbined token into.

    ^^^^
    Optional class functions
    ^^^^
    :fieldname `behaviour`:
        A function that takes the parallel tokens and returns a list of 
        `Simtoken` to place into outgoing. Used to collect data attributes
        from parallel actions back into a single token.
    """

    @staticmethod
    def __create__(cls, **kwargs):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        if hasattr(cls, 'behaviour'):
            behaviour = cls.behaviour
        else:
            behaviour = None
        # Register the gateway automatically
        BPMNParallelJoinGateway(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
            behaviour,
            **kwargs
        )

    def __init_subclass__(cls):
        if not all(hasattr(cls, attr) for attr in ("model", "incoming", "outgoing", "name")):
            raise AttributeError("HelperBPMNExclusiveSplitGateway subclasses must define model, incoming, outgoing, and name class variables.")
        if hasattr(cls, 'behaviour'):
            behaviour = cls.behaviour
        else:
            behaviour = None
        # Register the gateway automatically
        cls(
            cls.model,
            cls.incoming,
            cls.outgoing,
            cls.name,
            behaviour
        )

TYPES = {
    "start" : HelperBPMNStart.__create__,
    "end" : HelperBPMNEnd.__create__,
    "task" : HelperBPMNTask.__create__,
    "gat-ex-split" : HelperBPMNExclusiveSplit.__create__,
    "gat-ex-join" : HelperBPMNExclusiveJoin.__create__,
    "event" : HelperBPMNIntermediateEvent.__create__,
    "resource-pool" : HelperResourcePool.__create__,
    "flow" : HelperBPMNFlow.__create__,
    "gat-para-split" : HelperBPMNParallelSplit.__create__,
    "gat-para-join" : HelperBPMNParallelJoin.__create__

}
TYPE_NAMES = Literal["start", "end", "task", "gat-ex-split",
                     "gat-ex-join", "event", "resource-pool",
                     "flow", "gat-para-split", "gat-para-join"]

class BPMN:
    """
    A synatical sugar wrapper class to handle making a specific bpmn helper.
    To use this class, create a class definition that inherits from this 
    class and include the approciate fields to make a new prototype in the
    given `SimProblem`.

    ^^^^
    Required class fields
    ^^^^
    :fieldname `type`: 
        a string to denote what prototype should be made.
    :expected values: 
        `start`, `end`, `task`, `gat-ex-split`, `gat-ex-join`, `event`, 
        `resource-pool`, `flow`, `gat-para-split`, `gat-para-join`
    :fieldname `model`:
        The `SimProblem` to add the prototype to.
    :fieldname `name`:
        A unique identifier for the new prototype. 
    ^^^
    Optional class fields
    ^^^
    :fieldname `incoming`:
        A list of strings or `SimVar`'s to use as incoming. If a string is 
        passed then that string will be used to either make a `SimVar` or
        look one up in the given model.
    :fieldname `outgoing`:
        A list of strings or `SimVar`'s to use as outoing. Similar to above.
    
    For the fields needed for each individual helper, please check the 
    helper class definition.

    ^^^
    Examples of usage
    ^^^
    .. code-block:: python
        class Start(BPMN):
            type="start"
            model=agency
            name="arrive"
            amount=1
            outgoing=["waiting"]

            def interarrival_time():
                return exp(1/10)
            
        class Scan(BPMN):
            type="task"
            model=agency
            name="scan"
            incoming=["waiting", "employee"]
            outgoing=["done", "employee"]

            def behaviour(c, r):
                return [SimToken((c, r), delay=exp(1/9))]
            
        class End(BPMN):
            type="end"
            model=agency
            name="complete"
            incoming=["done"]
    """
    
    type:TYPE_NAMES=None 
    model:SimProblem=None
    name:str=None
    incoming:List[Union[str,SimVar]]=None
    outgoing:List[Union[str,SimVar]]=None
    guard=None 

    def __init_subclass__(cls, **kwargs):
        if not all(hasattr(cls, attr) and getattr(cls, attr) is not None for attr in ("type", "model", "name")):
            raise ValueError("Missing required attributes for BPMN construct : ['model', 'name', 'type']")
        # handle outgoing strings
        if hasattr(cls, 'outgoing') and cls.outgoing != None:
            for i,val in enumerate(cls.outgoing):
                if isinstance(val, str):
                    if val in cls.model.id2node.keys():
                        cls.outgoing[i] = cls.model.id2node[val]
                    else:
                        cls.outgoing[i] = BPMNFlow(cls.model, val)# cls.model.add_var(val)
        # handle incoming strings
        if hasattr(cls, 'incoming') and cls.incoming != None:
            for i,val in enumerate(cls.incoming):
                if isinstance(val, str):
                    if val in cls.model.id2node.keys():
                        cls.incoming[i] = cls.model.id2node[val]
                    else:
                        cls.incoming[i] = BPMNFlow(cls.model, val)
        tasker = TYPES[cls.type]
        tasker(cls)

