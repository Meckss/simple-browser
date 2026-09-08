def tree_to_list(tree, list):
    """Flatten a tree into a list using a pre-order traversal.

    The root node is appended first, followed by each descendant in
    child order. The supplied list is modified in place and returned.

    Args:
        tree: The root node to traverse. Each node must have a ``children``
            attribute containing its child nodes.
        list: The list to which nodes are appended.

    Returns:
        The same list passed in through ``list``, containing the tree's nodes.
    """
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list
