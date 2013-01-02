# error

class NoodleError(Exception):
    pass

class NoodleCompilerError(NoodleError):
    pass

class NoodleMacroError(NoodleError):
    pass

class NoodleSyntaxError(NoodleError):
    pass

class NoodleScannerError(Exception):
    pass
