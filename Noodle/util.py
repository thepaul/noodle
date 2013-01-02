# util

def listsplit(lst, item):
    parts = [[]]
    for member in lst:
        if member == item:
            parts.append([])
        else:
            parts[-1].append(member)
    return tuple(parts)

def dictadd(*somedicts):
    """Like a dict.update operation, but does not modify any of the
    dictionaries passed in. Instead, returns a new dictionary with the
    combination of all the dictionaries, with preference given to keys
    in dictionaries nearer the end.
    """

    return dict(item for d in somedicts for item in d.iteritems())

def partial(func, *fa, **fk):
    """Curry some arguments to the given function, and return a partial
    (a callable that accepts further arguments, if any). Keyword arguments
    are supported, and the callable can be used multiple times without
    being changed.
    """

    return lambda *a, **k: func(*(fa + a), **dictadd(fk, k))

def get_cell_value(cell):
    """Get the value associated with a cell object."""

    return type(lambda: 0)(
        (lambda x: lambda: x)(0).func_code, {}, None, None, (cell,)
    )() 

import new, dis
cell_changer = new.code(
    1, 1, 2, 0,
    ''.join([
        chr(dis.opmap['LOAD_FAST']), '\x00\x00',
        chr(dis.opmap['DUP_TOP']),
        chr(dis.opmap['STORE_DEREF']), '\x00\x00',
        chr(dis.opmap['RETURN_VALUE'])
    ]),
    (), (), ('newval',), '<nowhere>', 'cell_changer', 1, '', ('c',), ()
)

def change_cell_value(cell, newval):
    """Change the value associated with a cell object."""

    import new
    return new.function(cell_changer, {}, None, (), (cell,))(newval)
