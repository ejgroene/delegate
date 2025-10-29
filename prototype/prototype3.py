from inspect import signature, isfunction

def _f(): pass
function = type(_f)
del _f


from selftest import get_tester
test = get_tester(__name__)


""" This module implements a Self-like delegation, mostly compatible with Python.
    It introduces 'self' and 'this' for user code, and uses 'me' for its own
    internal code.
"""


class method:
    # A function bound to a 'self' and a 'this'.

    def __init__(me, function, self, this):
        me.__func__ = function   # Horribly ugly: it follows Pythons descriptor model, which is
        me.__self__ = self       #   undone in lookup.
        me._this = this
        me._signature = signature(function)

    def __call__(me, *args, **kwargs):
        if isinstance(me._this, prototype):
            me._this.resend = lookup(me.__self__, me._this._parents)
        signature = me._signature
        parameters = signature.parameters
        if 'this' in parameters:
            args = me._this, *args
        if 'self' in parameters:
            args = me.__self__, *args
        elif 'cls' in parameters:  # for delegation to classmethods
            args = me._this, *args
        binding = signature.bind(*args, **kwargs)
        binding.apply_defaults()
        return me.__func__(*binding.args, **binding.kwargs)


class meta(type):
    """ This type turns inheritance into delegation for
          class name(prototype):
    """
    def __new__(self, name, bases, attributes):
        if name == 'prototype': #bootstrap
            return type.__new__(self, name, bases, attributes)
        return prototype(**attributes)


class prototype(metaclass=meta):
    # The type of all objects

    def __new__(cls, *initializers, **__):
        """ This method turns inheritance into delegation for
              class name(prototype()):
        """
        if tuple(type(i) for i in initializers) == (str, tuple, dict): # prototype used as type
            name, bases, attributes = initializers
            if all(isinstance(b, prototype) for b in bases):
                return prototype(*bases, **attributes)
            raise TypeError(f"Cannot mix prototypes with classes.")
        return object.__new__(cls)

    def __init__(me, *parents, **attributes):
        if hasattr(me, '_parents'):
            return # already initialized in __new__
        me._parents = tuple(p for p in parents if not isfunction(p))
        me.__dict__.update(attributes)
        for f in parents:
            if isfunction(f):
                me.__dict__[f.__name__] = f

    def __getattribute__(me, name):
        if name in {'__dict__', '_parents', 'resend'}:
            return object.__getattribute__(me, name)

        try:
            attr = me.__dict__[name]
        except KeyError:
            return getattr(lookup(me, me._parents), name) # me as self is not always correct
        else:
            if isfunction(attr):
                return method(attr, me, me)
            return attr

    def __call__(me, *parents, **attributes):
        return prototype(me, *parents, **attributes)


class lookup:
    # Attribute lookup on parents

    def __init__(me, self, parents):
        me._self = self
        me._parents = parents

    def __getattr__(me, name):
        for this in me._parents:
            try:
                attr = getattr(this, name)  # we need this to lookup attributes in classes
            except AttributeError:
                continue
            if hasattr(attr, '__func__'):
                # remove descriptors such as staticmethod and classmethod
                # and (o horror!) also our own method object
                this = attr.__self__
                attr = attr.__func__
            if isfunction(attr):
                # we must supply the right self here, that is why we cannot
                # use the method object created by our own __getattribute__.
                return method(attr, me._self, this)
            return attr
        else:
            raise AttributeError(name)


@test
def create_prototype():
    p0 = prototype()
    p1 = prototype()
    test.ne(p0, p1)


@test
def init_attributes():
    p0 = prototype(a=1, b=2)
    test.eq(1, p0.a)
    test.eq(2, p0.b)


@test
def add_attributes():
    p0 = prototype()
    p0.a = 1
    test.eq(1, p0.a)

@test
def lookup_values():
    p0 = prototype(a=0)
    p1 = prototype(p0, b=1)
    p2 = prototype(p1, c=2)
    test.eq(0, p0.a)
    test.eq(1, p1.b)
    test.eq(0, p1.a)
    test.eq(2, p2.c)
    test.eq(1, p2.b)
    test.eq(0, p2.a)

@test
def init_functions():
    p = prototype(f=lambda: 4)
    test.hasattr(p, 'f')
    test.isinstance(p.f, method)
    test.eq(4, p.f())


@test
def add_functions():
    p = prototype()
    p.f = lambda: 3
    test.isinstance(p.f, method)
    test.eq(3, p.f())


@test
def method_lookup():
    p = prototype(f=lambda self, this: (self, this))
    test.callable(p.f)
    test.eq((p, p), p.f())


class A:
    # a 'normal' method receives self only when called on an object, not when called on a class
    def normal(self=None, *args):
        return self, *args

    @classmethod
    def classs(cls, *args):
        return cls, *args

    @staticmethod
    def static(*args):
        return args


@test
def different_member_functions():
    # just to get Python's mess
    a = A()
    test.eq({}, a.__dict__)

    # normal method varies
    test.eq(function, type(A.__dict__['normal']))
    test.isfunction(A.__dict__['normal'])
    test.isfunction( A.normal)
    test.ismethod(   a.normal)
    test.eq((None,), A.normal())
    test.eq(   (a,), a.normal())

    # classmethod is always the same
    descriptor = A.__dict__['classs']
    test.eq(classmethod, type(descriptor))
    test.ismethoddescriptor(descriptor)
    test.ismethod(A.classs)
    test.ismethod(a.classs)
    test.eq((A,), A.classs())
    test.eq((A,), a.classs())
    f = descriptor.__get__(42, None)  # instance (object), owner (class)
    test.eq((int,), f())
    f = descriptor.__get__(None, 42)
    test.eq((42,), f())

    # staticmethod is always the same
    descriptor = A.__dict__['static']
    test.eq(staticmethod, type(descriptor))
    test.ismethoddescriptor(descriptor)
    test.isfunction(A.static)
    test.isfunction(a.static)
    test.eq(    (), A.static())
    test.eq(    (), a.static())
    f = descriptor.__get__(42, None)
    test.eq((), f())
    f = descriptor.__get__(None, 42)
    test.eq((), f())


@test
def delegate_to_prototype_class():
    # sensible compatibility with Python
    p = prototype(A)
    test.callable(p.normal)
    test.callable(p.classs)
    test.callable(p.static)
    test.eq((p, 42), p.normal(42))
    test.eq((A, 42), p.classs(42))
    test.eq(  (42,), p.static(42))


@test
def classmethod_on_subclass():
    class B(A):
        @classmethod
        def classs_b(cls, *args):
            return cls, *args
    b = B()
    test.eq((B,), b.classs())
    test.eq((B,), b.classs_b())


@test
def delegate_to_python_object():
    a = A()
    p = prototype(a)
    test.callable(p.normal)
    test.callable(p.classs)
    test.callable(p.static)
    test.eq((p, 42), p.normal(42))
    test.eq((A, 42), p.classs(42))
    test.eq(  (42,), p.static(42))


@test
def delegate_to_python_subclass():
    class B(A):
        @classmethod
        def classs_b(cls, *args):
            return cls, *args
    p = prototype(B)
    test.callable(p.normal)
    test.callable(p.classs)
    test.callable(p.static)
    test.eq((p, 42), p.normal(42))
    test.eq((B, 42), p.classs(42))
    test.eq(  (42,), p.static(42))
    test.eq((B,   ), p.classs_b())


@test
def delegate_to_python_subclass_object():
    class B(A):
        @classmethod
        def classs_b(cls, *args):
            return cls, *args
    b = B()
    p = prototype(B)
    test.callable(p.normal)
    test.callable(p.classs)
    test.callable(p.static)
    test.eq((p, 42), p.normal(42))
    test.eq((B, 42), p.classs(42))
    test.eq(  (42,), p.static(42))
    test.eq((B,   ), p.classs_b())


@test
def resend_to_prototype():
    # Self-like resend
    a = prototype(f=lambda n: n * 3)
    b = prototype(a, f=lambda self, this, n: 2 * this.resend.f(n))
    test.eq(30, b.f(5))


@test
def resend_to_class():
    class F:
        def f(self, n):
            return n * 3
    b = prototype(F, f=lambda self, this, n: 2 * this.resend.f(n))
    test.eq(30, b.f(5))


@test
def resend_to_object():
    class F:
        def f(self, n):
            return n * 3
    f = F()
    b = prototype(f, f=lambda self, this, n: 2 * this.resend.f(n))
    test.eq(30, b.f(5))


@test
def raise_attribute_error():
    p = prototype()
    with test.raises(AttributeError, 'a'):
        p.a


@test
def add_predefined_function():
    def f(self, this, n):
        return self, this, n
    p = prototype(f)
    test.isinstance(p.f, method)
    test.eq((p, p, 3), p.f(3))


@test
def call_prototype():
    p = prototype(a=3)
    q = prototype(b=4)
    r = p(q, c=5)
    test.eq(3, r.a)
    test.eq(4, r.b)
    test.eq(5, r.c)


@test
def initialize_from_class():
    # because I can ¯_(ツ)_/¯
    class a(prototype):
        b = 2
        def f(self):
            return 42
    test.isinstance(a, prototype)
    test.eq(42, a.f())
    test.eq(2, a.b)


@test
def you_could_even_inherit_from_eh_delegate_to_an_object():
    # because I can ¯_(ツ)_/¯
    a = prototype(a=3, f=lambda: 16)
    class b(a):
        b = 2
        def f(this):
            return 2 * this.resend.f()
    test.isinstance(b, prototype)
    test.eq((a,), b._parents)
    test.eq(3, b.a)
    test.eq(2, b.b)
    test.eq(32, b.f())

   
@test
def explicit_function_name():
    def f():
        return 42
    a = prototype(f=f)
    test.eq(42, a.f())


@test
def doc_example():

    class top(prototype):
        a = 16
        def f(self):
            return self.a
        def g(this):
            return this.a

    class middle(top):
        def f(this):
            return 2 * this.resend.f()

    class bottom(middle):
        a = 42

    test.eq(42, bottom.a)
    test.eq(84, bottom.f())                          # will return 84
    test.eq(16, bottom.g())                          # will return 16
