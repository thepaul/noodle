# builtins

import assembling
from compiling import CompileLater, NoodleFunction, NoodleModule, ExecStmt
from error import NoodleSyntaxError, NoodleCompilerError
from NoodleBasics import (Symbol, NoCompilation, unique_name, current_macros)

predefineds = {}

def make_special(funcname):
    def add_to_predefineds(func):
        predefineds[funcname] = func
        return func
    return add_to_predefineds

@make_special('apply')
def apply(block, args):
    if len(args) < 1:
        block.emit_load_constant(())
        return NoCompilation

    func = args[0]
    positionals, keywords, varargs, kwargs = \
        decode_function_arguments(args[1:], check='nocheck')

    if len(keywords) > 255:
        raise NoodleSyntaxError("too many explicit keyword arguments given")
    if len(positionals) > 255:
        raise NoodleSyntaxError("too many positional arguments given")

    # high byte: number of keyword args; low byte: number of positional args
    oparg = (len(keywords) << 8) | len(positionals)

    block.compile_piece(func)
    for posarg in positionals:
        block.compile_piece(posarg)
    for key, value in keywords:
        block.compile_piece(key.name)
        block.compile_piece(value)
    if varargs:
        block.compile_piece(varargs)
        if kwargs:
            block.compile_piece(kwargs)
            block.emit('CALL_FUNCTION_VAR_KW', oparg)
        else:
            block.emit('CALL_FUNCTION_VAR', oparg)
    else:
        if kwargs:
            block.compile_piece(kwargs)
            block.emit('CALL_FUNCTION_KW', oparg)
        else:
            block.emit('CALL_FUNCTION', oparg)
    return NoCompilation

def make_recursive_apply(func_name, expected_args):
    def apply_recursively(block, args):
        positionals, keywords, varargs, kwargs = \
            decode_function_arguments(args, check='nocheck')
        return apply(block, (Symbol(func_name),) + args)
    return apply_recursively

@make_special('begin')
def begin(block, args):
    if len(args) == 0:
        args = [None]
    for arg in args[:-1]:
        block.compile_piece(arg)
        block.emit('POP_TOP')
    block.compile_piece(args[-1])
    return NoCompilation

@make_special('prog1')
def prog1(block, args):
    if len(args) == 0:
        return
    block.compile_piece(args[0])
    for arg in args[1:]:
        block.compile_piece(arg)
        block.emit('POP_TOP')
    return NoCompilation

@make_special('subscript')
def subscript(block, args):
    if len(args) != 2:
        raise NoodleSyntaxError("subscript operator takes exactly 2 arguments")
    block.compile_piece(args[0])
    if arg_is_special_symbol(args[1], 'mkslice', 2):
        low, high = args[1][1:3]
        if high is None:
            if low is None:
                block.emit('SLICE+0')
            else:
                block.compile_piece(low)
                block.emit('SLICE+1')
        else:
            if low is None:
                block.compile_piece(high)
                block.emit('SLICE+2')
            else:
                block.compile_piece(low)
                block.compile_piece(high)
                block.emit('SLICE+3')
    else:
        block.compile_piece(args[1])
        block.emit('BINARY_SUBSCR')
    return NoCompilation

@make_special('mkdict')
def mkdict(block, args):
    block.emit('BUILD_MAP', 0)
    for pair in args:
        block.emit_set_lineno(pair)
        key, val = pair
        block.emit('DUP_TOP')
        block.compile_piece(key)
        block.compile_piece(val)
        block.emit('ROT_THREE')
        block.emit('STORE_SUBSCR')
    return NoCompilation

@make_special('mktuple')
def mktuple(block, args):
    for arg in args:
        block.compile_piece(arg)
    block.emit('BUILD_TUPLE', len(args))
    return NoCompilation

@make_special('mklist')
def mklist(block, args):
    for arg in args:
        block.compile_piece(arg)
    block.emit('BUILD_LIST', len(args))
    return NoCompilation

@make_special('print-item')
def m_print_item(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "print-item requires 1 argument (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    block.emit('DUP_TOP')
    block.emit('PRINT_ITEM')
    return NoCompilation

@make_special('print-newline')
def m_print_newline(block, args):
    if len(args) != 0:
        raise NoodleSyntaxError(
            "print-newline requires 0 arguments (%d given)" % len(args)
        )
    block.emit('PRINT_NEWLINE')

@make_special('print-item-to')
def m_print_item_to(block, args):
    if len(args) != 2:
        raise NoodleSyntaxError(
            "print-item-to requires 2 arguments (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    block.emit('DUP_TOP')
    block.compile_piece(args[1])
    block.emit('ROT_TWO')
    block.emit('PRINT_ITEM_TO')
    return NoCompilation

@make_special('print-newline-to')
def m_print_newline_to(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "print-newline-to requires 1 argument (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    block.emit('DUP_TOP')
    block.emit('PRINT_NEWLINE_TO')
    return NoCompilation

@make_special('=')
def m_equal(block, args):
    if len(args) < 2:
        raise NoodleSyntaxError(
            "= takes exactly two arguments (%d given)" % len(args)
        )
    block.compile_piece(args[1])
    block.emit('DUP_TOP')
    assign_value_or_values(block, args[0])
    return NoCompilation

@make_special('setsubscript')
def setsubscript(block, args):
    if len(args) != 3:
        raise NoodleSyntaxError(
            "setsubscript requires 3 arguments (%d given)" % len(args)
        )
    block.compile_piece(args[2])
    block.compile_piece(args[0])
    store_to_subscript(block, args[1])

def store_to_subscript(block, subscript):
    if arg_is_special_symbol(subscript, 'mkslice', 2):
        low, high = subscript[1:]
        if high is None:
            if low is None:
                block.emit('STORE_SLICE+0')
            else:
                block.compile_piece(low)
                block.emit('STORE_SLICE+1')
        else:
            if low is None:
                block.compile_piece(high)
                block.emit('STORE_SLICE+2')
            else:
                block.compile_piece(low)
                block.compile_piece(high)
                block.emit('STORE_SLICE+3')
    else:
        block.compile_piece(subscript)
        block.emit('STORE_SUBSCR')

@make_special('setattribute')
def setattribute(block, args):
    if len(args) != 3:
        raise NoodleSyntaxError(
            "setattribute requires 3 arguments (%d given)" % len(args)
        )
    block.compile_piece(args[2])
    block.emit('DUP_TOP')
    block.compile_piece(args[0])
    store_to_attribute(block, args[1])

def store_to_attribute(block, attrname):
    if not isinstance(attrname, Symbol):
        raise NoodleSyntaxError("Invalid attribute name")
    block.emit('STORE_ATTR', block.lookup_add_name(attrname.name))

def assign_value_or_values(block, varnames):
    if isinstance(varnames, tuple):
        if arg_is_special_symbol(varnames, 'subscript', 2):
            block.compile_piece(varnames[1])
            store_to_subscript(block, varnames[2])
            return
        if arg_is_special_symbol(varnames, 'getattribute', 2):
            block.compile_piece(varnames[1])
            store_to_attribute(block, varnames[2])
            return
        if isinstance(varnames[0], Symbol) \
        and varnames[0].name == 'mktuple':
            varnames = varnames[1:]
        block.emit('UNPACK_SEQUENCE', len(varnames))
        for varname in varnames:
            assign_value_or_values(block, varname)
    elif isinstance(varnames, Symbol):
        block.emit_store_name(varnames.name, dup=False)
    else:
        raise NoodleCompilerError(
            "Unsupported argument type as target of assignment"
        )

@make_special('define')
def m_define(block, args):
    if len(args) < 1:
        raise NoodleSyntaxError(
            "define takes at least two arguments (%d given)" % len(args)
        )
    elif len(args) == 1:
        args = (args[0], None)
    varname = args[0]

    if isinstance(varname, tuple):
        define_function(block, varname[0].name, varname[1:], args[1:])
    elif isinstance(varname, Symbol):
        if len(args) != 2:
            raise NoodleSyntaxError(
                "defining a variable requires exactly 1 value argument"
            )
        define_variable(block, varname.name, args[1])
    else:
        raise NoodleCompilerError(
            "define operator received unrecognized argument type %r" % varname
        )
    return NoCompilation

def define_variable(block, varname, value):
    # force it to be local, not free or global
    block.force_add_local(varname)
    block.compile_piece(value)
    block.emit_store_name(varname)

def define_function(block, funcname, funcargs, funcsteps):
    # force it to be local, not free or global
    block.force_add_local(funcname)
    define_lambda(block, funcargs, funcsteps, codename=funcname)
    block.emit_store_name(funcname, dup=True)

@make_special('lambda')
def m_lambda(block, args):
    define_lambda(block, args[0], args[1:])
    return NoCompilation

def define_lambda(block, args, steps, codename='*lambda*'):
    given_posargs, func_defaultargs, func_vararg, func_kwarg = \
        decode_function_arguments(args)

    func_posargs = []
    codetuple = [Symbol('begin')]
    for element in given_posargs:
        if isinstance(element, tuple):
            specialname = Symbol(unique_name())
            func_posargs.append(specialname)
            codetuple.append((Symbol('='), element, specialname))
        else:
            if not isinstance(element, Symbol):
                raise NoodleSyntaxError(
                    "Defined arguments to a function must be symbols"
                )
            func_posargs.append(element)

    arglist = list([pos.name for pos in func_posargs])
    codeflags = 0
    for name, val in func_defaultargs:
        arglist.append(name.name)
        block.compile_piece(val)
    if func_vararg:
        arglist.append(func_vararg.name)
        codeflags |= 0x4  # uses *args syntax
    if func_kwarg:
        arglist.append(func_kwarg.name)
        codeflags |= 0x8  # uses **kwargs syntax

    # (final) stack changes to result from this MAKE_FUNCTION call.
    # Doesn't yet take into account free variables to be loaded and
    # consumed.
    block.stackmove(-len(func_defaultargs))

    # docstring
    docstring = None
    if len(steps) > 0 and isinstance(steps[0], str):
        docstring = steps[0]
        steps = steps[1:]

    block.code.append(CreateSubBlock(
        block.subfunc(
            tuple(codetuple) + tuple(steps),
            firstlineno=block.curlineno,
            varnames=arglist,
            argcount=(len(func_posargs) + len(func_defaultargs)),
            codename=codename,
            codeflags=codeflags,
            docstring=docstring,
            nopassmacros={
                codename: make_recursive_apply(
                    codename,
                    [n.name for n in func_posargs] +
                        [p[0].name for p in tuple(func_defaultargs)]
                ),
                'return': m_return,
                'yield': m_yield
            }
        ),
        block,
        len(func_defaultargs)
    ))
    block.stackmove(1)

class CreateSubBlock(CompileLater):
    def __init__(self, newblock, oldblock, numdefaults):
        self.newblock = newblock
        self.oldblock = oldblock
        self.numdefaults = numdefaults

    def find_cell(self, varname):
        num = self.oldblock.lookup_cell(varname)
        if num is not None:
            return num
        num = self.oldblock.lookup_free(varname)
        if num is not None:
            return len(self.oldblock.cellvars) + num
        raise NoodleCompilerError(
            "Subblock had invalid free variable %s" % varname
        )

    def compile(self):
        code_object = self.newblock.as_code_object()
        mycode = []

        # if a nested scope, load the cells for the cellvars
        for freevar in code_object.co_freevars:
            mycode.append(('LOAD_CLOSURE', self.find_cell(freevar)))
        # this might have affected maxstacklevel (not necessarily, of course)
        self.oldblock.maxstacklevel += len(code_object.co_freevars)

        mycode.append(('LOAD_CONST', self.oldblock.add_constant(code_object)))

        if code_object.co_freevars:
            mycode.append(('MAKE_CLOSURE', self.numdefaults))
        else:
            mycode.append(('MAKE_FUNCTION', self.numdefaults))
        self.code = ''.join(
            [assembling.assemble_instruction(*t) for t in mycode]
        )

    def prepare(self, block, index):
        return self.code

def decode_function_arguments(arglist, check=''):
    """Set check to a nonempty string to skip checking of argument type
    order. This will probably cause problems except when making a function
    call, rather than defining arguments.
    """

    vararg = None
    kwarg = None
    keywords = []
    pos = []
    used = set()
    for arg in arglist:
        if arg_is_special_symbol(arg, 'mkvarargs', 1):
            if 'kwarg' in used:
                raise NoodleSyntaxError("* arg used after ** arg")
            if 'vararg' in used:
                raise NoodleSyntaxError("two * args given")
            used.add('vararg' + check)
            vararg = arg[1]
        elif arg_is_special_symbol(arg, 'mkkwargs', 1):
            if 'kwarg' in used:
                raise NoodleSyntaxError("two ** args given")
            used.add('kwarg' + check)
            kwarg = arg[1]
        elif arg_is_special_symbol(arg, 'mkkeyword', 2):
            if 'kwarg' in used:
                raise NoodleSyntaxError("keyword argument used after ** arg")
            if 'vararg' in used:
                raise NoodleSyntaxError("keyword argument used after * arg")
            used.add('keyword' + check)
            if not isinstance(arg[1], Symbol):
                raise NoodleSyntaxError("keyword key must be symbol")
            keywords.append((arg[1], arg[2]))
        else:
            if 'kwarg' in used:
                raise NoodleSyntaxError("positional arg used after ** arg")
            if 'vararg' in used:
                raise NoodleSyntaxError("positional arg used after * arg")
            if 'keyword' in used:
                raise NoodleSyntaxError("positional arg used after keyword arg")
            pos.append(arg)

    return pos, keywords, vararg, kwarg

@make_special('defmacro')
def defmacro(block, args):
    if len(args) < 2:
        raise NoodleSyntaxError(
            "defmacro takes at least two arguments (%d given)" % len(args)
        )
    if not isinstance(args[0], tuple) or len(args[0]) < 1:
        raise NoodleSyntaxError(
            "Bad defmacro syntax; non-empty tuple required as first argument"
        )
    funcname = args[0][0]
    if not isinstance(funcname, Symbol):
        raise NoodleSyntaxError(
            "Bad defmacro syntax; symbol required as function name"
        )
    funcname = funcname.name

    pos, keywords, vararg, kwarg = decode_function_arguments(args[0][1:])
    argnames = [p.name for p in pos]
    codeflags = 0
    codetuple = [Symbol('begin')]
    defaults = 0
    for k, v in keywords:
        argnames.append(k.name)
        codetuple.append((Symbol('if'),
                          (Symbol('is'), Symbol('None'), k),
                          (Symbol('='), k, v)))
        defaults += 1
    if vararg:
        argnames.append(vararg.name)
        codeflags |= 0x4  # uses *args syntax
    if kwarg:
        raise NoodleSyntaxError(
            "Invalid mkkwargs in defmacro: macros cannot take keyword arguments"
        )

    macrocode = NoodleFunction(
        tuple(codetuple) + tuple(args[1:]),
        block.filename,
        varnames=list(argnames),
        argcount=(len(pos) + len(keywords)),
        codename=funcname,
        codeflags=codeflags
    ).as_code_object()

    from nucfiles import macrofunc_from_macrocode
    current_macros[funcname] = macrofunc_from_macrocode(
        macrocode, defaults, block.compiling_namespace
    )
    block.localmacro(funcname, macrocode, defaults)

@make_special('undefmacro')
def undefmacro(block, args):
    for macroname in args:
        if not isinstance(macroname, Symbol):
            raise NoodleSyntaxError("undefmacro requires all symbol arguments")
        if macroname.name in current_macros:
            del current_macros[macroname.name]
        else:
            raise NoodleSyntaxError(
                "undefmacro: No macro named '%s'" % macroname.name
            )

@make_special('macroexpand-1')
def macroexpand_1(block, args):
    if len(args) != 1 or not isinstance(args[0], tuple):
        raise NoodleSyntaxError("macroexpand-1 requires one tuple argument")
    mactup = args[0]
    if len(mactup) == 0:
        return ()
    if not isinstance(mactup[0], Symbol):
        raise NoodleSyntaxError(
            "Argument to macroexpand-1 must start with a symbol"
        )
    macfunc = block.lookup_macro(mactup[0].name)
    if macfunc is None:
        raise NoodleSyntaxError("No macro named %s" % mactup[0].name)
    return quote(block, (macfunc(block, mactup[1:]),))

@make_special('and')
def m_and(block, args):
    if len(args) < 1:
        block.emit_load_constant(True)
        return NoCompilation
    jumpers = []
    for arg in args[:-1]:
        block.compile_piece(arg)
        jumpers.append(block.emit_jump_if_false())
        block.emit('POP_TOP')
    block.compile_piece(args[-1])
    for jump in jumpers:
        block.set_jump_target(jump)
    return NoCompilation

@make_special('or')
def m_or(block, args):
    if len(args) < 1:
        return False
    jumpers = []
    for arg in args[:-1]:
        block.compile_piece(arg)
        jumpers.append(block.emit_jump_if_true())
        block.emit('POP_TOP')
    block.compile_piece(args[-1])
    for jump in jumpers:
        block.set_jump_target(jump)
    return NoCompilation

@make_special('assert')
def m_assert(block, args):
    block.compile_piece((Symbol('begin'),) + tuple(args))
    jump = block.emit_jump_if_true()
    block.emit('POP_TOP')
    block.emit_load_global('AssertionError')
    block.emit('RAISE_VARARGS', 1)
    block.set_jump_target(jump)
    block.stackmove(1)
    return NoCompilation

def make_special_operator(sym, opcode, if_one_term=None):
    def operator_macro(block, args):
        if args_contain_special_symbol(args, 'mkvarargs', 1):
            return (Symbol('apply'), Symbol(sym)) + tuple(args)
        elif len(args) == 0:
            block.emit_load_constant(0)
        elif (len(args) == 1) and (if_one_term is not None):
            if_one_term(block, args[0])
        else:
            block.compile_piece(args[0])
            for arg in args[1:]:
                block.compile_piece(arg)
                block.emit(opcode)
        return NoCompilation
    return operator_macro

def unary_plus(block, arg):
    # Why does UNARY_POSITIVE even exist? There must be a good reason,
    # so I'll support it.
    block.compile_piece(arg)
    block.emit('UNARY_POSITIVE')

def unary_minus(block, arg):
    block.compile_piece(arg)
    block.emit('UNARY_NEGATIVE')

def reciprocal(block, arg):
    block.emit_load_constant(1.0)
    block.compile_piece(arg)
    block.emit('BINARY_TRUE_DIVIDE')

def lshiftone(block, arg):
    block.emit_load_constant(1)
    block.compile_piece(arg)
    block.emit('BINARY_LSHIFT')

def rshiftone(block, arg):
    block.emit_load_constant(1)
    block.compile_piece(arg)
    block.emit('BINARY_RSHIFT')

make_special('+')(make_special_operator('+', 'BINARY_ADD', unary_plus))
make_special('-')(make_special_operator('-', 'BINARY_SUBTRACT', unary_minus))
make_special('*')(make_special_operator('*', 'BINARY_MULTIPLY'))
make_special('/')(make_special_operator('/', 'BINARY_TRUE_DIVIDE', reciprocal))
make_special('%')(make_special_operator('%', 'BINARY_MODULO'))
make_special('**')(make_special_operator('**', 'BINARY_POWER'))
make_special('//')(make_special_operator('//', 'BINARY_FLOOR_DIVIDE'))
make_special('<<')(make_special_operator('<<', 'BINARY_LSHIFT', lshiftone))
make_special('>>')(make_special_operator('>>', 'BINARY_RSHIFT', rshiftone))
make_special('&')(make_special_operator('&', 'BINARY_AND'))
make_special('^')(make_special_operator('^', 'BINARY_XOR'))
make_special('|')(make_special_operator('|', 'BINARY_OR'))

@make_special('~')
def m_invert(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "~ takes exactly one argument (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    block.emit('UNARY_INVERT')
    return NoCompilation

@make_special('not')
def m_not(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "(not) takes exactly one argument (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    block.emit('UNARY_NOT')
    return NoCompilation

def make_comparer(opsign):
    opnum = assembling.compare_op[opsign]
    def comparer(block, args):
        if args_contain_special_symbol(args, 'mkvarargs', 1):
            return (Symbol('apply'), Symbol(opsign)) + tuple(args)
        if len(args) < 2:
            raise NoodleSyntaxError(
                "%s op needs 2 or more arguments (%d given)" %
                   (opsign, len(args))
            )
        elif len(args) == 2:
            block.compile_piece(args[0])
            block.compile_piece(args[1])
            block.emit('COMPARE_OP', opnum)
        else:
            block.emit_load_constant(True)
            block.compile_piece(args[0])
            for arg in args[1:]:
                block.compile_piece(arg)
                block.emit('DUP_TOP')
                block.emit('ROT_THREE')
                block.emit('COMPARE_OP', opnum)
                block.emit('ROT_TWO')
                block.emit('ROT_THREE')
                block.emit('BINARY_AND')
                block.emit('ROT_TWO')
            block.emit('POP_TOP')
        return NoCompilation
    comparer.func_name = '%s-comparer' % opsign
    return comparer

for comparesign in ('==', '!=', '>', '<', '>=', '<=', 'in', 'is'):
    make_special(comparesign)(make_comparer(comparesign))
make_special('not-in')(make_comparer('not in'))
make_special('is-not')(make_comparer('is not'))

def make_inplace_op(opname, opcode):
    def inplace_op(block, args):
        if len(args) == 0 \
        or not isinstance(args[0], Symbol):
            raise NoodleSyntaxError(
                "First argument to %s must be a symbol" % opname
            )
        block.emit_load_name(args[0].name)
        for arg in args[1:]:
            block.compile_piece(arg)
            block.emit(opcode)
        block.emit_store_name(args[0].name)
        return NoCompilation
    return inplace_op

for opname, opcode in {
    '+=': 'INPLACE_ADD',
    '-=': 'INPLACE_SUBTRACT',
    '*=': 'INPLACE_MULTIPLY',
    '/=': 'INPLACE_TRUE_DIVIDE',
    '//=': 'INPLACE_FLOOR_DIVIDE',
    '%=': 'INPLACE_MODULO',
    '<<=': 'INPLACE_LSHIFT',
    '>>=': 'INPLACE_RSHIFT',
    '&=': 'INPLACE_AND',
    '^=': 'INPLACE_XOR',
    '|=': 'INPLACE_OR',
    '**=': 'INPLACE_POWER',
}.iteritems():
    make_special(opname)(make_inplace_op(opname, opcode))

@make_special('cond')
def m_cond(block, args):
    endjumps = []
    for arg in args:
        if not isinstance(arg, tuple):
            raise NoodleSyntaxError("Arguments to cond must be tuples")
        if len(arg) < 1:
            raise NoodleSyntaxError("Empty tuple to cond")
        if isinstance(arg[0], Symbol) \
        and arg[0] == Symbol('else'):
            begin(block, arg[1:])
            break

        block.compile_piece(arg[0])
        lastjump = block.emit_jump_if_false()
        block.emit('POP_TOP') # pop value tested, if true
        begin(block, arg[1:])
        endjumps.append(block.emit_jump_forward())
        block.set_jump_target(lastjump)
        block.emit('POP_TOP') # pop value tested, if false

    else:
        # this point reached if no else clause given
        block.emit_load_constant(None)

    for endjump in endjumps:
        block.set_jump_target(endjump)

    return NoCompilation

@make_special('if')
def m_if(block, args):
    if len(args) < 2 or len(args) > 3:
        raise NoodleSyntaxError("Bad (if) call; needs 2 or 3 arguments")
    block.compile_piece(args[0])
    jump_over_true = block.emit_jump_if_false()
    block.emit('POP_TOP')
    block.compile_piece(args[1])
    jump_over_false = block.emit_jump_forward()
    block.set_jump_target(jump_over_true)
    block.emit('POP_TOP')
    if len(args) == 3:
        block.compile_piece(args[2])
    else:
        block.emit_load_constant(None)
    block.set_jump_target(jump_over_false)
    return NoCompilation

def compile_loop_body(block, loopstart, steps):
    """Insert code to execute the statements in a loop, properly providing
    the continue and break operators. 'continue' should jump back to
    loopstart, and the function returns a list of forward jumps from 'break'
    statements. Before continue or break or end-of-body, the stack must be at
    the same depth at which it is when this at the start (now).
    """

    def fixstack(block):
        if block.stacklevel < stacklevel_at_start:
            raise NoodleCompilerError("Unexpected low stack level")
        pops = block.stacklevel - stacklevel_at_start
        for x in xrange(pops):
            block.emit('POP_TOP')
        return pops

    # Can't use BREAK_LOOP or CONTINUE_LOOP; they pop off everything on the
    # stack, since Python would never have items on the stack when starting a
    # loop (?)

    def m_break(block, args):
        block.stackmove(fixstack(block))
        breaks.append(block.emit_jump_forward())
        block.stackmove(1)  # to keep stack count as expected at call end
        return NoCompilation

    def m_continue(block, args):
        block.stackmove(fixstack(block))
        block.emit_jump_absolute_backward(loopstart)
        block.stackmove(1)  # to keep stack count as expected at call end
        return NoCompilation

    breaks = []
    stacklevel_at_start = block.stacklevel

    # override any break or continue macros defined (probably from
    # enclosing loops, if any)
    oldbreak = block.nopassmacros.get('break', None)
    oldcontinue = block.nopassmacros.get('continue', None)
    block.nopassmacros['break'] = m_break
    block.nopassmacros['continue'] = m_continue

    begin(block, steps)
    block.emit('POP_TOP')

    if block.stacklevel != stacklevel_at_start:
        raise NoodleCompilerError("Unexpected stacklevel after loop body")

    # Restore previous break/continue actions, if any
    del block.nopassmacros['break']
    del block.nopassmacros['continue']
    if oldbreak is not None:
        block.nopassmacros['break'] = oldbreak
    if oldcontinue is not None:
        block.nopassmacros['continue'] = oldcontinue

    return breaks

@make_special('while')
def m_while(block, args):
    if len(args) == 0:
        return
    loopstart = block.set_backward_jump_target()
    block.compile_piece(args[0])
    jumps_to_end = [block.emit_jump_if_false()]
    block.emit('POP_TOP')

    jumps_to_end.extend(compile_loop_body(block, loopstart, args[1:]))

    block.emit_jump_absolute_backward(loopstart)
    map(block.set_jump_target, jumps_to_end)

@make_special('iterate-over')
def m_iterate_over(block, args):
    if len(args) < 2:
        raise NoodleSyntaxError(
            "Bad iterate-over: should be like 'iterate-over varname iter ...'"
        )
    block.compile_piece(args[1])
    loopstart = block.set_backward_jump_target()
    jumps_to_end = [block.emit_for_iter()]
    assign_value_or_values(block, args[0])

    jumps_to_end.extend(compile_loop_body(block, loopstart, args[2:]))

    block.emit_jump_absolute_backward(loopstart)
    map(block.set_jump_target, jumps_to_end)

def dotted_name_in_import(arg):
    if arg_is_special_symbol(arg, 'getattribute', 2):
        return '%s.%s' % (dotted_name_in_import(arg[1]), arg[2].name)
    elif isinstance(arg, Symbol):
        return arg.name
    else:
        raise NoodleSyntaxError(
            "Improper expression as import name: %s" % repr(arg)
        )

@make_special('import')
def m_import(block, args):
    for module in args:
        block.emit_load_constant(None)
        fullname = dotted_name_in_import(module)
        block.emit('IMPORT_NAME', block.lookup_add_name(fullname))
        block.emit_store_name(fullname.split('.', 1)[0], dup=True)
    if len(args) > 1:
        block.emit('BUILD_TUPLE', len(args))
    return NoCompilation

@make_special('get-module')
def m_get_module(block, args):
    for module in args:
        block.emit_load_constant(None)
        fullname = dotted_name_in_import(module)
        block.emit('IMPORT_NAME', block.lookup_add_name(fullname))
    if len(args) > 1:
        block.emit('BUILD_TUPLE', len(args))
    return NoCompilation

@make_special('import-from')
def m_import_from(block, args):
    if len(args) < 2:
        raise NoodleSyntaxError("Insufficient arguments to import-from")
    name = dotted_name_in_import(args[0])
    symbols_to_import = args[1:]
    names_to_import = []
    for symbol_to_import in symbols_to_import:
        if not isinstance(symbol_to_import, Symbol):
            raise NoodleSyntaxError("Attempt to import non-symbol")
        names_to_import.append(symbol_to_import.name)
    block.emit_load_constant(tuple(names_to_import))
    block.emit('IMPORT_NAME', block.lookup_add_name(name))
    for name_to_import in names_to_import:
        block.emit('IMPORT_FROM', block.lookup_add_name(name_to_import))
        block.emit_store_name(name_to_import, dup=True)
        block.emit('ROT_TWO')
    block.emit('POP_TOP')
    if len(names_to_import) > 1:
        block.emit('BUILD_TUPLE', len(names_to_import))
    return NoCompilation

@make_special('get-from-module')
def m_get_from_module(block, args):
    if len(args) < 2:
        raise NoodleSyntaxError("Insufficient arguments to get-from-module")
    name = dotted_name_in_import(args[0])
    symbols_to_import = args[1:]
    names_to_import = []
    for symbol_to_import in symbols_to_import:
        if not isinstance(symbol_to_import, Symbol):
            raise NoodleSyntaxError("Attempt to import non-symbol")
        names_to_import.append(symbol_to_import.name)
    block.emit_load_constant(tuple(names_to_import))
    block.emit('IMPORT_NAME', block.lookup_add_name(name))
    for name_to_import in names_to_import:
        block.emit('IMPORT_FROM', block.lookup_add_name(name_to_import))
        block.emit('ROT_TWO')
    block.emit('POP_TOP')
    if len(names_to_import) > 1:
        block.emit('BUILD_TUPLE', len(names_to_import))
    return NoCompilation

@make_special('import-all-from')
def m_import_all_from(block, args):
    if block.__class__ != NoodleModule:
        raise NoodleSyntaxError("import-all-from only allowed at module level")
    for module in args:
        name = dotted_name_in_import(module)
        block.emit_load_constant(('*',))
        block.emit('IMPORT_NAME', block.lookup_add_name(name))
        block.emit('IMPORT_STAR')
    block.emit_load_constant(None)
    return NoCompilation

def try_body(block, arg):
    def make_jumpwrapper(jumpfunc):
        def wrapjump(block, args):
            stackdiff = block.stacklevel - stacklevel_under_block
            block.emit('POP_BLOCK')
            block.stackmove(-stackdiff)
            ret = jumpfunc(block, args)
            block.stackmove(stackdiff)
            return ret
        return wrapjump

    stacklevel_under_block = block.stacklevel
    holdcont = block.nopassmacros.get('continue', None)
    if holdcont is not None:
        block.nopassmacros['continue'] = make_jumpwrapper(holdcont)
    holdbreak = block.nopassmacros.get('break', None)
    if holdbreak is not None:
        block.nopassmacros['break'] = make_jumpwrapper(holdbreak)

    retval = block.compile_piece(arg)

    if holdcont is not None:
        block.nopassmacros['continue'] = holdcont
    if holdbreak is not None:
        block.nopassmacros['break'] = holdbreak

    return retval

@make_special('try')
def m_try(block, args):
    if len(args) < 2:
        return begin(block, args)
    end_jumpers = []
    has_else = False

    for arg in args[1:]:
        if not isinstance(arg, tuple) \
        or len(arg) < 2 \
        or not isinstance(arg[0], Symbol):
            raise NoodleSyntaxError("Malformed except/else/finally clause")
        if arg[0] == Symbol('finally'):
            return m_try_finally(block, args)
        if arg[0] == Symbol('else'):
            has_else = True

    to_exception_checkers = block.emit_setup_except()
    try_body(block, args[0])
    if has_else:
        block.emit('POP_TOP')
    else:
        # can't hold anything on the stack across a POP_BLOCK
        resultvar = block.force_add_local()
        block.emit_store_name(resultvar, dup=False)
    block.emit('POP_BLOCK')

    to_else_or_end = block.emit_jump_forward()
    block.set_jump_target(to_exception_checkers)

    for arg in args[1:]:
        if arg[0].name == "except":
            stacklevel = block.stacklevel
            end_jumpers.append(compile_except_clause(block, arg[1], arg[2:]))
            if block.stacklevel != stacklevel:
                raise NoodleCompilerError(
                    "Unexpected stacklevel %d instead of %d after "
                    "except clause: %s:line %d" % (
                        block.stacklevel,
                        stacklevel,
                        block.filename,
                        block.curlineno
                    )
                )
        elif arg[0].name == "else":
            block.emit('END_FINALLY')
            block.set_jump_target(to_else_or_end)
            to_else_or_end = None
            begin(block, arg[1:])
            break
        else:
            raise NoodleSyntaxError("Illegal clause named %s in try form-"
                                    "expected except or else" % arg[0])
    else:
        block.emit('END_FINALLY')
        block.set_jump_target(to_else_or_end)
        block.emit_load_name(resultvar)
    for end_jump in end_jumpers:
        block.set_jump_target(end_jump)

    return NoCompilation

def m_try_finally(block, args):
    if len(args) != 2 \
    or not isinstance(args[1], tuple) \
    or not isinstance(args[1][0], Symbol) \
    or args[1][0] != Symbol('finally'):
        raise NoodleSyntaxError("Malformed try-finally block")
    block_start = block.emit_setup_finally()
    try_body(block, args[0])
    block.emit('POP_TOP')
    block.emit('POP_BLOCK')
    block.emit_load_constant(None) # <- what's this for? Python does it.
    block.set_jump_target(block_start)
    block.stackmove(-1)
    hold_cont = block.nopassmacros.get('continue', None)
    if hold_cont is not None:
        del block.nopassmacros['continue']
    begin(block, args[1][1:])
    if hold_cont is not None:
        block.nopassmacros['continue'] = hold_cont
    storevar = block.force_add_local()
    block.emit_store_name(storevar, dup=False)
    block.emit('END_FINALLY')
    block.emit_load_name(storevar)
    return NoCompilation

def compile_except_clause(block, exceptarg, steps):
    block.stackmove(3)
    if isinstance(exceptarg, Symbol):
        exceptarg = (exceptarg,)
    if not isinstance(exceptarg, tuple) or \
    len(exceptarg) > 2:
        raise NoodleSyntaxError("Malformed except clause")
    if len(exceptarg) == 2:
        # except clause with parameter
        if not isinstance(exceptarg[1], Symbol):
            raise NoodleSyntaxError("Malformed except clause parameter")
        block.emit('DUP_TOP')
        block.compile_piece(exceptarg[0])
        block.emit('COMPARE_OP',
                   assembling.compare_op['exception match'])
        to_next_exception = block.emit_jump_if_false()
        block.emit('POP_TOP')             # results of compare
        block.emit('POP_TOP')             # exception itself
        block.emit_store_name(exceptarg[1].name, dup=False)  # parameter
        block.emit('POP_TOP')             # traceback
        begin(block, steps)
        jump_to_end = block.emit_jump_forward()
        block.set_jump_target(to_next_exception)
        block.emit('POP_TOP')
    elif len(exceptarg) == 1:
        # except clause with exception only, no parameter
        block.emit('DUP_TOP')
        block.compile_piece(exceptarg[0])
        block.emit('COMPARE_OP',
                   assembling.compare_op['exception match'])
        to_next_exception = block.emit_jump_if_false()
        block.emit('POP_TOP')             # results of compare
        block.emit('POP_TOP')             # exception
        block.emit('POP_TOP')             # parameter
        block.emit('POP_TOP')             # traceback
        begin(block, steps)
        jump_to_end = block.emit_jump_forward()
        block.set_jump_target(to_next_exception)
        block.emit('POP_TOP')
    else:
        # catch-all except clause
        block.emit('POP_TOP')             # exception
        block.emit('POP_TOP')             # parameter
        block.emit('POP_TOP')             # traceback
        begin(block, steps)
        jump_to_end = block.emit_jump_forward()
        block.stackmove(-1)
    return jump_to_end

@make_special('raise')
def m_raise(block, args):
    if len(args) > 3:
        raise NoodleSyntaxError("Too many arguments to raise")
    for arg in args:
        block.compile_piece(arg)
    block.emit('RAISE_VARARGS', len(args))
    return NoCompilation

@make_special('getattribute')
def m_getattribute(block, args):
    if len(args) != 2 \
    or not isinstance(args[1], Symbol):
        raise NoodleSyntaxError("getattribute requires identifier argument")
    block.compile_piece(args[0])
    block.emit('LOAD_ATTR', block.lookup_add_name(args[1].name))
    return NoCompilation

@make_special('class')
def m_class(block, args):
    if len(args) < 1:
        raise NoodleSyntaxError("Improper class definition")
    namedef = args[0]
    bases = ()
    if isinstance(namedef, tuple):
        if len(namedef) != 2:
            raise NoodleSyntaxError("Improper class definition")
        if not isinstance(namedef[1], tuple):
            raise NoodleSyntaxError("bases not in tuple")
        bases = namedef[1]
        namedef = namedef[0]
    if not isinstance(namedef, Symbol):
        raise NoodleSyntaxError("Class name must be symbol")
    classname = namedef.name
    make_class(block, bases, args[1:], classname=classname)
    block.emit_store_name(classname)
    return NoCompilation

@make_special('anon-class')
def m_anon_class(block, args):
    if len(args) < 1:
        raise NoodleSyntaxError("Improper class definition")
    bases = args[0]
    if not isinstance(bases, tuple):
        raise NoodleSyntaxError("bases not in tuple")
    make_class(block, bases, args[1:])
    return NoCompilation

def make_class(block, bases, steps, classname='*anon class*'):
    block.emit_load_constant(classname)
    for base in bases:
        block.compile_piece(base)
    block.emit('BUILD_TUPLE', len(bases))

    # docstring
    docstring = None
    if len(steps) > 0 and isinstance(steps[0], str):
        docstring = steps[0]
        steps = steps[1:]

    block.code.append(CreateSubBlock(
        block.subclass(
            (Symbol('begin'),) + tuple(steps),
            firstlineno=block.curlineno,
            docstring=docstring,
            codename=classname
        ),
        block,
        0
    ))
    block.stackmove(1)
    block.emit('CALL_FUNCTION', 0)
    block.emit('BUILD_CLASS')

@make_special('-list-append-')
def list_append(block, args):
    if len(args) < 2:
        raise NoodleSyntaxError("bad -list-append- call: needs at least 2 args")
    block.compile_piece(args[0])
    for arg in args[1:]:
        block.emit('DUP_TOP')
        block.compile_piece(arg)
        block.emit('LIST_APPEND')
    return NoCompilation

@make_special('gensym')
def m_gensym(block, args):
    return (Symbol('mksymbol'), unique_name())

@make_special('get-iter')
def m_get_iter(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError("bad get-iter call: needs 1 argument")
    block.compile_piece(args[0])
    block.emit('GET_ITER')
    return NoCompilation

def m_yield(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "yield takes exactly one argument (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    block.emit('DUP_TOP')
    block.emit('YIELD_VALUE')
    return NoCompilation

def m_return(block, args):
    begin(block, args)
    block.emit('RETURN_VALUE')
    block.stackmove(1)
    return NoCompilation

@make_special('exec')
def m_exec(block, args):
    # XXX: disallow unqualified exec when there are any cell or free vars
    if len(args) < 1 or len(args) > 3:
        raise NoodleSyntaxError(
            "Invalid exec call; must be between 1 and 3 arguments"
        )
    block.compile_piece(args[0])
    if len(args) > 1:
        block.compile_piece(args[1])
    else:
        block.emit_load_constant(None)
    if len(args) > 2:
        block.compile_piece(args[2])
    else:
        block.emit('DUP_TOP')
    block.code.append(ExecStmt(len(args) == 1))
    block.stackmove(-3)
    return None

@make_special('global')
def m_global(block, args):
    for arg in args:
        if not isinstance(arg, Symbol):
            raise NoodleSyntaxError("arguments to global must be identifiers")
        block.declareds[arg.name] = 'global'
    return None

@make_special('let')
def m_let(block, args):
    if not isinstance(args[0], tuple):
        raise NoodleSyntaxError("bad let call; first arg must be tuple")
    if len(args) < 1:
        raise NoodleSyntaxError("empty let call")

    translator = block.push_var_translator()
    mynumber = unique_name()
    for vardef in args[0]:
        if not isinstance(vardef, tuple):
            raise NoodleSyntaxError(
                "bad let call; variable binding must be tuple"
            )
        if len(vardef) != 2 or not isinstance(vardef[0], Symbol):
            raise NoodleSyntaxError(
                "bad let call; variable binding must be (identifier value)"
            )
        name = vardef[0].name
        mungedname = mynumber + name
        translator[name] = mungedname

    for varname, varvalue in args[0]:
        block.compile_piece(varvalue)
        block.emit_store_name(varname.name, dup=False)
    begin(block, args[1:])

    if block.pop_var_translator() is not translator:
        raise NoodleCompilerError("Unexpected var translator popped")
    return NoCompilation

@make_special('delsubscript')
def delsubscript(block, args):
    if len(args) != 2:
        raise NoodleSyntaxError(
            "delsubscript requires 2 arguments (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    delete_subscript(block, args[1])

def delete_subscript(block, subscript):
    if arg_is_special_symbol(subscript, 'mkslice', 2):
        low, high = subscript[1:]
        if high is None:
            if low is None:
                block.emit('DELETE_SLICE+0')
            else:
                block.compile_piece(low)
                block.emit('DELETE_SLICE+1')
        else:
            if low is None:
                block.compile_piece(high)
                block.emit('DELETE_SLICE+2')
            else:
                block.compile_piece(low)
                block.compile_piece(high)
                block.emit('DELETE_SLICE+3')
    else:
        block.compile_piece(subscript)
        block.emit('DELETE_SUBSCR')

@make_special('delattribute')
def delattribute(block, args):
    if len(args) != 2:
        raise NoodleSyntaxError(
            "delattribute requires 2 arguments (%d given)" % len(args)
        )
    block.compile_piece(args[0])
    delete_attribute(block, args[1])

def delete_attribute(block, attrname):
    if not isinstance(attrname, Symbol):
        raise NoodleSyntaxError("Invalid attribute name")
    block.emit('DELETE_ATTR', block.lookup_add_name(attrname.name))

@make_special('del')
def m_del(block, args):
    for arg in args:
        if arg_is_special_symbol(arg, 'subscript', 2):
            block.compile_piece(arg[1])
            delete_subscript(block, arg[2])
        elif arg_is_special_symbol(arg, 'getattribute', 2):
            block.compile_piece(arg[1])
            delete_attribute(block, arg[2])
        elif isinstance(arg, Symbol):
            block.emit_del_name(arg.name)
        else:
            raise NoodleSyntaxError("bad delete call")

@make_special('del-value')
def del_value(block, args):
    if len(args) != 1 or \
    not isinstance(args[0], Symbol):
        raise NoodleSyntaxError("del-value requires one symbol argument")
    block.emit_load_name(args[0].name)
    m_del(block, args)
    return NoCompilation

@make_special('mkslice')
def mkslice(block, args):
    if len(args) not in (2, 3):
        raise NoodleSyntaxError(
            "mkslice requires 2 or 3 arguments (%d given)" % len(args)
        )
    for arg in args:
        block.compile_piece(arg)
    block.emit('BUILD_SLICE', len(args))
    return NoCompilation

@make_special('quote')
def quote(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "quote takes exactly one argument (%d given)" % len(args)
        )
    arg = args[0]
    if isinstance(arg, tuple):
        for subarg in arg:
            quote(block, (subarg,))
        block.emit('BUILD_TUPLE', len(arg))
    elif isinstance(arg, Symbol):
        block.compile_piece((Symbol('mksymbol'), arg.name))
    else:
        block.compile_piece(arg)
    return NoCompilation

@make_special('quasiquote')
def quasiquote(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "quasiquote takes exactly one argument (%d given)" % len(args)
        )
    arg = args[0]
    if arg_is_special_symbol(arg, 'unquote'):
        unquote(block, arg[1:])
    elif isinstance(arg, tuple):
        curlen = 0
        pieces = 0
        for subarg in arg:
            if arg_is_special_symbol(subarg, 'unquote-splice'):
                if curlen:
                    block.emit('BUILD_TUPLE', curlen)
                unquote(block, subarg[1:])
                if curlen:
                    block.emit('BINARY_ADD')
                curlen = 0
                pieces += 1
            else:
                quasiquote(block, (subarg,))
                curlen += 1
        block.emit('BUILD_TUPLE', curlen)
        for addnum in xrange(pieces):
            block.emit('BINARY_ADD')
    elif isinstance(arg, Symbol):
        block.compile_piece((Symbol('mksymbol'), arg.name))
    elif arg_is_special_symbol(arg, 'unquote-splice'):
        raise NoodleSyntaxError("unquote-splice is meaningful only in tuple")
    else:
        block.compile_piece(arg)
    return NoCompilation

def unquote(block, args):
    if len(args) != 1:
        raise NoodleSyntaxError(
            "unquote requires 1 argument (%d given)" % len(args)
        )
    block.compile_piece(args[0])

@make_special('eval-when')
def eval_when(block, args):
    if len(args) < 1 or not isinstance(args[0], tuple):
        raise NoodleSyntaxError(
            "eval-when requires a list of situations as first argument"
        )
    try:
        situations = set(map(lambda n: n.name, args[0]))
    except AttributeError:
        raise NoodleSyntaxError("non-keyword in situation list")
    body = (Symbol('begin'),) + args[1:]
    if 'compile' in situations:
        from NoodleMain import noodle_compile
        bodycode = noodle_compile(body, block.filename, block.linemap)
        exec bodycode in block.get_compiling_namespace()
    if 'import' in situations:
        return body

def build_arg_list(block, args):
    block.emit('BUILD_TUPLE', 0)
    so_far = 0
    for arg in args:
        if arg_is_special_symbol(arg, 'mkvarargs', 1):
            if so_far:
                block.emit('BUILD_TUPLE', so_far)
                block.emit('BINARY_ADD')
                so_far = 0
            block.emit_load_global('tuple')
            block.compile_piece(arg[1])
            block.emit('CALL_FUNCTION', 1)
            block.emit('BINARY_ADD')
        else:
            block.compile_piece(arg)
            so_far += 1
    if so_far:
        block.emit('BUILD_TUPLE', so_far)
        block.emit('BINARY_ADD')

def args_contain_special_symbol(arglist, sym, symargs=-1):
    for arg in arglist:
        if arg_is_special_symbol(arg, sym, symargs):
            return True
    return False

def arg_is_special_symbol(arg, sym, symargs=-1):
    return isinstance(arg, tuple) \
           and (symargs < 0 or len(arg) == (1 + symargs)) \
           and isinstance(arg[0], Symbol) \
           and arg[0] == Symbol(sym)
