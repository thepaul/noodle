# NoodleMain

import reader
import nucfiles
import compiling
import sys
from NoodleBasics import Symbol, current_macros
import __builtin__
from cStringIO import StringIO

__builtin__.mksymbol = Symbol

def run_noodle(codeobj):
    """Executes a code object and returns the exit code

    Catches and handles any exceptions thrown as appropriate for an execution
    context. Returns the error code for running the function; 0 for normal
    execution, 1 if an unhandled exception was thrown, or another exit value if
    a SystemExit was thrown with a number.
    """

    import __builtin__
    import importing
    import runtime
    noodle_builtins = runtime._items.copy()
    noodle_builtins['__builtins__'] = __builtin__
    noodle_builtins['__name__'] = '__main__'
    noodlefunc = type(run_noodle)(codeobj, noodle_builtins)
    try:
        noodlefunc()
    except SystemExit, e:
        if not isinstance(e.code, int):
            sys.stderr.write(str(e.code) + '\n')
            return 1
        return e.code
    except:
        import traceback
        t, v, tb = sys.exc_info()
        traceback.print_exception(t, v, tb.tb_next, file=sys.stderr)
        return 1
    return 0

def noodle_compile(tree, filename="*", linemap=None):
    return compiling.noodle_compile_tree(
        tree,
        filename,
        linemap=linemap
    )

def noodle_compile_str(codestring, filename="*"):
    return noodle_compile_stream(StringIO(codestring), filename)

def noodle_compile_stream(instream, filename=None):
    if filename is None:
        try:
            filename = instream.name
        except AttributeError:
            filename = '*unnamed-stream*'
    r = reader.Reader(instream, filename=filename)
    return noodle_compile((Symbol('begin'),) + r.read_elements(),
                          filename,
                          linemap=r.linemap)

def noodle_compile_file(filename):
    return noodle_compile_stream(
        file(filename, 'U'),
        filename
    )

def noodle_to_nuc(infilename, outfilename=None):
    nucfiles.output_nuc(
        infilename,
        noodle_compile_file(infilename),
        outfilename
    )

def execfile(nu_file):
    """Execute the given noodle source, or its associated compiled-bytecode
    file if one is found with the same timestamp. Returns the exit code.
    """

    nucname = nucfiles.find_nuc(nu_file)
    if nucname is not None:
        return run_noodle(nucfiles.nuc_code_object(nucname))

    # Either no .nuc, or timestamps don't match
    codeobj = noodle_compile_file(nu_file)
    try:
        nucfiles.output_nuc(nu_file, codeobj, nucname)
    except IOError:
        pass
    return run_noodle(codeobj)

import importing  # must be done after noodle_compile and friends are defined
import Noodle
import builtins

current_macros.update(builtins.predefineds)

import macros
standard_macros = current_macros.copy()
