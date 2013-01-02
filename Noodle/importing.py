# importing Noodle modules

import sys
import os, stat
import new
import NoodleBasics, nucfiles

ext = NoodleBasics.extension
cext = NoodleBasics.compiled_extension

def findmodule(fullname, path=None):
    name = fullname.split('.')[-1]
    for directory in (path or sys.path):
        filename = os.path.join(directory, name)
        if os.access(filename + ext, os.R_OK):
            return NoodleModuleLoader(filename + ext)
        if os.access(filename + cext, os.R_OK):
            return NoodleCompiledModuleLoader(filename + cext)
        try:
            mode = os.stat(filename)[0]
        except OSError:
            continue
        if stat.S_ISDIR(mode):
            initname = os.path.join(filename, '__init__')
            if os.access(initname + ext, os.R_OK):
                return NoodlePackageLoader(filename, initname + ext)
            if os.access(initname + cext, os.R_OK):
                return NoodleCompiledPackageLoader(filename, initname + cext)

class NoodleImporter:
    find_module = staticmethod(findmodule)

def code_from_nu(filename, instream):
    import NoodleMain
    code = NoodleMain.noodle_compile_stream(instream, filename)
    compiledfile = nucfiles.nuc_filename(filename)
    try:
        nucfiles.output_nuc(filename, code, compiledfile)
    except IOError:
        pass
    return code

def code_from_nuc(instream):
    return nucfiles.nuc_code_object(instream)

class NoodleModuleLoader:
    def __init__(self, filename):
        self.filename = filename
        self.f = file(filename, 'r')

    def getcode(self):
        compiledfile = nucfiles.find_nuc(self.filename)
        if compiledfile is not None:
            self.filename = compiledfile
            return code_from_nuc(compiledfile)
        return code_from_nu(self.filename, self.f)

    def setup_path(self, module):
        pass

    def load_module(self, fullname):
        code = self.getcode()
        self.f.close()
        module = sys.modules.setdefault(fullname, new.module(fullname))
        module.__file__ = self.filename
        module.__loader__ = self
        self.setup_path(module)
        exec code in module.__dict__
        NoodleBasics.current_macros.update(
            nucfiles.macros_from_code(code, module.__dict__)
        )
        return module

class NoodleCompiledModuleLoader(NoodleModuleLoader):
    def getcode(self):
        return code_from_nuc(self.f)

class NoodlePackageLoader(NoodleModuleLoader):
    def __init__(self, dirname, initname):
        self.dirname = dirname
        NoodleModuleLoader.__init__(self, initname)

    def setup_path(self, module):
        module.__path__ = [self.dirname]

class NoodleCompiledPackageLoader(NoodlePackageLoader,
                                  NoodleCompiledModuleLoader):
    getcode = NoodleCompiledModuleLoader.getcode

sys.meta_path.append(NoodleImporter())
