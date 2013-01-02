# reader.py

import sys
import array
from error import NoodleSyntaxError
from util import listsplit
from NoodleBasics import *

def thrower(err, *args):
    def callable_thrower(*a):
        raise err(*args)
    return callable_thrower

def invalidchar(stream, c):
    raise NoodleSyntaxError("Invalid character %s read" % repr(c))

_default_macrochars = [invalidchar] * 256
_default_terminating = array.array('b', [0] * 256)

def crange(lo, hi):
    return ''.join([chr(i) for i in range(ord(lo), ord(hi) + 1)])

tokenchars = set(crange('a', 'z') + crange('A', 'Z') + crange('0', '9') +
                 '!$%^&*~<>/?;|-_=+')
spacechars = set("\t\n\x0b\x0c\r ")
digits = crange('0', '9')

def new_default_readtable():
    return copy_readtable((
        _default_macrochars,
        _default_terminating
    ))

def copy_readtable(r):
    return tuple([i[:] for i in r])

class ReaderStopReading(Exception): pass
class ReaderIgnore(Exception): pass

_isspace = array.array('b', [0] * 256)
for ws in spacechars:
    _isspace[ord(ws)] = True
def isspace(c):
    return bool(_isspace[ord(c)])

def default_reader_macro(chars, isterminating=False):
    def register_macro(f):
        for char in chars:
            _default_macrochars[ord(char)] = f
            _default_terminating[ord(char)] = isterminating
        return f
    return register_macro

default_reader_macro(spacechars, isterminating=True)(thrower(ReaderIgnore))

@default_reader_macro('#', isterminating=True)
def read_comment(reader, c):
    while True:
        c = reader.getc()
        if c in ('\n', ''):
            raise ReaderIgnore

def read_delimited_elements(reader, endc):
    oldinfo = reader.set_macro_character(
        endc, thrower(ReaderStopReading), isterminating=True
    )
    try:
        return reader.read_elements(eoferror=True)
    finally:
        reader.set_macro_character(endc, *oldinfo)

@default_reader_macro(':', isterminating=True)
def read_separator(reader, c):
    return Symbol(c)

def read_separated_elements(reader, separator, endc):
    oldinfo = reader.set_macro_character(separator, read_separator, isterminating=True)
    try:
        return tuple(listsplit(
            read_delimited_elements(reader, endc),
            Symbol(separator)
        ))
    finally:
        reader.set_macro_character(separator, *oldinfo)

@default_reader_macro('.', isterminating=True)
def read_dot(reader, c):
    c = reader.peekc()
    if isspace(c):
        return Symbol('.')
    elif c.isdigit():
        return read_number(reader, '.')
    obj = reader.read()
    next = reader.getc()
    if next != '.':
        raise NoodleSyntaxError("Dotted object with no attributes")
    while next == '.':
        attr = reader.read()
        obj = (
            Symbol(isinstance(attr, Symbol) and 'getattribute' or 'getattr'),
            obj,
            attr
        )
        next = reader.getc()
    reader.unread(next)
    return obj

@default_reader_macro('(', isterminating=True)
def read_tuple(reader, c):
    elements = iter(read_delimited_elements(reader, ')'))
    acc = []
    try:
        for e in elements:
            if e == Symbol(':'):
                acc[-1] = (Symbol('mkkeyword'), acc[-1], elements.next())
            else:
                list.append(acc, e)
    except (IndexError, StopIteration), e:
        raise NoodleSyntaxError("Bad syntax for keyword argument (%s)" % str(e))
    return tuple(acc)

@default_reader_macro('[', isterminating=True)
def read_list(reader, c):
    elements = read_delimited_elements(reader, ']')
    # special case empty [] as \[]
    if len(elements) == 0:
        return (Symbol('mklist'),)
    object = elements[0]
    slice_parts = listsplit(elements[1:], Symbol(':'))
    if len(slice_parts) == 1:
        return (Symbol('subscript'), object) + tuple(slice_parts[0])
    slice = []
    for e in slice_parts:
        if len(e) == 0:
            slice.append(None)
        elif len(e) == 1:
            slice.append(e[0])
        else:
            raise NoodleSyntaxError("Invalid slice: multiple values")
    return (Symbol('subscript'), object, (Symbol('mkslice'),) + tuple(slice))

@default_reader_macro('{')
def read_dict(reader, c):
    readlist = read_separated_elements(reader, ':', '}')
    if len(readlist) == 1 and len(readlist[0]) == 0:
        return (Symbol('mkdict'),)
    if len(readlist) == 1 \
    or len(readlist[0]) != 1 \
    or len(readlist[-1]) != 1 \
    or sum([int(len(p) != 2) for p in readlist[1:-1]]) > 0:
        raise NoodleSyntaxError("Bad syntax for {}")
    return (Symbol('mkdict'),) + tuple(
        [(readlist[i][-1], readlist[i+1][0]) for i in range(len(readlist) - 1)]
    )

@default_reader_macro('@')
def read_at(reader, c):
    c = reader.getc()
    if c == '@':
        return (Symbol('mkkwargs'), reader.read())
    reader.unread(c)
    return (Symbol('mkvarargs'), reader.read())

@default_reader_macro('\\')
def read_escape(reader, c):
    next = reader.getc()
    if next == '[':
        return (Symbol("mklist"),) + read_delimited_elements(reader, ']')
    elif next == '(':
        return (Symbol("mktuple"),) + read_delimited_elements(reader, ')')
    else:
        reader.unread(next)
        escaped_token = reader.read()
        if isinstance(escaped_token, Symbol):
            return (Symbol("mksymbol"), escaped_token.name)
        else:
            return escaped_token

@default_reader_macro(tokenchars)
def read_symbol(reader, c):
    chars = [c]
    while True:
        c = reader.getc()
        if c == '':
            break
        if c in ('"', "'") and len(chars) <= 2:
            cstr = ''.join(chars).lower()
            if cstr in ('u', 'r', 'ur'):
                return read_string_constant(reader, c, cstr)
        if reader.terminating[ord(c)]:
            reader.unread(c)
            break
        if c not in tokenchars:
            raise NoodleSyntaxError("Illegal character %s in token" % repr(c))
        list.append(chars, c)
    tokstr = ''.join(chars)
    return Symbol(tokstr)

@default_reader_macro(digits)
def read_number(reader, c):
    chars = [c]
    while True:
        c = reader.getc()
        if c == '':
            break
        if reader.terminating[ord(c)]:
            if c != '.':  # override any reader macros defined for .
                reader.unread(c)
                break
        list.append(chars, c)
    tokstr = ''.join(chars)
    if tokstr[-1] in ('l', 'L'):
        try:
            return long(tokstr[:-1])
        except ValueError:
            raise NoodleSyntaxError("invalid long: %s" % tokstr)
    try:
        return int(tokstr, 0)
    except ValueError:
        try:
            return float(tokstr)
        except ValueError:
            raise NoodleSyntaxError("invalid number: %s" % tokstr)

@default_reader_macro('+-')
def read_number_or_symbol(reader, c):
    use = read_symbol
    next = reader.getc()
    if next.isdigit():
        use = read_number
    elif next == '.' and reader.peekc().isdigit():
        use = read_number
    reader.unread(next)
    return use(reader, c)

def isoctaldigits(c):
    if c:
        for char in c:
            if char < '0' or char > '7':
                break
        else:
            return True
    return False

def read_octal_escape(reader, c):
    code = ord(c) - ord('0')
    for i in range(2):
        c = reader.getc()
        if not isoctaldigits(c):
            break
        code = code * 8 + (ord(c) - ord('0'))
    return chr(code)

def ishexdigits(str):
    return str.lstrip('1234567890abcdef') == ''

def string_escape(reader, c):
    def get_chars(num):
        return ''.join([reader.getc() for i in range(num)])
    next = reader.getc()
    if isoctaldigits(next):
        return read_octal_escape(reader, next)
    if next == 'x':
        hexcode = reader.getc() + reader.getc()
        if len(hexcode) != 2 or not ishexdigits(hexcode):
            raise ValueError("invalid \\x escape")
        return chr(int(hexcode, 16))
    return {
        '\n': '',
        '\\': '\\',
        "'": "'",
        '"': '"',
        'a': '\a',
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        't': '\t',
        'v': '\v',
    }.get(next, '\\' + next)

def raw_escape(reader, c):
    return c + reader.getc()

def unicode_escape(subescapereader):
    def unicode_escape_reader(reader, c):
        next = reader.getc()
        if next == 'u':
            hexcode = ''.join([reader.getc() for i in range(4)])
        elif next == 'U':
            hexcode = ''.join([reader.getc() for i in range(8)])
        else:
            reader.unread(next)
            return subescapereader(reader, c)
        if len(hexcode) not in (4, 8):
            raise UnicodeDecodeError("end of string in escape sequence")
        return unichr(int(hexcode, 16))
    return unicode_escape_reader

def make_string_ender(quoteletters):
    if len(quoteletters) == 1:
        return thrower(ReaderStopReading)
    def string_ender(reader, c):
        maybe_endquote = [c]
        while len(maybe_endquote) < len(quoteletters):
            next = reader.getc()
            if next != quoteletters[len(maybe_endquote)]:
                reader.unread(next)
                return ''.join(maybe_endquote)
            maybe_endquote.append(next)
        raise ReaderStopReading
    return string_ender

@default_reader_macro('"\'', isterminating=True)
def read_string_constant(reader, c, leaderchars=''):
    quote = [c]
    next = reader.getc()
    if next == c:
        next = reader.getc()
        if next == c:
            quote = [c] * 3
            next = reader.getc()
        else:
            reader.unread(next)
            return ""
    reader.unread(next)
    realreadtable = reader.get_readtable()
    escapereader = ('r' in leaderchars) and raw_escape or string_escape
    if ('u' in leaderchars):
        escapereader = unicode_escape(escapereader)
    try:
        reader.set_readtable(
            ([lambda reader, c: c] * 256, [False] * 256)
        )
        reader.set_macro_character(c, make_string_ender(quote))
        reader.set_macro_character('\\', escapereader)
        if len(quote) == 1:
            reader.set_macro_character('\n', thrower(
                SyntaxError, "End of line while scanning single-quoted string"
            ))
        return ''.join(reader.read_elements(eoferror=True))
    finally:
        reader.set_readtable(realreadtable)

def read_unquote(reader, c):
    if reader.peekc() == '@':
        reader.getc()
        return (Symbol('unquote-splice'), reader.read())
    return (Symbol('unquote'), reader.read())

@default_reader_macro('`')
def read_quasiquote(reader, c):
    oldinfo = reader.set_macro_character(',', read_unquote)
    try:
        return (Symbol('quasiquote'), reader.read())
    finally:
        reader.set_macro_character(',', *oldinfo)

class Reader:
    def __init__(self, instream=None, readtable=None, filename=None):
        if instream is None:
            instream = sys.stdin
        if filename is None:
            filename = getattr(instream, 'name', '?')
        self.filename = filename
        self.instream = instream
        self.readfunc = instream.read
        self.set_readtable(readtable or new_default_readtable())
        self.unreadchars = []

        self.last_item_read = [None]
        self.lineno = 0
        self.column = 0
        self.linemap = {}

    def getc(self):
        """Can return an empty string on EOF."""

        if self.unreadchars:
            return list.pop(self.unreadchars)
        c = self.readfunc(1)
        if c == '\n':
            self.column = 0
            self.lineno += 1
        else:
            self.column += 1
        return c

    def unread(self, c):
        list.append(self.unreadchars, c)

    def peekc(self):
        c = self.getc()
        self.unread(c)
        return c

    def read(self, eoferror=True, eofvalue=None):
        while True:
            gotchar = self.getc()
            try:
                readermacro = self.macrochars[ord(gotchar)]
            except IndexError:
                readermacro = invalidchar
            except TypeError:
                # eof processing
                if eoferror:
                    raise EOFError
                return eofvalue
            startline = self.lineno
            try:
                item = readermacro(self, gotchar)
            except ReaderIgnore:
                pass
            else:
                break
        self.linemap[id(item)] = (startline, self.lineno, self.filename)
        return item

    def set_macro_character(self, c, func, isterminating=False):
        o = ord(c)
        oldf = self.macrochars[o]
        oldt = self.terminating[o]
        self.macrochars[o] = func
        self.terminating[o] = isterminating
        return oldf, oldt

    def get_macro_character(self, c):
        return self.macrochars[ord(c)]

    def read_elements(self, eoferror=False):
        items = []
        try:
            while True:
                items.append(self.read(eoferror=True))
        except ReaderStopReading:
            pass
        except EOFError:
            if eoferror:
                raise
        return tuple(items)

    def get_readtable(self):
        return self.macrochars, self.terminating

    def set_readtable(self, readtable):
        self.macrochars, self.terminating = readtable

import bindconsts
bindconsts.bind_module_funcs()
