from inspect import isfunction
from graphlib import TopologicalSorter


def _f(): pass
function = type(_f)
del _f


from selftest import get_tester
test = get_tester(__name__)


""" This module implements a Self-like delegation, mostly compatible with Python.
    It introduces 'self' and 'this' for user code, and uses 'me' for its own
    internal code.
"""


class meta(type):
    """ This type turns inheritance into delegation for "class name(prototype):" """

    def __new__(self, name, bases, attributes):
        if name == 'prototype': #bootstrap
            return type.__new__(self, name, bases, attributes)
        return prototype(**attributes)



class method:
    """ A function bound to a 'self' and a 'this'. Doubles as 'super'"""

    def __init__(me, function, self, this):
        me._func = function 
        me._self = self
        me._this = this
        me._arg_names = function.__code__.co_varnames


    def __call__(me, *args, **kwargs):
        """ call function(self, this, super, *args, **kwargs) """
        arg_names = me._arg_names
        if 'super' in arg_names:   # if present, must be last
            args = me, *args
        if 'this' in arg_names:    # if present, must be in the middle
            args = me._this, *args
        if 'self' in arg_names:    # if present, must be first
            args = me._self, *args
        elif 'cls' in arg_names:   # if present, must be first
            args = me._this, *args
        return me._func(*args, **kwargs)


    def __getattribute__(me, name):
        """ support for 'super' """
        if name in {'_func', '_self', '_this', '_arg_names'}:
            return object.__getattribute__(me, name)
        attr, this = me._this.lookup(name, skip=me._this)
        return method(attr, me._self, this)



class prototype(metaclass=meta):
    """ The type of all objects """

    def __new__(cls, *type_initializers, **__):
        """ This method turns inheritance into delegation for "class name(prototype()):" """
        if tuple(map(type, type_initializers)) == (str, tuple, dict): # prototype used as type
            name, bases, attributes = type_initializers
            return prototype(*bases, __name__=name, **attributes)
        return object.__new__(cls)


    def __init__(me, *parents, **attributes):
        if not hasattr(me, '__bases__'):
            me.__bases__ = tuple(p for p in parents if not isfunction(p))
            me.__dict__.update(attributes)
            me.__dict__.update((f.__name__, f) for f in parents if isfunction(f))


    def __getattribute__(me, name):
        if name in {'__dict__', '__bases__', 'lookup', '_call_dunder', 'get'}:
            return object.__getattribute__(me, name)

        attr, this = me.lookup(name)
        if isfunction(attr):
            return method(attr, me, this)
        return attr


    def __call__(me, *args, **kwargs):
        try:
            f, this = me.lookup('__call__')
        except AttributeError:
            return prototype(me, *args, **kwargs)
        else:
            return method(f, me, this)(*args, **kwargs)


    def _call_dunder(me, name, *args, **kwargs):
        """ Looks up __dunder__ method in the instance (prototype)
            before falling back to the class (as Python does by default)
        """
        try:
            f, this = me.lookup(name)
        except AttributeError:
            return getattr(object, name)(me, *args, **kwargs)
        return method(f, me, this)(*args, **kwargs)


    def __eq__(me, rhs):
        return me._call_dunder('__eq__', rhs)


    def __hash__(me):
        return me._call_dunder('__hash__')


    def lookup(me, name, skip=None):
        """ Depth (height) first lookup of attribute in the parents. """
        for this in linearize(me):
            if id(this) == id(skip):
                continue
            if isinstance(this, prototype):
                try:
                    #return this.lookup(name)
                    return this.__dict__[name], this
                except KeyError:
                    continue
            else: # support Python classes and objects
                try:
                    attr = getattr(this, name)
                except AttributeError:
                    continue
                if hasattr(attr, '__func__'): # undo descriptors
                    this = attr.__self__
                    attr = attr.__func__
            return attr, this
        else:
            raise AttributeError(name)


    def get(me, name, default=None):
        return me.__dict__.get(name, default)

    def __getitem__(me, name):
        return me.__dict__[name]


    def __iter__(me):
        return (k for k in me.__dict__ if k[0] != '_')


    def __repr__(me):
        return f"{me.get('__name__','')}[" + ', '.join(f"{k} = {me[k]}" for k in me) + ']'


def linearize(obj):
    """ C3 compatible linearization (which is a topological sort) """
    idmap = {id(obj): obj}
    graph = TopologicalSorter({id(obj): ()})

    def add_bases(obj):
        prev = None
        for base in getattr(obj, '__bases__', ()):
            idmap[id(base)] = base
            graph.add(id(base), id(obj))
            if prev:
                graph.add(id(base), id(prev))
            prev = base
            add_bases(base)

    add_bases(obj)
    return [idmap[id] for id in graph.static_order()]


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
def super_to_prototype():
    # Self-like resend
    a = prototype(f=lambda n: n * 3)
    b = prototype(a, f=lambda self, super, n: 2 * super.f(n))
    test.eq(30, b.f(5))


@test
def super_to_class():
    class F:
        def f(self, n):
            return n * 3
    b = prototype(F, f=lambda self, super, n: 2 * super.f(n))
    test.eq(30, b.f(5))


@test
def super_to_object():
    class F:
        def f(self, n):
            return n * 3
    f = F()
    b = prototype(f, f=lambda self, super, n: 2 * super.f(n))
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
        def f(super):
            return 2 * super.f()
    test.isinstance(b, prototype)
    test.eq((a,), b.__bases__)
    test.eq(3, b.a)
    test.eq(2, b.b)
    test.eq(32, b.f())
    test.eq('b', b.__name__)

   
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
        def f(super):
            return 2 * super.f()

    class bottom(middle):
        a = 42

    test.eq(42, bottom.a)

    f = bottom.f
    test.eq(middle.f._func, f._func)
    test.eq(bottom, f._self)
    test.eq(middle, f._this)


    test.eq(84, bottom.f())                          # will return 84
    test.eq(16, bottom.g())                          # will return 16


@test
def sensible_iter():
    p = prototype()
    test.eq([], list(iter(p)))
    p = prototype(a=1, f=lambda: None)
    test.eq(['a', 'f'], list(iter(p)))



@test
def sensible_repr():
    p = prototype()
    test.eq('[]', repr(p))
    test.eq('[]', str(p))
    p = prototype(a=1)
    test.eq('[a = 1]', repr(p))
    p = prototype(a=1, f=lambda: None)
    test.eq(f'[a = 1, f = <function sensible_repr.<locals>.<lambda> at 0x{id(p.f._func):x}>]', repr(p))
    def f(): pass
    p = prototype(f, a=1)
    test.eq(f'[a = 1, f = <function sensible_repr.<locals>.f at 0x{id(p.f._func):x}>]', repr(p))
    p = prototype(__name__='yes', a=2)
    test.eq('yes[a = 2]', str(p))


@test
def lookup_dunder():
    class A:
        def __call__(self):
            return 27
        def __getattribute__(self, name):
            return 42
    a = A()
    # Python looks up __ methods on the class, skipping the objects __getattribute__
    test.eq(27, a())
    # Explicit dereferencing does invoke __getattribute__; useful for super/resend
    test.eq(42, a.__call__)
    # (__getattr__ works as expected)


@test
def dunder_method__call__():
    def a_call(n):
        return 2 * n

    a = prototype(__call__=a_call)

    test.isinstance(a.__call__, method)
    test.eq(a_call, a.__call__._func)
    test.eq((a_call, a), a.lookup('__call__'))
    test.eq(42, a(21))

    def b_call(self, this, super, n):
        return self, this, super, super.__call__(n)

    b = prototype(a, __call__=b_call)

    test.isinstance(b.__call__, method)
    test.eq(b_call, b.__call__._func)
    test.eq((b_call, b), b.lookup('__call__'))
    self, this, super, n = b(21)
    test.eq(42, n)


@test
def dunder_method__eq__():
    def a_eq(self, rhs):
        return self.x == rhs.x
    def a_hash(self):
        return hash(self.x)
    a = prototype(__eq__=a_eq, __hash__=a_hash, x=None)
    test.eq(a_eq, a.__eq__._func)
    test.eq(a_hash, a.__hash__._func)
    b = prototype(a, x=3)
    c = prototype(a, x=4)
    d = prototype(a, x=3)
    test.eq(a, a)
    test.ne(a, b)
    test.ne(hash(a), hash(b))
    test.ne(b, a)
    test.ne(a, c)
    test.ne(hash(a), hash(c))
    test.ne(c, a)
    test.eq(b, d)
    test.eq(d, b)
    test.eq(hash(b), hash(d))


@test
def dunder_method__eq__via_class():
    class a(prototype):
        x = None
        def __eq__(self, rhs):
            return self.x == rhs.x
        def __hash__(self):
            return hash(self.x)
    b = prototype(a, x=3)
    c = prototype(a, x=4)
    d = prototype(a, x=3)
    test.eq(a, a)
    test.ne(a, b)
    test.ne(hash(a), hash(b))
    test.ne(b, a)
    test.ne(a, c)
    test.ne(hash(a), hash(c))
    test.ne(c, a)
    test.eq(b, d)
    test.eq(d, b)
    test.eq(hash(b), hash(d))


@test
def assignments():
    a = prototype(x = 1, y = 3)
    b = prototype(a, x = 2)
    test.eq(1, a.x)
    test.eq(2, b.x)
    test.eq(3, a.y)
    test.eq(3, b.y)
    b.y = 6
    test.eq(3, a.y)
    test.eq(6, b.y)
    #b['y'] = 9
    #test.eq(9, a.y)
    #test.eq(9, b.y)


# TODO directed resend: this[<parent>].<method>(...)
#      how to refer to parent? Index, name, ...?

@test
def C3_liniarization():
    O = object
    test.eq([O], linearize(O))
    class A(O): pass
    test.eq([A, O], linearize(A))
    class B(O): pass
    class C(O): pass
    class D(O): pass
    class E(O): pass
    class K1(C, A, B): pass
    test.eq([K1, C, A, B, O], linearize(K1), diff=test.diff)
    test.eq(K1.mro(), linearize(K1), diff=test.diff)
    class K2(B, D, E): pass
    test.eq([K2, B, D, E, O], linearize(K2))
    test.eq(K2.mro(), linearize(K2), diff=test.diff)
    class K3(A, D): pass
    test.eq([K3, A, D, O], linearize(K3))
    test.eq(K3.mro(), linearize(K3), diff=test.diff)
    class Z(K1, K3, K2): pass
    test.eq(Z.mro(), linearize(Z), diff=test.diff)
    test.eq([Z, K1, C, K3, A, K2, B, D, E, O], linearize(Z), diff=test.diff)


@test
def C3_liniarization_with_prototypes():
    O = prototype()
    test.eq([O], linearize(O))
    class A(O): pass
    test.eq([A, O], linearize(A))
    class B(O): pass
    class C(O): pass
    class D(O): pass
    class E(O): pass
    class K1(C, A, B): pass
    test.eq([K1, C, A, B, O], linearize(K1), diff=test.diff)
    class K2(B, D, E): pass
    test.eq([K2, B, D, E, O], linearize(K2))
    class K3(A, D): pass
    test.eq([K3, A, D, O], linearize(K3))
    class Z(K1, K3, K2): pass
    test.eq([Z, K1, C, K3, A, K2, B, D, E, O], linearize(Z), diff=test.diff)


@test
def diamond():
    class A:
        x = 0
        y = 0
        def product(self):
            return self.x * self.y

    class B(A):
        x = 5

    class C(A):
        y = 3

    class D(B, C):
        pass

    class E(C, B):
        pass

    test.eq(15, D().product())
    test.eq(15, E().product())

    class a(prototype):
        x = 0
        y = 0
        def product(self):
            return self.x * self.y

    class b(a):
        x = 5

    class c(a):
        y = 3

    class d(b, c):
        pass

    class e(c, b):
        pass

    test.eq(15, d.product())
    test.eq(15, e.product())


