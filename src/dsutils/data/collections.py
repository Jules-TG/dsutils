def compare_lists(l1: list, l2: list, length: bool = False):
    """Compare two lists by set operations and return unique and shared items.

    Args:
        l1: The first list to compare.
        l2: The second list to compare.
        length: If True, return counts instead of the actual items.

    Returns:
        A tuple of (unique_to_l1, unique_to_l2, shared_items). When ``length``
        is True, each element is an integer count instead of a list.
    """
    s1, s2 = set(l1), set(l2)

    l1_uniques = list(s1 - s2)
    l2_uniques = list(s2 - s1)
    shared_items = list(s1 & s2)

    if length:
        return len(l1_uniques), len(l2_uniques), len(shared_items)
    else:
        return l1_uniques, l2_uniques, shared_items
