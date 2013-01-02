# compiling

import cStringIO
import os
import new
import dispatcher
import assembling
import optimizing
from NoodleBasics import (Symbol, NoCompilation, unique_name, current_macros,
                          default_macro_namespace)
from error import NoodleCompilerError, NoodleSyntaxError
from util import partial

ConstantNames = {
    'None': None,
    'True': True,
    'False': False
}

global_compiling_namespace = {}

class GeneratedCode:
    """Instances of subclasses of this may be inserted into the code list
    of a NoodleBlock. When the NoodleBlock prepares a code-object version
    of itself, each instance's 'prepare' method is called in turn.
    """
    
    def prepare(self, block, index):
        """Expected to return the corresponding bytecode string, or an
        empty string if no bytecode corresponds to this object. That string
        may be of any length; the NoodleBlock will keep track of the current
        byte-address. 'block' is the NoodleBlock instance itself, and 'index' 
        is the current index into the code string.
        """
        pass

class CompileLater(GeneratedCode):
    pass

class ExecStmt(GeneratedCode):
    def __init__(self, is_unqualified):
        self.is_unqualified = is_unqualified

    def prepare(self, block, index):
        if self.is_unqualified \
        and (len(block.cellvars) > 0 or len(block.freevars) > 0):
            raise NoodleSyntaxError("Unqualified exec disallowed when "
                                    "cell or free variables are in scope")
        return assembling.assemble_instruction('EXEC_STMT')

class SimpleOp(GeneratedCode):
    def __init__(self, opname, arg=None):
        self.opnum = assembling.dis.opmap[opname]
        self.arg = arg

    def prepare(self, block, index):
        return assembling.assemble_opcode_arg(self.opnum, self.arg)

class LineNumber(GeneratedCode):
    def __init__(self, lineno):
        self.lineno = lineno

    def prepare(self, block, index):
        block.add_to_lnotab(block.address, self.lineno)
        return ''

class UseName(GeneratedCode):
    def __init__(self, block, varname):
        self.block = block
        self.varname = varname

    def prepare(self, block, index):
        return assembling.assemble_instruction(*self.getop(block, index))

class LoadName(UseName):
    """Used for variable accesses in code when it is not yet known whether
    that variable will be local, global, or cell."""

    def getop(self, block, index):
        # It is assumed block.cellvars is already populated and won't
        # be added to during or after this call.

        num = block.lookup_cell(self.varname)
        if num is not None:
            return block.get_as_declared(self.varname, 'cell')
        num = block.lookup_local(self.varname)
        if num is not None:
            return block.get_as_declared(self.varname, 'local')
        return block.get_as_declared(self.varname, 'global')

class StoreName(UseName):
    """Used for variable assignment in code when it is not yet known whether
    that variable will be local or cell."""

    def getop(self, block, index):
        # It is assumed block.cellvars is already populated and won't
        # be added to during or after this call.

        num = block.lookup_cell(self.varname)
        if num is not None:
            return block.store_as_declared(self.varname, 'cell')
        num = block.lookup_local(self.varname)
        if num is not None:
            return block.store_as_declared(self.varname, 'local')
        raise NoodleCompilerError(
            "StoreName-owned variable not in varnames"
        )

class DelName(UseName):
    """Used for variable deletion in code when it is not yet known whether
    that variable will be global or local."""

    def getop(self, block, index):
        if block.lookup_cell(self.varname) is not None:
            raise NoodleSyntaxError(
                "Attempt to delete variable '%s', referenced in nested scope"
                    % self.varname
            )
        if block.lookup_local(self.varname) is not None:
            return block.del_as_declared(self.varname, 'local')
        raise NoodleCompilerError(
            "DelName-owned variable not in varnames"
        )

class Jump(GeneratedCode):
    def __init__(self):
        self.firstendcodeindex = None  # to be filled in
        self.firstendaddress = None    # to be filled in

    def prepare(self, block, codeindex):
        if self.firstendaddress is None:
            self.firstendaddress = block.address
            self.firstendcodeindex = codeindex
            return ' ' * self.firstendlen
        else:
            block.backpatches.append(
                self.register_backpatch(codeindex, block.address)
            )
            return ' ' * self.lastendlen

class RelativeForwardJump(Jump):
    def __init__(self, opcode):
        Jump.__init__(self)
        self.opcode = opcode
        self.firstendlen = 3
        self.lastendlen = 0

    def register_backpatch(self, lastendcodeindex, lastendaddress):
        return (
            self.firstendcodeindex,
            assembling.assemble_instruction(
                self.opcode,
                lastendaddress - self.firstendaddress - 3
            )
        )

class AbsoluteBackwardJump(Jump):
    def __init__(self):
        Jump.__init__(self)
        self.ops = []
        self.firstendlen = 0
        self.lastendlen = 3

    def register_backpatch(self, lastendcodeindex, lastendaddress):
        op = self.ops[0]
        self.ops = self.ops[1:]
        return (
            lastendcodeindex,
            assembling.assemble_instruction(op, self.firstendaddress)
        )

class NoodleBlock:
    def __init__(self, tree, filename, firstlineno=1, nopassmacros=None,
                 varnames=None, argcount=0, codename='*', parent=None,
                 linemap=None, codeflags=0, docstring=None):

        self.code = []
        self.filename = filename
        self.name = codename
        self.argcount = argcount
        self.var_translators = []

        ## Map of ids of tuples/symbols in input to tuples of
        # (filename, startline, endline)
        if linemap is None:
            linemap = {}
        self.linemap = linemap

        if varnames is None:
            varnames = []
        ## List of arguments that are either local or cell
        self.varnames = varnames

        ## List of arguments that are either global, local, or cell
        self.unknowns = []

        ## List of other names needed in the function
        self.names = []

        ## List of constants used in the code block
        self.constants = [docstring]

        ## Map of variable names to the variable-name list in which
        # they want to belong.
        self.declareds = {}

        ## List of variable names which are to be taken from the function's
        # closure (the func_closure attribute).
        #
        # when appending to freevars, ensure that the corresponding parent
        # block has its variable made into a cellvar.
        self.freevars = []

        ## List of variable names which are referenced by nested blocks.
        # They may also appear in varnames.
        self.cellvars = []

        ## Maximum depth the value stack might reach when executing this
        # code block.
        self.maxstacklevel = 0
        self.stacklevel = 0

        ## 0x2000: future division (standard for Noodle); 0x4: *arguments;
        # 0x8: **kwargs; 0x20: generator
        self.codeflags = 0x2000 | codeflags

        ## Line number table
        self.lnotab = []
        self.lnotab_last_address = 0
        self.lnotab_last_lineno = firstlineno
        self.curlineno = self.firstlineno = firstlineno

        if nopassmacros is None:
            nopassmacros = {}
        self.nopassmacros = nopassmacros
        self.parent = parent

        self.setup_array_control()

        self.subfunc = partial(NoodleFunction,
                               filename=self.filename,
                               linemap=self.linemap,
                               parent=self)
        self.subclass = partial(NoodleClass,
                                filename=self.filename,
                                linemap=self.linemap,
                                parent=self)

        self.loadscopes = {
            'local': ('LOAD_FAST', self.varnames),
            'cell': ('LOAD_DEREF', self.cellvars),
            'free': ('LOAD_DEREF', self.freevars),
            'global': ('LOAD_GLOBAL', self.names)
        }
        self.storescopes = {
            'local': ('STORE_FAST', self.varnames),
            'cell': ('STORE_DEREF', self.cellvars),
            'free': ('STORE_DEREF', self.freevars),
            'global': ('STORE_GLOBAL', self.names)
        }
        self.delscopes = {
            'local': ('DELETE_FAST', self.varnames),
            'global': ('DELETE_GLOBAL', self.names)
        }

        self.extra_setup()
        self.compile_piece(tree)
        self.close_block()
        self.compile_deferreds()
        self.codestring = self.arrange_code(
            optimizing.OptimizeBytecode(self, self.code)
        )

    def setup_array_control(self):
        self.lookup_local, self.add_local, self.lookup_add_local = \
            self.make_lookuper('varnames')
        self.lookup_name, self.add_name, self.lookup_add_name = \
            self.make_lookuper('names')
        self.lookup_free = self.make_lookuper('freevars')[0]
        self.lookup_cell = self.make_lookuper('cellvars')[0]
        self.lookup_unknown = self.make_lookuper('unknowns')[0]

    def localmacro(self, **args):
        if self.parent is not None:
            self.parent.localmacro(**args)
        else:
            raise NoodleSyntaxError("can't define macro in this block")

    def get_compiling_namespace(self):
        if self.parent is not None:
            return self.parent.get_compiling_namespace()
        return global_compiling_namespace

    def extra_setup(self):
        pass

    def close_block(self):
        if self.codeflags & 0x20:
            # generator can't return a value.
            self.emit('POP_TOP')
            self.emit_load_constant(None)
        self.emit('RETURN_VALUE')

    def stackmove(self, delta):
        self.stacklevel += delta
        if self.stacklevel > self.maxstacklevel:
            self.maxstacklevel = self.stacklevel
        if self.stacklevel < 0:
            self.stacklevel = 0

    def make_lookuper(self, attr):
        varlist = getattr(self, attr)
        def lookup(name):
            for index in range(len(varlist) - 1, -1, -1):
                if varlist[index] == name:
                    return index
        def add(name):
            varlist.append(name)
            return len(varlist) - 1
        def lookup_add(name):
            num = lookup(name)
            if num is None:
                num = add(name)
            return num
        return lookup, add, lookup_add

    def add_constant(self, value):
        for cnum, cvalue in enumerate(self.constants):
            if cvalue is value:
                return cnum
        self.constants.append(value)
        return len(self.constants) - 1

    def lookup_macro(self, macroname):
        # check current_macros before nopassmacros since make_recursive_apply
        # macros (tail call optimization) get put in nopassmacros, and we
        # want same-named macros to take precedence
        macro = current_macros.get(macroname, None)
        if macro is not None:
            return macro
        else:
            return self.nopassmacros.get(macroname, None)

    def make_cellvar(self, name):
        if self.lookup_cell(name) is not None:
            return True
        if self.lookup_free(name) is not None:
            return True
        if self.lookup_local(name) is not None:
            self.add_to_cellvars(name)
            return True
        if self.make_cellvar_in_parent(name):
            self.freevars.append(name)
            return True
        return False

    def make_cellvar_in_parent(self, varname):
        if self.parent is None:
            return False
        return self.parent.make_cellvar(varname)

    def add_to_cellvars(self, name):
        """Make sure if any arguments are set as cellvars, they appear
        first and in order in the cellvars list. Otherwise, some subtle
        errors may occur in certain closures. Unclear whether this is due
        to a bug in the python VM, or due to some undocumented
        requirement."""

        if not isinstance(name, str):
            raise NoodleCompilerError("%s is not a string" % repr(name))
        num = self.lookup_local(name)
        if num is not None and num < self.argcount:
            insert_at = 0
            for previous_arg in range(num):
                if insert_at >= len(self.cellvars):
                    break
                if self.cellvars[insert_at] == self.varnames[previous_arg]:
                    insert_at += 1
        else:
            insert_at = len(self.cellvars)
        self.cellvars.insert(insert_at, name)

    def emit(self, op, arg=None, lineno=None):
        self.emit_set_lineno(lineno)
        self.code.append(SimpleOp(op, arg))
        self.stackmove(assembling.stackchange(op, arg))
        if op == 'YIELD_VALUE':
            self.codeflags |= 0x20  # generator flag

    def _real_emit_set_lineno(self, num):
        if num is None or num <= self.curlineno:
            return
        self.curlineno = num
        self.code.append(LineNumber(num))

    def emit_set_lineno(self, lineno):
        if isinstance(lineno, int):
            self._real_emit_set_lineno(lineno)
        elif isinstance(lineno, tuple) or isinstance(lineno, Symbol):
            start, end, fname = self.linemap.get(id(lineno), (0, 0, None))
            if fname == self.filename:
                self._real_emit_set_lineno(start)

    def push_var_translator(self):
        newtranslator = {}
        self.var_translators.append(newtranslator)
        return newtranslator

    def pop_var_translator(self):
        return self.var_translators.pop()

    def translate_name(self, name):
        for translator in reversed(self.var_translators):
            changed = translator.get(name, None)
            if changed is not None:
                return changed
        return name

    def emit_load_constant(self, const, lineno=None):
        num = self.add_constant(const)
        self.emit('LOAD_CONST', num, lineno)

    def emit_load_name(self, varname, lineno=None):
        self.emit_set_lineno(lineno)
        varname = self.translate_name(varname)
        self.stackmove(1)
        # If variable has a declared scope, use it
        stype = self.declareds.get(varname, None)
        if stype is not None:
            self.code.append(SimpleOp(*self.get_as_declared(varname, stype)))
            return
        # If it is already determined to be a free variable, load it that way
        num = self.lookup_free(varname)
        if num is not None:
            self.code.append(SimpleOp(*self.get_as_declared(varname, 'free')))
            return
        # If it is already determined to be local/cell or local/cell/global,
        # use a LoadName instance
        if (self.lookup_local(varname) is not None) \
        or (self.lookup_unknown(varname) is not None):
            self.code.append(LoadName(self, varname))
            return

        # scope not already determined.

        # If var is in an enclosing block, make it free
        if self.make_cellvar_in_parent(varname):
            self.code.append(SimpleOp(*self.get_as_declared(varname, 'free')))
            return
        # otherwise, make a LoadName instance
        self.code.append(LoadName(self, varname))
        self.unknowns.append(varname)

    def force_add_local(self, varname=None):
        if varname is None:
            varname = unique_name()
        varlist = self.loadscopes['local'][1]
        varlist.append(varname)
        return varname

    def emit_store_name(self, varname, lineno=None, dup=True):
        self.emit_set_lineno(lineno)
        varname = self.translate_name(varname)
        if dup:
            self.emit('DUP_TOP')
        self.stackmove(-1)
        # If variable has a declared scope, use it
        stype = self.declareds.get(varname, None)
        if stype is not None:
            self.code.append(SimpleOp(*self.store_as_declared(varname, stype)))
            return
        # If it is already determined to be a free variable, store it that way
        if self.lookup_free(varname) is not None:
            self.code.append(SimpleOp(*self.store_as_declared(varname, 'free')))
            return
        # If var is already in varnames, make a StoreName instance
        if self.lookup_local(varname) is not None:
            self.code.append(StoreName(self, varname))
            return
        # If var is already in unknowns, make a StoreName instance and add
        # variable to varnames
        if self.lookup_unknown(varname) is not None:
            self.code.append(StoreName(self, varname))
            self.varnames.append(varname)
            return

        # scope not already determined.

        # If var is in an enclosing block, make it free
        if self.make_cellvar_in_parent(varname):
            self.code.append(SimpleOp(*self.store_as_declared(varname, 'free')))
            return
        # otherwise, make a StoreName instance
        self.code.append(StoreName(self, varname))
        self.varnames.append(varname)

    def emit_del_name(self, varname, lineno=None):
        self.emit_set_lineno(lineno)
        varname = self.translate_name(varname)
        stype = self.declareds.get(varname, None)
        if stype is not None:
            self.code.append(SimpleOp(*self.del_as_declared(varname, stype)))
            return
        # Add var to varnames--it must be local if it's not global.
        # There is no DELETE_DEREF.
        self.varnames.append(varname)
        self.code.append(DelName(self, varname))

    def emit_load_global(self, varname, lineno=None):
        """Used when a global is explicitly wanted, rather than a local
        with the same name. Is this a bad idea? Some macros use it for
        things like tuple() and so on, since any locally defined object
        with that name is not likely to be what they want.
        """

        self.emit_set_lineno(lineno)
        self.code.append(SimpleOp(*self.get_as_declared(varname, 'global')))

    def get_as_declared(self, varname, scopetype):
        loadop, varlist = self.loadscopes[scopetype]
        for num, var in enumerate(varlist):
            if varname == var:
                usenum = num
                break
        else:
            usenum = len(varlist)
            varlist.append(varname)
        return loadop, usenum

    def store_as_declared(self, varname, scopetype):
        storeop, varlist = self.storescopes[scopetype]
        for num, var in enumerate(varlist):
            if varname == var:
                usenum = num
                break
        else:
            usenum = len(varlist)
            varlist.append(varname)
        return storeop, usenum

    def del_as_declared(self, varname, scopetype):
        delop, varlist = self.delscopes[scopetype]
        for num, var in enumerate(varlist):
            if varname == var:
                usenum = num
                break
        else:
            usenum = len(varlist)
            varlist.append(varname)
        return delop, usenum

    def compile_deferreds(self):
        """Subblocks need to be compiled after this block has been compiled,
        so this block can report which variables are defined in its scope.
        """

        for index in range(len(self.code)):
            if isinstance(self.code[index], CompileLater):
                self.code[index].compile()

    def emit_jump_if_false(self):
        jump = RelativeForwardJump('JUMP_IF_FALSE')
        self.code.append(jump)
        return jump

    def emit_jump_if_true(self):
        jump = RelativeForwardJump('JUMP_IF_TRUE')
        self.code.append(jump)
        return jump

    def emit_jump_forward(self):
        jump = RelativeForwardJump('JUMP_FORWARD')
        self.code.append(jump)
        return jump

    def emit_setup_except(self):
        jump = RelativeForwardJump('SETUP_EXCEPT')
        self.code.append(jump)
        return jump

    def emit_setup_finally(self):
        jump = RelativeForwardJump('SETUP_FINALLY')
        self.code.append(jump)
        return jump

    def emit_for_iter(self):
        jump = RelativeForwardJump('FOR_ITER')
        self.code.append(jump)
        return jump

    # This shouldn't be needed, since JUMP_FORWARD should work fine
    #def emit_jump_absolute_forward(self):
    #    jump = AbsoluteForwardJump('JUMP_ABSOLUTE')
    #    self.code.append(jump)
    #    return jump

    def emit_jump_absolute_backward(self, target):
        self.code.append(target)
        target.ops.append('JUMP_ABSOLUTE')

    def emit_continue(self, target):
        self.code.append(target)
        target.ops.append('CONTINUE_LOOP')

    def set_jump_target(self, jump):
        self.code.append(jump)

    def set_backward_jump_target(self):
        jump = AbsoluteBackwardJump()
        self.code.append(jump)
        return jump

    def do_backpatches(self, backpatches):
        for codeindex, op in backpatches:
            self.code[codeindex] = op

    def arrange_code(self, codelist):
        """Do last-minute conversions of special objects in the codestream;
        uses of variables with undecided scope, backpatches, and line
        number codes. By this point, cellvars is populated.
        """

        self.backpatches = []
        self.address = 0
        for index in range(len(codelist)):
            codelist[index] = codelist[index].prepare(self, index)
            self.address += len(codelist[index])
        self.do_backpatches(self.backpatches)
        return ''.join(codelist)

    def nlocals(self):
        return len(self.varnames)

    def as_code_object(self):
        return new.code(
            self.argcount,
            self.nlocals(),
            self.maxstacklevel,
            self.codeflags,
            self.codestring,
            tuple(self.constants),
            tuple(self.names),
            tuple(self.varnames),
            self.filename,
            self.name,
            self.firstlineno,
            self.make_lnotab(),
            tuple(self.freevars),
            tuple(self.cellvars)
        )

    def add_to_lnotab(self, address, lineno):
        address_offset = address - self.lnotab_last_address
        lineno_offset = lineno - self.lnotab_last_lineno

        if address_offset > 0xff:
            self.lnotab.append((0xff, 0))
            self.lnotab_last_address += 0xff
            self.add_to_lnotab(address, lineno)
        elif lineno_offset > 0xff:
            self.lnotab.append((address_offset, 0xff))
            self.lnotab_last_address = address
            self.lnotab_last_lineno += 0xff
            self.add_to_lnotab(address, lineno)
        else:
            self.lnotab.append((address_offset, lineno_offset))
            self.lnotab_last_address = address
            self.lnotab_last_lineno = lineno

    def make_lnotab(self):
        return ''.join([(chr(a) + chr(ln)) for a, ln in self.lnotab])

    @dispatcher.genericmethod
    def compile_piece(self, piece):
        if type(piece) not in (unicode, str, int, float, long, bool,
                               type(None)):
            raise NoodleCompilerError(
                "No compile smarts for object %s" % repr(piece)
            )
        self.emit_load_constant(piece)

    @compile_piece.with_types(tuple)
    def compile_tuple(self, tup):
        self.emit_set_lineno(tup)
        if len(tup) < 1:
            self.emit('BUILD_TUPLE', 0)
            return
        stacklevel = self.stacklevel
        macfunc = None
        if isinstance(tup[0], Symbol):
            macfunc = self.lookup_macro(tup[0].name)
        if macfunc is not None:
            tup = tup[1:]
        else:
            macfunc = self.lookup_macro('apply')
            if macfunc is None:
                raise NoodleCompilerError("No 'apply' macro- can't make calls!")
        self.run_macro(macfunc, tup)
        if self.stacklevel != stacklevel + 1:
            raise NoodleCompilerError("Unexpected stacklevel %d instead of %d after call to %s. line %d, file %s" % (self.stacklevel, stacklevel + 1, macfunc, self.curlineno, self.filename))

    @compile_piece.with_types(Symbol)
    def compile_symbol(self, sym):
        self.emit_set_lineno(sym)
        try:
            val = ConstantNames[sym.name]
        except KeyError:
            self.emit_load_name(sym.name, sym)
        else:
            self.emit_load_constant(val, sym)

    @compile_piece.with_values(NoCompilation)
    def compile_nothing(self, n):
        pass

    def run_macro(self, macro, args):
        return self.compile_piece(macro(self, args))

class NoodleModule(NoodleBlock):
    def extra_setup(self):
        self.subfunc = partial(self.subfunc, parent=None)
        self.subclass = partial(self.subclass, parent=None)
        self.loadscopes = {
            'local': ('LOAD_NAME', self.names),
            'global': ('LOAD_GLOBAL', self.names)
        }
        self.storescopes = {
            'local': ('STORE_NAME', self.names),
            'global': ('STORE_GLOBAL', self.names)
        }
        self.delscopes = {
            'local': ('DELETE_NAME', self.names),
            'global': ('DELETE_GLOBAL', self.names)
        }
        self.localmacros = {}

        # XXX: ?
        # XXX: ?
        self.compiling_namespace = default_macro_namespace.copy()
 
    def localmacro(self, name, code, defaults):
        self.localmacros[name] = (defaults, code)

    def get_compiling_namespace(self):
        return self.compiling_namespace

    def nlocals(self):
        return 0

    def as_code_object(self):
        self.store_macros(self.localmacros)
        return NoodleBlock.as_code_object(self)

    def store_macros(self, macrodict):
        self.constants.append(macrodict)

class NoodleFunction(NoodleBlock):
    pass

class NoodleClass(NoodleBlock):
    def extra_setup(self):
        self.loadscopes = {
            'local': ('LOAD_NAME', self.names),
            'cell': ('LOAD_DEREF', self.cellvars),
            'free': ('LOAD_DEREF', self.freevars),
            'global': ('LOAD_GLOBAL', self.names)
        }
        self.storescopes = {
            'local': ('STORE_NAME', self.names),
            'cell': ('STORE_DEREF', self.cellvars),
            'free': ('STORE_DEREF', self.freevars),
            'global': ('STORE_GLOBAL', self.names)
        }
        self.delscopes = {
            'local': ('DELETE_NAME', self.names),
            'global': ('DELETE_GLOBAL', self.names)
        }
        self.emit_load_global('__name__')
        self.emit_store_name('__module__', dup=False)
        if self.constants[0] is not None:
            self.emit('LOAD_CONST', 0)
            self.emit_store_name('__doc__', dup=False)
        # 0x2: CO_NEWLOCALS. This needs to be set for a class body, for
        # reasons which aren't competely clear.
        self.codeflags |= 0x2

    def close_block(self):
        self.emit('POP_TOP')
        self.emit('LOAD_LOCALS')
        NoodleBlock.close_block(self)

    def make_cellvar(self, name):
        # classes don't share their variables with nested scopes.
        if self.make_cellvar_in_parent(name):
            self.freevars.append(name)
            return True
        return False

    def nlocals(self):
        return 0

def noodle_compile_tree(tree, filename='<nofilename>', linemap=None):
    return NoodleModule(
        tree, 
        filename,
        linemap=linemap
    ).as_code_object()
