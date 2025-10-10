# This is a try-out of a more simple breadth-first search,
# before we try it on the actual problem: finding bindings.

def bfs(values, combinations, condition, max_time, look_beyond=False):
    """
    Breadth-first search to find a combination of indices at which the values satisfy a given condition.
    Initially, look_beyond is False, meaning we only consider combinations, where each index <= max_time.
    If no such combination is found, we set look_beyond to True and continue searching without the max_time constraint.
    :param values: A list of lists of possible values.
    :param combinations: A list of tuples, each representing a combination of indices into the lists in values.
    :param condition: A function that takes values and a combination of indices, and returns True if the condition is satisfied.
    :param max_time: The maximum index value to consider when look_beyond is False.
    :param look_beyond: A boolean indicating whether to ignore the max_time constraint.
    :return: A combination of indices that satisfies the condition, or None if no such combination exists.
    """
    next_combinations = []
    seen = set()

    for t in combinations:
        value_tuple = tuple(values[j][t[j]] for j in range(len(values)))
        if condition(value_tuple):
            return t
        for j in range(len(t)):
            if t[j] + 1 >= len(values[j]):
                continue
            if not look_beyond and t[j]+1 > max_time:
                continue
            u = (*t[:j], t[j] + 1, *t[j+1:])
            if u not in seen:
                next_combinations.append(u)
                seen.add(u)
    if len(next_combinations) == 0:
        if look_beyond:
            return None
        else:
            return bfs(values, combinations, condition, max_time, True)
    return bfs(values, next_combinations, condition, max_time, look_beyond)


values = [[1,2,3], [1,2,3], [1,2,3]]
initial_combination = [tuple(0 for _ in values)]
condition = lambda vals: sum(vals) == 6
result = bfs(values, initial_combination, condition, 5)
result_values = [values[i][result[i]] for i in range(len(values))]
print(result, result_values)

initial_combination = [tuple(0 for _ in values)]
condition = lambda vals: sum(vals) == 6
result = bfs(values, initial_combination, condition, 1)
result_values = [values[i][result[i]] for i in range(len(values))]
print(result, result_values)

initial_combination = [tuple(0 for _ in values)]
condition = lambda vals: sum(vals) == 7
result = bfs(values, initial_combination, condition, 1)
result_values = [values[i][result[i]] for i in range(len(values))]
print(result, result_values)
