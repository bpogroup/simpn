"""
This module contains some predefined priority functions for use in BPMN models.
"""


class FirstClassPriority:
    """
    A priority function that assigns higher priority to tasks with lower 
    class numbers.
    """

    def __call__(self, *args, **kwds):
        pass


class WeightedFirstClassPriority:
    """
    A priority function that assigns priority based on 
    weighted class numbers.
    """

    def __init__(self, weights):
        self.weights = weights

    def __call__(self, *args, **kwds):
        pass


class NearestToCompletionPriority:
    """
    A priority function that assigns higher priority to tasks that are nearest 
    to completion.
    """

    def __call__(self, *args, **kwds):
        pass


class WeightedTaskPriority:
    """
    A priority function that assigns priority based on weights between tasks.
    """

    def __init__(self, weights):
        self.weights = weights

    def __call__(self, *args, **kwds):
        pass
