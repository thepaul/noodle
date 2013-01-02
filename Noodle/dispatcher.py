# dispatcher
#
# paul cannon <pcannon@novell.com>
# mar 2005

"""A way to make generic functions -- functions with different versions
depending on the types of the incoming arguments. Used with decorators.

The best way to explain is probably by example, so:

    #!/usr/bin/env python2.4

    from dispatcher import *

    # This is made the default.
    @generic
    def foo(*args):
        print "foo%s" % str(args)

    # This is called when foo gets two arguments of type string.
    @foo.with_types(str, str)
    def bar(one, two):
        print "bar(%s, %s)" % (one, two)

    # This is called when foo gets four arguments, and the first, second,
    # and fourth are 29, 13, and 14, respectively. The third can be anything.
    @foo.with_values(29, 13, Any, 14)
    def baz(one, two, three, four):
        print "baz(%s, %s, %s, %s)" % (one, two, three, four)

    # This is called when foo gets 2 or more arguments, and the first and
    # last are of type int. ("Others" means any number of arguments of
    # any type and value).
    @foo.with_types(int, Others, int)
    def bonk(*args):
        print "bonk%s" % str(args)

    # This is called when the arguments to foo match these conditions: the
    # first is of type str, and the second is between 55 and 75.
    @foo.with_conditions(TypeMatch(str), lambda arg: 55 < arg < 75)
    def boo(*args):
        print "boo%s" % str(args)

    print "---------------------"
    print "this should call foo:"
    foo('hello', 12)

    print "---------------------"
    print "this should call bar:"
    foo('hello', 'world')

    print "---------------------"
    print "this should call baz:"
    foo(29, 13, {'big': 'extra', 'arg': 'in here'}, 14)

    print "---------------------"
    print "this should call bonk:"
    foo(29, 13, 14, 'what a world', 12)

    print "---------------------"
    print "this should call bonk:"
    foo(29, 12)

    print "---------------------"
    print "this should call foo:"
    foo('blob', 55)

    print "---------------------"
    print "this should call boo:"
    foo('blob', 56)

So the process is: decorate the default version of the function with
@dispatcher.generic. After that, you can use several attributes of
that function in order to add other possibilities to the generic
function: with_types, with_values, and with_conditions.

Each function can still be called normally after becoming a candidate
for the generic function.

Note that this causes some confusion when used with methods of a class:
when normally bound, the 'self' argument is automatically inserted, so
your with_* decorators need to allow for that argument. If you don't
want to need to deal with that, use the @dispatcher.genericmethod
decorator instead. This will cause the first parameter for each call
to be treated specially- it won't be compared against any of the items
in the specified argument values, types, etc.

"""

class Any:
    """Pass this as an argument to a generic function's with_* decorators
    to indicate that "Any" one argument can match in that position.
    """

class Others:
    """Pass this as an argument to a generic function's with_* decorators
    to indicate that any number of arguments of any sort (or zero arguments)
    can match in that position.
    """

class _Candidate:
    """A candidate for a default generic function."""

    def __call__(self, func):
        """This is called when the candidate is finally applied as a
        decorator; it just stores the function in itself. The master
        generic function already has a reference to this object, so
        this is sufficient.
        """

        self.func = func
        return func

def _get_index_of(seq, item):
    for num, member in enumerate(seq):
        if member == item:
            return num
    return -1

class _ArgumentBasedCandidate(_Candidate):
    def __init__(self, specd_args):
        othersloc = _get_index_of(specd_args, Others)
        if othersloc < 0:
            self.begin_args = specd_args
            self.end_args = []
            self.extra_args_ok = False
        else:
            self.begin_args = specd_args[:othersloc]
            self.end_args = specd_args[othersloc+1:]
            self.extra_args_ok = True

    def lenmatches(self, given_args):
        combined_len = len(self.begin_args) + len(self.end_args)
        return ((len(given_args) == combined_len) or
                (self.extra_args_ok and len(given_args) > combined_len))

    def matches(self, arglist):
        if not self.lenmatches(arglist):
            return False
        for inarg, reqtype in zip(arglist, self.begin_args):
            if not self.arg_ok(inarg, reqtype):
                return False
        for inarg, reqtype in zip(arglist[-len(self.end_args):], self.end_args):
            if not self.arg_ok(inarg, reqtype):
                return False
        return True

class _TypeMatcher(_ArgumentBasedCandidate):
    def __init__(self, argtypes):
        _ArgumentBasedCandidate.__init__(self, argtypes) 

    def arg_ok(self, given, required):
        return (isinstance(given, required) or required == Any)

class _ValueMatcher(_ArgumentBasedCandidate):
    def __init__(self, argvals):
        _ArgumentBasedCandidate.__init__(self, argvals)

    def arg_ok(self, given, required):
        return (given == required or required == Any)

class _FuncMatcher(_ArgumentBasedCandidate):
    def __init__(self, args):
        _ArgumentBasedCandidate.__init__(self, args)

    def arg_ok(self, given, required):
        return required(given)

def ValueMatch(required_val):
    """Call this function within the spec arguments to the
    with_conditions decorator to create a value checker.
    """

    def do_value_match(given):
        return given == required_val
    return do_value_match

def TypeMatch(required_type):
    """Call this function within the spec arguments to the
    with_conditions decorator to create a type checker; it checks
    for any objects of the given type or a subtype.
    """

    def do_type_match(val):
        return isinstance(val, required_type)
    return do_type_match

# Note: this was done with closures instead of a class because, (a), I like
# it that way, and (b), the returned function is actually a function, which
# means it can be normally bound as a method when found in a class. Class
# instances--even callable ones--aren't made bound methods in a class
# definition.

def generic(func, _skip=0):
    candidates = []

    candidatetypes = {
        'with_types': _TypeMatcher,
        'with_values': _ValueMatcher,
        'with_conditions': _FuncMatcher
    }

    def _candidate_creator_factory(candidatetype):
        def _candidate_creator_decorator(*args):
            def _new_candidate(c):
                candidates.append(c)
                return c
            return _new_candidate(candidatetype(args))
        return _candidate_creator_decorator

    def choose(*args):
        for candidate in candidates:
            if candidate.matches(args[_skip:]):
                return candidate.func(*args)
        return func(*args)

    for name, klass in candidatetypes.items():
        setattr(choose, name, _candidate_creator_factory(klass))

    choose.func_name = 'generic_%s' % func.func_name

    return choose

def genericmethod(func):
    """Generic function which is usable as a normally bound method: it skips
    checking of the first argument, since that will be the self argument.
    """

    return generic(func, _skip=1)

# vim: set et sw=4 ts=4 :
