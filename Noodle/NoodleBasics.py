# NoodleBasics

version = '0.1.0'

extension = '.nu'
compiled_extension = '.nuc'

class Symbol(object):
    def __init__(self, name):
        self.__n = name

    def __str__(self):
        return '\\' + self.__n
    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.__n == other.__n

    def __ne__(self, other):
        return not isinstance(other, Symbol) or self.__n != other.__n

    def __hash__(self):
        return hash(self.__n)

    __slots__ = ['__n']

    def getname(self):
        return self.__n
    name = property(getname)

def unique_number_maker(start=0):
    unique_num = [start]
    def unique_number():
        unique_num[0] += 1
        return unique_num[0]
    def unique_name():
        return '_*%d*' % unique_number()
    return unique_number, unique_name
unique_number, unique_name = unique_number_maker()

class NoCompilation:
    pass

import __builtin__
default_macro_namespace = {'mksymbol': Symbol, '__builtins__': __builtin__}
current_macros = {}
