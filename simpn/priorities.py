"""
This module contains some predefined priority functions for use in BPMN models.
"""

import random
from typing import Dict, Collection, Protocol
from abc import abstractmethod
from copy import deepcopy
from simpn.simulator import SimToken, SimTokenValue


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
    def find_priority(self, token: SimToken) -> float:
        """
        Finds the priority of a token based on priority mechanism.
        Useful for wanting to prioritise tokens associated with a SimVar.
        A lower priority means that that token should have higher priority
        over over tokens.

        :param token: The token to evaluate.
        :return: The priority index of the token. Lower index means higher priority.
        """
        pass

    def get_values(self, binding) -> Collection:
        """
        Helper function to extract SimTokens from a binding.
        """
        return [val for val in binding[0][0] if isinstance(val, SimToken)]

    def get_event(self, binding) -> Collection:
        """
        Helper function to extract the event of a binding.
        """
        return binding[-1]


class FirstClassPriority(PriorityFunction):
    """
    A priority function that assigns higher priority to bindings based on
    the number of tokens in binding with a classifying attribute.
    Furthermore, higher priority can be given to specific values of the attribute.
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
         Finds the priority of a SimToken based on the classifying attribute.
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
        bindings = [ ... ] # some collection of bindings
        priority = priority(bindings)

        # sorts the tokens based on the classifying attribute.
        SimVar("foo", priority=priority.find_priority)
    """

    def __init__(self, class_attr: str, priority_ordering: Collection[object]):
        self.attr = class_attr
        self.priorities = deepcopy(priority_ordering)

    def find_priority(self, token: SimToken) -> int:
        attr_val = None
        if hasattr(token.value, self.attr):
            attr_val = getattr(token.value, self.attr)

        if attr_val in self.priorities:
            return self.priorities.index(attr_val)
        return len(self.priorities)

    def __call__(self, bindings: Collection) -> object:

        def find_priority(binding):
            values = self.get_values(binding)
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
    A priority function that assigns higher priority to bindings based on
    the number of tokens in binding with a classifying attribute.
    Furthermore, priority can be given to specific values of the attribute.
    While similar to FirstClassPriority, this class allows for weights to be
    specified for each attribute value, meaning that the choice between
    bindings is determined by the total weight of the attribute values
    in the binding.

    For instance, we can say we are three times more likely to select a 'gold'
    customer over a 'silver' customer. Allowing for a more flexible prioritisation
    mechanism.

    :param class_attr: The attribute used for classifying tokens.
    :param weights: A mapping defining the weight of attribute values.
        Higher weight means that bindings with tokens having that value
        are more likely to be selected.

    The class is a callable that takes a collection of bindings and returns the binding
    with the highest priority based on the specified attribute and priority map.

    .. methods::
        __call__(bindings):
         Finds the binding with the highest priority.
         Useful for handling prioritisation in SimProblems.

        find_priority(tok):
         Finds the priority of a SimToken based on the classifying attribute.
         Useful for wanting to prioritise tokens associated with a SimVar.

    ^^^^^
    Example:
    ^^^^^
    .. code-block:: python
        priority = WeightedFirstClassPriority(
            class_attr='type',
            weights={
            'gold':5, 'silver':2.5 'bronze':0.5
            }
        )
        # returns the highest priority binding of bindings.
        bindings = [ ... ] # some collection of bindings
        priority = priority(bindings)

        # sorts the tokens based on the classifying attribute.
        SimVar("foo", priority=priority.find_priority)
    """

    def __init__(self, class_attr: str, weights: Dict[object, int]):
        self.attr = class_attr
        self.weights = weights

    def find_priority(self, token: SimToken) -> int:
        attr_val = None
        value = token.value
        weight = 0
        if isinstance(value, (tuple, list)):
            for item in value:
                if hasattr(item, self.attr):
                    attr_val = getattr(item, self.attr)
                    if attr_val in self.weights:
                        weight += self.weights[attr_val]
        else:
            if hasattr(token.value, self.attr):
                attr_val = getattr(token.value, self.attr)
                if attr_val in self.weights:
                    weight += self.weights[attr_val]

        return -1 * (weight + 1)

    def __call__(self, bindings: Collection) -> object:

        def find_priority(binding):
            values = self.get_values(binding)
            weight = 1

            for val in values:
                if isinstance(val.value, (tuple, list)):
                    for item in val.value:
                        if hasattr(item, self.attr):
                            attr_val = getattr(item, self.attr)
                            if attr_val in self.weights:
                                weight += self.weights[attr_val]
                else:
                    if hasattr(val.value, self.attr):
                        attr_val = getattr(val.value, self.attr)
                        if attr_val in self.weights:
                            weight += self.weights[attr_val]

            return weight

        # find the weights for each binding
        weights = [find_priority(binding) for binding in bindings]

        # select binding based on weights
        return random.choices(bindings, weights=weights, k=1)[0]


class NearestToCompletionPriority(PriorityFunction):
    """
    A priority function that assigns higher priority to tasks that are nearest
    to completion. Completion is determined by the number of times a token id
    has been seen and selected by the priority fucntion.

    If a token has been seen more times, it is considered to be closer to
    completion and is given higher priority over other tokens/bindings.

    This priority function is useful for prioritising completing executions
    over starting new ones. The highest priority is given to the binding with
    the combined total of token observations across all tokens in the binding.
    Then, if multiple bindings have the same total, a random choice is made
    between them.

    The class is a callable that takes a collection of bindings and returns
    the binding with the highest priority based on token observations.

    .. methods::
        __call__(bindings):
         Finds the binding with the highest priority.
         Useful for handling prioritisation in SimProblems.

        find_priority(tok):
         Not supported.
         Raises RuntimeError if called.

    ^^^^^
    Example:
    ^^^^^
    .. code-block:: python
        priority = WeightedFirstClassPriority(
            class_attr='type',
            weights={
            'gold':5, 'silver':2.5 'bronze':0.5
            }
        )
        # returns the highest priority binding of bindings.
        bindings = [ ... ] # some collection of bindings
        priority = priority(bindings)

        # this priority function does not support for place priority.
    """

    def __init__(self):
        super().__init__()
        self.observations = {}

    def _extract_token_id(self, value: object) -> str:
        if isinstance(value, SimToken):
            value = value.value
        if isinstance(value, SimTokenValue):
            return deepcopy(value.id)
        elif isinstance(value, str):
            return value
        else:
            raise ValueError(f"Cannot extract token id from value :: {type(value)=}")

    def find_priority(self, token: SimToken) -> int:
        raise RuntimeError(
            "This priority function does not support for place priority."
        )

    def _find_priority(self, token: SimToken) -> int:
        values = []
        if isinstance(token.value, (tuple, list)):
            for item in token.value:
                id = self._extract_token_id(item)
                values.append(self.observations.get(id, 0))
        else:
            id = self._extract_token_id(token.value)
            values.append(self.observations.get(id, 0))

        return sum(values)

    def __call__(self, bindings: Collection) -> object:

        def find_priority(binding):
            values = self.get_values(binding)
            weight = 1

            for val in values:
                weight += self._find_priority(val)

            return weight

        # find the weights for each binding
        selection = []
        highest_weight = float("-inf")
        for binding in bindings:
            weight = find_priority(binding)
            if weight > highest_weight:
                highest_weight = weight
                selection = [binding]
            elif weight == highest_weight:
                selection.append(binding)

        # select binding from highest weight bindings
        selected = random.choice(selection)

        # update observations
        values = self.get_values(selected)
        for val in values:
            if isinstance(val.value, (tuple, list)):
                for item in val.value:
                    id = self._extract_token_id(item)
                    if id not in self.observations:
                        self.observations[id] = 0
                    self.observations[id] += 1
            else:
                id = self._extract_token_id(val)
                if id not in self.observations:
                    self.observations[id] = 0
                self.observations[id] += 1

        return selected


class WeightedTaskPriority(PriorityFunction):
    """
    A priority function that assigns priority based on weights between tasks.
    The priority function makes a weighted random choice between bindings based
    on the event in the binding. The weight mapping should have keys that have
    would be used within the `names` of events, in particular they should begin
    with them. The value of mapping should be a float, where larger numbers make
    bindings for keyyed events more likely to be picked.

    A default weight of 1.0 is used for events not mentioned in the
    given weight mapping.

    :param weights: a mapping between event prefixes and weights to decide
        between bindings.

    The class is a callable that takes a collection of bindings and returns
    the binding with the highest priority based on token observations.

    .. methods::
        __call__(bindings):
         Finds the binding with the highest priority.
         Useful for handling prioritisation in SimProblems.

        find_priority(tok):
         Not supported.
         Raises RuntimeError if called.

    ^^^^^
    Example:
    ^^^^^
    .. code-block:: python
        priority = WeightedTaskPriority(
            weights={
                "started-process" : 10,
                "Investigate" : 2.5,
                "Calling Customer" : 10,
                "Pick Package for Gold": 7.5,
                "Invoice Gold": 7.5,
            },
            default_weight=0.5
        )
        # returns the highest priority binding of bindings.
        bindings = [ ... ] # some collection of bindings
        priority = priority(bindings)

        # this priority function does not support for place priority.
    """

    def __init__(self, weights: Dict[str, float], default_weight: int = 1.0):
        self.weights = weights
        self.default = default_weight

    def find_priority(self, token):
        raise RuntimeError(
            "This priority function does not support for place priority."
        )

    def __call__(self, bindings):
        weights = []
        for binding in bindings:
            event = self.get_event(binding)
            name: str = event._id
            appended = False

            for key in self.weights.keys():
                if name.lower().startswith(key.lower()):
                    weights.append(self.weights[key])
                    appended = True
                    break

            if not appended:
                weights.append(self.default)

        selected = random.choices(bindings, weights, k=1)[0]
        return selected
