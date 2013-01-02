# assembling

import dis
import struct
from error import *

compare_op = dict((which, num) for num, which in enumerate(dis.cmp_op))

def assemble(tuples):
    return ''.join([assemble_instruction(*tup) for tup in tuples]) 

def assemble_instruction(opname, arg=None):
    return assemble_opcode_arg(dis.opmap[opname], arg)

def assemble_opcode_arg(opcode, arg=None):
    prefix = ''
    oparg = ''
    if opcode >= dis.HAVE_ARGUMENT:
        if arg is None:
            raise NoodleCompilerError("op %s given without argument" %
                                      dis.opname[opcode])
        if arg > 0xffff:
            oparg = struct.pack('<L', arg)
            prefix = chr(dis.EXTENDED_ARG) + oparg[2:]
            oparg = oparg[:2]
        else:
            oparg = struct.pack('<H', arg)
    return ''.join([prefix, chr(opcode), oparg])

stackchanges = {
    'POP_TOP': -1,
    'DUP_TOP': 1,
    'SLICE+1': -1,
    'SLICE+2': -1,
    'SLICE+3': -2,
    'STORE_SLICE+0': -2,
    'STORE_SLICE+1': -3,
    'STORE_SLICE+2': -3,
    'STORE_SLICE+3': -4,
    'DELETE_SLICE+0': -1,
    'DELETE_SLICE+1': -2,
    'DELETE_SLICE+2': -2,
    'DELETE_SLICE+3': -3,
    'STORE_SUBSCR': -3,
    'DELETE_SUBSCR': -2,
    'PRINT_EXPR': -1,
    'PRINT_ITEM': -1,
    'PRINT_ITEM_TO': -2,
    'PRINT_NEWLINE_TO': -1,
    'LOAD_LOCALS': 1,
    'RETURN_VALUE': -1,
    'YIELD_VALUE': -1,
    'IMPORT_STAR': -1,
    'EXEC_STMT': -3,
    'BUILD_CLASS': -2,
    'STORE_NAME': -1,
    'STORE_ATTR': -2,
    'DELETE_ATTR': -1,
    'STORE_GLOBAL': -1,
    'LOAD_CONST': 1,
    'LOAD_NAME': 1,
    'BUILD_MAP': 1,
    'COMPARE_OP': -1,
    'IMPORT_NAME': 0,
    'IMPORT_FROM': 1,
    'FOR_ITER': 1,
    'LOAD_GLOBAL': 1,
    'LOAD_FAST': 1,
    'STORE_FAST': -1,
    'LOAD_CLOSURE': 1,
    'LOAD_DEREF': 1,
    'STORE_DEREF': -1,
    'LIST_APPEND': -2
}

def stackchange(opname, arg):
    def func_stack_change(arg):
        # number of positionals + twice the number of keyword args
        return -((arg & 0xff) + 2 * (arg >> 8))

    if opname.startswith('BINARY_') or opname.startswith('INPLACE_'):
        return -1
    elif opname in ('BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SLICE', 'RAISE_VARARGS'):
        return 1 - arg
    elif opname == 'UNPACK_SEQUENCE':
        return arg - 1
    elif opname == 'DUP_TOPX':
        return arg
    elif opname == 'CALL_FUNCTION':
        return func_stack_change(arg)
    elif opname == 'MAKE_FUNCTION':
        return -arg
    elif opname == 'MAKE_CLOSURE':
        # not quite correct; should also subtract number of free variables
        #  in code object at TOS
        return -arg
    elif opname in ('CALL_FUNCTION_VAR', 'CALL_FUNCTION_KW'):
        return func_stack_change(arg) - 1
    elif opname == 'CALL_FUNCTION_VAR_KW':
        return func_stack_change(arg) - 2
    else:
        return stackchanges.get(opname, 0)
