# nucfiles

import os, marshal, struct
import NoodleBasics

def nuc_filename(infilename):
    return os.path.splitext(infilename)[0] + NoodleBasics.compiled_extension

def output_nuc(infilename, codeobj, outfile=None):
    import imp
    if outfile is None:
        outfile = nuc_filename(infilename)
    f = file(outfile, 'wb')
    f.write('\0\0\0\0')  # don't set the magic number until file is complete
    f.write(struct.pack('<L', long(os.stat(infilename).st_mtime)))
    marshal.dump(codeobj, f)
    f.flush()
    f.seek(0, 0)
    f.write(imp.get_magic())
    f.close()
    if os.name == "mac":
        import MacOS
        MacOS.SetCreatorAndType(outfile, 'Pyth', 'PYC ')

def nuc_code_object(nuc_file):
    """Returns the code object contained in a .nuc file. Accepts both
    filenames (strings) and file-like objects."""

    if isinstance(nuc_file, str):
        nuc_file = file(nuc_file, 'rb')
    nuc_file.seek(8)
    return marshal.load(nuc_file)

def find_nuc(nu_file):
    """If the specified source file has a corresponding ready-compiled
    file (.nuc) with a matching timestamp, returns the filename of that
    .nuc file. Otherwise, returns None.
    """

    f = file(nu_file, 'U')
    nucname = nuc_filename(nu_file)
    try:
        nuc = file(nucname, 'rb')
    except IOError:
        pass
    else:
        nuc.seek(4, 0)
        nuctimestamp = struct.unpack('<L', nuc.read(4))[0]
        try:
            timestamp = long(os.fstat(f.fileno()).st_mtime)
        except AttributeError:
            timestamp = long(os.stat(nu_file).st_mtime)
        f.close()
        nuc.close()
        if timestamp == nuctimestamp:
            return nucname

def find_nufile_in_path(modulename, path=None):
    import sys
    fname = modulename + NoodleBasics.extension
    if path is None:
        path = sys.path
    for piece in path:
        full = os.path.join(piece, fname)
        if os.access(full, os.R_OK):
            return full
    raise ImportError("No noodle-module named %s" % modulename)

def macrofunc_from_macrocode(code, numdefaults, macronamespace):
    mfunc = type(macrofunc_from_macrocode)(
        code,
        macronamespace,
        code.co_name,
        (None,) * numdefaults
    )
    def runmacro(block, args):
        return mfunc(*args)
    runmacro.func_name = code.co_name
    return runmacro

def macros_from_code(modulecode, macronamespace):
    consts = modulecode.co_consts
    if len(consts) < 1:
        return {}
    macrodict = consts[-1]
    if not isinstance(macrodict, dict):
        return {}
    try:
        return dict(
            (name, macrofunc_from_macrocode(co, numdefaults, macronamespace))
            for name, (numdefaults, co) in macrodict.iteritems()
        )
    except TypeError:
        # improper macro-storage block; give up
        return {}
