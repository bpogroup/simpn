def sed(s1: str, s2: str) -> int:
    """
    Computes the string edit distance between two strings.

    :param s1: The first string.
    :param s2: The second string.

    :return: The edit distance between the two strings.
    """
    if len(s1) < len(s2):
        return sed(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def seds(s1: str, s2: str) -> float:
    """
    Computes the string edit distance similarity between two strings.
    This is the string edit distance divided by the length of the longer string.

    :param s1: The first string.
    :param s2: The second string.

    :return: The edit distance between the two strings.
    """
    return 1.0 - (sed(s1, s2) / max(len(s1), len(s2)))