import types
import functools


class FunctionRegistry:
    def __init__(self, sep: str = ":"):
        """
        Assigns unique names to functions to ensure different events can have the same behavior but distinct names.
        It also perform function copy operations to have different name, but no undesirable side effect on global
        variable and object attributes.
        """
        self.previous_functions = dict()
        # Separator to distinguish between user-defined names and generated names
        self.sep = sep

    def rename_callable(self, func):
        is_an_attribute_of_an_object = hasattr(func, "__self__") and func.__self__ is not None
        func_name = func.__name__

        is_never_seen_before = func_name not in self.previous_functions
        if is_never_seen_before:
            # First time seeing this function name, initialize the counter
            self.previous_functions[func.__name__] = 1
            return func  # No need to rename it for the first instance

        if is_an_attribute_of_an_object:
            # If it's a bound method (has __self__), handle it separately
            instance = func.__self__

            # Increment identifier for future calls
            identifier = str(self.previous_functions[func_name])
            self.previous_functions[func_name] += 1

            # Create a new function name with a unique identifier
            new_func_name = func_name + self.sep + identifier
            # Wrap the method using functools.partial to retain the bound instance
            func2 = functools.partial(func)
            func2.__name__ = new_func_name

        else:
            # Increment identifier for future calls
            identifier = str(self.previous_functions[func.__name__])
            self.previous_functions[func.__name__] += 1

            # Create a new function object with a new unique name
            new_func_name = func.__name__ + self.sep + identifier

            func2 = types.FunctionType(code=func.__code__,
                                       globals=func.__globals__,
                                       name=new_func_name,
                                       closure=func.__closure__)

            # Copy over important metadata
            func2.__dict__.update(func.__dict__)  # Copy attributes
            func2.__doc__ = func.__doc__  # Copy docstring
            func2.__annotations__ = func.__annotations__  # Copy annotations

        return func2
