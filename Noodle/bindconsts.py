# Taken from code by Raymond Hettinger-
# see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/277940
#
# Good stuff.

import sys
import util
from opcode import opmap, HAVE_ARGUMENT, EXTENDED_ARG
from types import FunctionType, ClassType, CodeType
globals().update(opmap)

def _make_constants(f, builtin_only=False, stoplist=[], verbose=False):
    try:
        co = f.func_code
    except AttributeError:
        return f

    import __builtin__
    env = vars(__builtin__).copy()
    if builtin_only:
        stoplist = dict.fromkeys(stoplist)
        stoplist.update(f.func_globals)
    else:
        env.update(f.func_globals)

    for cell in (f.func_closure or []):
        value = util.get_cell_value(cell)
        if isinstance(value, FunctionType):
            util.change_cell_value(
                cell,
                _make_constants(value, builtin_only, stoplist, verbose)
            )

    return type(f)(code_make_constants(f.func_code, env, stoplist, verbose),
                   f.func_globals, f.func_name, f.func_defaults, f.func_closure)

def code_make_constants(co, env, stoplist=[], verbose=False):
    newcode = map(ord, co.co_code)
    newconsts = [(isinstance(c, CodeType) and code_make_constants(c, env, stoplist, verbose) or c) for c in co.co_consts]
    names = co.co_names
    codelen = len(newcode)

    # First pass converts global lookups into constants
    i = 0
    while i < codelen:
        opcode = newcode[i]
        if opcode in (EXTENDED_ARG, STORE_GLOBAL):
            return co    # for simplicity, only optimize common cases
        if opcode == LOAD_GLOBAL:
            oparg = newcode[i+1] + (newcode[i+2] << 8)
            name = co.co_names[oparg]
            if name in env and name not in stoplist:
                value = env[name]
                for pos, v in enumerate(newconsts):
                    if v is value:
                        break
                else:
                    pos = len(newconsts)
                    newconsts.append(value)
                newcode[i] = LOAD_CONST
                newcode[i+1] = pos & 0xFF
                newcode[i+2] = pos >> 8
                if verbose:
                    print name, '-->', value
        i += 1
        if opcode >= HAVE_ARGUMENT:
            i += 2

    # Second pass folds tuples of constants and constant attribute lookups
    i = 0
    while i < codelen:

        newtuple = []
        while newcode[i] == LOAD_CONST:
            oparg = newcode[i+1] + (newcode[i+2] << 8)
            newtuple.append(newconsts[oparg])
            i += 3

        opcode = newcode[i]
        if not newtuple:
            i += 1
            if opcode >= HAVE_ARGUMENT:
                i += 2
            continue

        if opcode == LOAD_ATTR:
            obj = newtuple[-1]
            oparg = newcode[i+1] + (newcode[i+2] << 8)
            name = names[oparg]
            try:
                value = getattr(obj, name)
            except AttributeError:
                continue
            deletions = 1

        elif opcode == BUILD_TUPLE:
            oparg = newcode[i+1] + (newcode[i+2] << 8)
            if oparg != len(newtuple):
                continue
            deletions = len(newtuple)
            value = tuple(newtuple)

        else:
            continue

        reljump = deletions * 3
        newcode[i-reljump] = JUMP_FORWARD
        newcode[i-reljump+1] = (reljump-3) & 0xFF
        newcode[i-reljump+2] = (reljump-3) >> 8

        n = len(newconsts)
        newconsts.append(value)
        newcode[i] = LOAD_CONST
        newcode[i+1] = n & 0xFF
        newcode[i+2] = n >> 8
        i += 3
        if verbose:
            print "new folded constant:", value

    codestr = ''.join(map(chr, newcode))
    return type(co)(co.co_argcount, co.co_nlocals, co.co_stacksize,
                    co.co_flags, codestr, tuple(newconsts), co.co_names,
                    co.co_varnames, co.co_filename, co.co_name,
                    co.co_firstlineno, co.co_lnotab, co.co_freevars,
                    co.co_cellvars)

_make_constants = _make_constants(_make_constants) # optimize thyself!

@_make_constants
def bind_all(mc, **kwargs):
    """Recursively apply constant binding to functions in a module or class.

    Use as the last line of the module (after everything is defined, but
    before test code).  In modules that need modifiable globals, set
    builtin_only to True.

    """
    try:
        d = vars(mc)
    except TypeError:
        return
    for k, v in d.items():
        if type(v) is FunctionType:
            newv = _make_constants(v, **kwargs)
            setattr(mc, k, newv)
        elif type(v) in (type, ClassType):
            bind_all(v, **kwargs)

@_make_constants
def bind_module_funcs(**kwargs):
    d = sys._getframe().f_back.f_globals
    for k, v in d.iteritems():
        if type(v) is FunctionType:
            d[k] = _make_constants(v, **kwargs)
        elif type(v) in (type, ClassType):
            bind_all(v, **kwargs)

@_make_constants
def make_constants(*args, **kwargs):
    """ Return a decorator for optimizing global references.

    Replaces global references with their currently defined values.
    If not defined, the dynamic (runtime) global lookup is left undisturbed.
    If builtin_only is True, then only builtins are optimized.
    Variable names in the stoplist are also left undisturbed.
    Also, folds constant attr lookups and tuples of constants.
    If verbose is True, prints each substitution as is occurs

    """
    if len(args) == 1 and type(args[0]) == type(make_constants):
        return _make_constants(args[0])
    else:
        return lambda f: _make_constants(f, *args, **kwargs)
