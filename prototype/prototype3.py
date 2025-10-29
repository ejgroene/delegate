from inspect import getfullargspec, isfunction

def _f(): pass
function = type(_f)
del _f


from selftest import get_tester
test = get_tester(__name__)


class method:
    # A function bound to a self and a this

    def __init__(me, function, self, this):
        me._function = function
        me._self = self
        me._this = this
        me._argsspec = getfullargspec(function).args[:2]

    def __call__(me, *args, **kwargs):
        argspec = me._argsspec
        if argspec == ['self']:
            return me._function(me._self, *args, **kwargs)
        if argspec == ['self', 'this']:
            return me._function(me._self, me._this, *args, **kwargs)
        if argspec == ['cls']:
            return me._function(me._this, *args, **kwargs)
        return me._function(*args, **kwargs)


class prototype:

    def __init__(self, *parents, **attributes):
        self._parents = parents
        self.__dict__.update(attributes)

    def __getattribute__(self, name):
        if name in {'__dict__', '_parents', 'resend'}:
            return object.__getattribute__(self, name)

        this = self
        try:
            attr = self.__dict__[name]
        except KeyError:
            for this in self._parents:
                if attr := getattr(this, name):  # use Python's lookup for compatibility
                    break

        if hasattr(attr, '__func__'):
            # remove descriptors such as staticmethod and classmethod
            this = attr.__self__
            attr = attr.__func__

        if isfunction(attr):
            return method(attr, self, this)

        return attr

    @property
    def resend(self):
        class x:
            def __getattr__(_, name):
                for this in self._parents:
                    if attr := getattr(this, name):
                        return attr
        return x()


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
def resend():
    # Self-like resend
    a = prototype(f=lambda n: n * 3)
    b = prototype(a, f=lambda self, this, n: 2 * this.resend.f(n))
    test.eq(30, b.f(5))
    test.isinstance(b.resend.f, method)
