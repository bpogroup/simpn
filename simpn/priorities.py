"""
This module contains some predefined priority functions for use in BPMN models.
"""

import random
from typing import Dict, Collection, Protocol
from abc import abstractmethod
from copy import deepcopy
from simpn.simulator import SimToken


class PriorityFunction(Protocol):
    """
    Behaviour protocol for priority functions.
    """

    @abstractmethod
    def __call__(self, bindings: Collection) -> object:
        """
        Finds the binding with the highest priority.
        Uses random selection if multiple bindings have the
        same priority.

        :param bindings: A collection of bindings to evaluate.
        :return: The binding with the highest priority.
        """
        pass

    @abstractmethod
    def find_priority(self, token: SimToken) -> int:
        """
        Finds the priority of a token based on priority mechanism.
        Useful for wanting to prioritise tokens associated with a SimVar.

        :param token: The token to evaluate.
        :return: The priority index of the token. Lower index means higher priority.
        """
        pass


class FirstClassPriority(PriorityFunction):
    """
    A priority function that assigns higher priority to bindings based on
    the number of tokens in binding with a classifying attribute.
    Further, priority can be given to specific values of the attribute.
    For instance, we can give higher priority to 'gold' customers over 'silver'
    customers. This priority function ensures that any binding that has a 'gold'
    member will be actioned first over bindings that only have 'silver' or
    'bronze'.

    :param class_attr: The attribute used for classifying tokens.
    :param priority_ordering: An ordered collection defining the priority of
        attribute values. Higher index means higher priority. All bindings with at
        least one token having the highest priority attribute value will be given
        the highest priority.

    The class is a callable that takes a collection of bindings and returns the binding
    with the highest priority based on the specified attribute and priority map.

    .. methods::
        __call__(bindings):
         Finds the binding with the highest priority.
         Useful for handling prioritisation in SimProblems.

        find_priority(tok):
         Finds the priority of a token based on the classifying attribute.
         Useful for wanting to prioritise tokens associated with a SimVar.

    ^^^^^
    Example:
    ^^^^^
    .. code-block:: python
        priority = FirstClassPriority(
            class_attr='type',
            priority_ordering=['gold', 'silver', 'bronze']
        )
        # returns the highest priority binding of bindings.
        priority = priority(bindings)

        # sorts the tokens based on the classifying attribute.
        SimVar("foo", priority=priority.find_priority)
    """

    def __init__(self, class_atr: str, priority_ordering: Collection[object]):
        self.attr = class_atr
        self.priorities = deepcopy(priority_ordering)

    def find_priority(self, token: SimToken) -> int:
        attr_val = None
        if hasattr(token.value, self.attr):
            attr_val = getattr(token.value, self.attr)

        if attr_val in self.priorities:
            return self.priorities.index(attr_val)
        return len(self.priorities)

    def __call__(self, bindings: Collection) -> object:

        def get_values(binding):
            return [val for val in binding[0][0] if isinstance(val, SimToken)]

        def find_priority(binding):
            values = get_values(binding)
            classes = []

            for val in values:
                if isinstance(val.value, (tuple, list)):
                    for item in val.value:
                        classes.append(self.find_priority(SimToken(item)))
                else:
                    classes.append(self.find_priority(val))

            return min(classes) if classes else len(self.priorities)

        # Find the maximum priority bindings
        groups = [[] for _ in range(len(self.priorities) + 1)]

        for binding in bindings:
            priority = find_priority(binding)
            groups[priority].append(binding)

        for group in groups:
            if group:
                highest_priority_bindings = group
                break

        return random.choice(highest_priority_bindings)


class WeightedFirstClassPriority(PriorityFunction):
    """
    A priority function that assigns priority based on
    weighted class numbers.
    """

    def __init__(self, weights):
        self.weights = weights

    def __call__(self, *args, **kwds):
        pass


class NearestToCompletionPriority(PriorityFunction):
    """
    A priority function that assigns higher priority to tasks that are nearest
    to completion.
    """

    def __call__(self, *args, **kwds):
        pass


class WeightedTaskPriority(PriorityFunction):
    """
    A priority function that assigns priority based on weights between tasks.
    """

    def __init__(self, weights):
        self.weights = weights

    def __call__(self, *args, **kwds):
        pass
