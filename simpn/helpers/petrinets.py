"""
This file describes simple wrappers around `SimVar` and `SimEvent` 
to make places and transitions for a Petri net.
"""

from simpn.simulator import SimProblem, SimVar

class Place:
    """
    Helper class to make a place in a `SimProblem`. A thin wrapper around
    the needed calls on a known problem to make a `SimVar`.

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
    The amount of tokens to initially placed in this place. Tokens
    are generated using the name of the place plus an integer identifier

    ^^^
    Example usage
    ^^^

    .. code-block :: python
        class Home(Place):
            name="Home"
            model=problem
            amount=5
    """

    @staticmethod
    def __create__(cls, **kwargs):
        if any(hasattr(cls, attr) and getattr(cls, attr) is None for attr in ["name","model"]):
            raise ValueError('Missing values for the following key attributes: ["name","model"]')
        place = cls.model.add_var(cls.name)
        if hasattr(cls, 'amount'):
            for i in range(cls.amount):
                place.put(f"{cls.name}-{i+1}") 

    def __init_subclass__(cls, **kwargs):
        if any(hasattr(cls, name) and getattr(cls, name) is None for name in ["name","model"]):
            raise ValueError('Missing values for the following key attributes: ["name","model"]')
        place = cls.model.add_var(cls.name)
        if hasattr(cls, 'amount'):
            for i in range(cls.amount):
                place.put(f"{cls.name}-{i+1}") 

class Transition:
    """
    Helper class to make a transition in a `SimProblem`. A thin wrapper around
    the needed calls on a known problem to make a `SimEvent`.

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
    :fieldname `outgoing`:
        A list of `SimVar` or `str` to pull tokens from to trigger the task.
        If a `str` is passed, the place will be looked up or made beforehand.
    :fieldname `outgoing`:
        A list of `SimVar` or `str` to place tokens into from the behaviour
        function.
        If a `str` is passed, the place will be looked up or made beforehand.
    
    ^^^
    Required class functions
    ^^^
    :fieldname `behaviour`:
        A function taking tokens from `incoming` and returns a list of tokens
        to place into `outgoing`.

    ^^^
    Example usage
    ^^^

    .. code-block :: python
        class Drive(Transition):
            name="Drive"
            model=problem
            incoming=["Home"]
            outgoing=["Work"]

            def behaviour(h):
                return [SimToken(h, delay=5)]
    """

    model:SimProblem=None 
    name=None 
    incoming=None 
    outgoing=None 

    @staticmethod
    def __create__(cls, **kwargs):
        if any(hasattr(cls, attr) and getattr(cls, attr) is None for attr in ["name","model","incoming", "outgoing"]):
            raise ValueError('Missing values for the following key attributes: ["name","model","incoming", "outgoing"]')
        incoming = []
        for inc in cls.incoming:
            if isinstance(inc, str):
                try:
                    inc = cls.model.var(inc) 
                except Exception as e:
                    inc = cls.model.add_var(inc)
                finally:
                    incoming.append(inc) 
            elif isinstance(inc, SimVar):
                incoming.append(inc)
            else:
                raise ValueError(f"Unknown type provided in incoming :: {inc=}, of {type(inc)=}")
        outgoing = []
        for inc in cls.outgoing:
            if isinstance(inc, str):
                try:
                    inc = cls.model.var(inc) 
                except Exception as e:
                    inc = cls.model.add_var(inc)
                finally:
                    outgoing.append(inc) 
            elif isinstance(inc, SimVar):
                outgoing.append(inc)
            else:
                raise ValueError(f"Unknown type provided in outgoing :: {inc=}, of {type(inc)=}")
        if not hasattr(cls, 'behaviour'):
            raise ValueError("Missing behaviour function on class.")
        behaviour = cls.behaviour 
        name = cls.name 
        cls.model.add_event(
            incoming,
            outgoing,
            behaviour,
            name
        )

    def __init_subclass__(cls, **kwargs):
        if any(hasattr(cls, attr) and getattr(cls, attr) is None for attr in ["name","model","incoming", "outgoing"]):
            raise ValueError('Missing values for the following key attributes: ["name","model","incoming", "outgoing"]')
        incoming = []
        for inc in cls.incoming:
            if isinstance(inc, str):
                try:
                    inc = cls.model.var(inc) 
                except Exception as e:
                    inc = cls.model.add_var(inc)
                finally:
                    incoming.append(inc)
            elif isinstance(inc, SimVar):
                incoming.append(inc)
            else:
                raise ValueError(f"Unknown type provided in incoming :: {inc=}, of {type(inc)=}")
        outgoing = []
        for inc in cls.outgoing:
            if isinstance(inc, str):
                try:
                    inc = cls.model.var(inc) 
                except Exception as e:
                    inc = cls.model.add_var(inc)
                finally:
                    outgoing.append(inc) 
            elif isinstance(inc, SimVar):
                outgoing.append(inc)
            else:
                raise ValueError(f"Unknown type provided in outgoing :: {inc=}, of {type(inc)=}")
        if not hasattr(cls, 'behaviour'):
            raise ValueError("Missing behaviour function on class.")
        behaviour = cls.behaviour 
        name = cls.name 
        cls.model.add_event(
            incoming,
            outgoing,
            behaviour,
            name
        )

