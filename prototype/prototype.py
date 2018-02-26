from types import FunctionType, MethodType, ClassType
from inspect import getargspec, isfunction, isclass

class Self(object):
    """ Instances of this class represent self during method calls in order
        to distinquis between self and this."""

    def __init__(me, self, this, prox=None):
        object.__setattr__(me, '_self', self)
        object.__setattr__(me, '_this', this)
        object.__setattr__(me, '_prox', prox if prox else this)

    @property
    def this(me):
        return Self(me._self, me._this)

    @property
    def next(me):
        return Self(me._self, me._this._prototypes[1])

    def __getattr__(me, name):
        return me._self.__getattribute__(name, me._prox._prototypes)

    def __setattr__(me, name, val): return setattr(me._prox, name, value)
    def __cmp__(me, rhs):           return cmp(me._prox, rhs)
    def __call__(me, *arg, **kws):  return me._prox(*arg, **kws)
    def __contains__(me, name):     return name in me._prox
    def __getitem__(me, name):      return me._prox[name]
    def __repr__(me):               return repr(me._prox)

class meta(type):
    """ This type turns inheritance into delegation for
          class name(prototype): """

    def __new__(self, name, bases, dct):
        if name == 'prototype': #bootstrap
            return type.__new__(self, name, bases, dct)
        return prototype(**dct)

class prototype(object):
    """ This is the class for all objects. """

    __metaclass__ = meta

    def __new__(*_, **__):
        """ This method turns inheritance into delegation for
              class name(prototype()): """
        return object.__new__(prototype)

    def __init__(self, *initializers, **attributes):
        if tuple(type(i) for i in initializers) == (str, tuple, dict):
            attributes = initializers[2]
            initializers = initializers[1]
        self._prototypes = (self,)
        for arg in initializers:
            if isfunction(arg) and 'self' in getargspec(arg).args:  # f(self): method
                attributes[arg.__name__] = arg
            elif isfunction(arg) and not getargspec(arg).args:      # f(): ctor
                attributes.update(arg())
            elif isinstance(arg, ClassType):            # old style class: ctor
                attributes.update(arg.__dict__)
            elif hasattr(arg, '_prototypes'):           # other object: prototype
                self._prototypes += arg._prototypes
            elif isclass(arg):                          # new style class: prototype
                self._prototypes += (arg,)
            elif isinstance(arg, object) and type(arg).__module__ != '__builtin__': 
                self._prototypes += (arg,)              # new style object: prototype
            else:
                raise Exception("not a valid argument: %s,  %s" % (initializers, attributes))
        self.__dict__.update(attributes)
           
    def __getattribute__(self, name, prototypes=None):
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        for this in prototypes or self._prototypes:
            try:
                attribute = object.__getattribute__(this, name)
            except AttributeError:
                continue
            if isfunction(attribute):
                return MethodType(attribute, Self(self, this, self))
            if isinstance(attribute, dict):
                return prototype(self, **dict((str(k),v) for k,v in attribute.iteritems()))
            return attribute

    def __call__(self, *prototypes_or_functions, **attributes):
        return prototype(self, *prototypes_or_functions, **attributes)

    #behave a bit dict'isch
    def __getitem__(self, name):  return getattr(self, str(name)) 
    def __contains__(self, name): return name in self.__dict__
    def __repr__(self):           return "prototype"+repr(dict(self.__iter__()))
    def __iter__(self):           return ((k,v) for k,v in \
                                    self.__dict__.iteritems() if not k.startswith('_'))

from autotest import autotest

@autotest
def simple_object_assembled_manually():
    a = prototype()
    a.x = 1
    assert a.x == 1
    def f(self):
        assert self.x == 1
        assert self == a
        return self
    assert type(f) == FunctionType
    a.f = f
    assert type(a.f) == MethodType
    assert a.f() == a
    b = prototype()
    assert a != b

@autotest
def simple_object_with_old_style_class_syntax():
    @prototype
    class a:
        x = 1
        def f(self):
            return self
    assert type(a.f) == MethodType
    assert a.f() == a
    @prototype
    class b:
        pass
    assert a != b

@autotest
def create_your_first_prototype():

    @prototype
    class creature:
        legs = 4
        def age(self):
            return 2016 - self.birth_date

    assert creature.legs == 4

    @creature
    class person:
        legs = 2

    assert person.legs == 2

    @person
    class pete:
        birth_date = 1990

    assert pete.legs == 2
    assert pete.age() == 26

@autotest
def alternative_syntax_1():

    creature = prototype(legs=4, age=lambda self: 2016 - self.birth_date)
    assert creature.legs == 4

    person = creature(legs=2)
    assert person.legs == 2

    pete = prototype(person, birth_date=1990)
    assert pete.legs == 2
    assert pete.age() == 26

@autotest
def alternative_syntax_2():

    @prototype
    def creature():
        legs = 4
        def age(self):
            return 2016 - self.birth_date
        def person(self):
            def bear(self, year):
                return self(birth_date=year)
            return self(bear, legs=2)
        return locals()

    assert creature.legs == 4
    
    person = creature.person()
    assert person.legs == 2

    pete = person.bear(1990)
    assert pete.age() == 26

@autotest
def anonymous_prototype_because_we_can():

    @prototype(age=lambda self: 2016 - self.birth_date)
    class person:
        legs = 2
    
    pete = person(birth_date=1990)
    
    assert pete.legs == 2
    assert pete.age() == 26

@autotest
def accept_noarg_ctor_function_creating_attributes():
    def f(not_self, a, b=10):
        pass
    try:
        prototype(f)
        assert False
    except Exception as e:
        assert "not a valid argument:" in str(e), str(e)
    def g(a, b):
        pass
    try:
        prototype(g)
        assert False
    except Exception as e:
        assert "not a valid argument:" in str(e)
    try:
        prototype('10')
        assert False
    except Exception as e:
        assert "not a valid argument:" in str(e), e

@autotest
def simply_pass_functions_as_attributes():
    o = prototype()
    def f(self):
        return "Hello!"
    o2 = o(f=f)
    assert o2.f() == "Hello!"
    def g(self):
        return "Goodbye!"
    o3 = o(f, g)
    assert o3.f() == "Hello!"
    assert o3.g() == "Goodbye!"

@autotest
def create_simple_prototype():
    o = prototype()
    assert o
    o = prototype(a=1)
    assert o.a == 1
    o1 = prototype(o)
    assert o1.a == 1
    o1 = prototype(o, a=2)
    assert o1.a == 2
    o2 = prototype(o1, f=lambda self: 42)
    assert o2.f() == 42
    def f(self): return 84
    o2 = prototype(o1, f=f)
    assert o2.f() == 84
    def g(self, x): return 2 * x
    o2 = prototype(o1, f, g)
    assert o2.f() == 84
    assert o2.g(9) == 18
    def ctor():
        return {"a": 23}
    o3 = prototype(o2, ctor)
    assert o3.a == 23, o3.a
    o3 = prototype(o2, lambda self: 23, lambda self: 56, lambda: {"x": 89})
    assert o3["<lambda>"]() == 56  #yuk
    assert o3.x == 89

@autotest
def create_using_old_style_python_class():
    @prototype
    class obj:
        a = 42
        def f(self):
            return 54
    assert obj.a == 42
    assert obj.f() == 54

@autotest
def calling_object_create_new_object():
    p = prototype()
    o = p(a=42)
    assert o
    assert o != p
    assert o._prototypes == (o, p)
    assert o.a == 42

@autotest
def self_is_callable_and_creates_new_object():
    def f(self):
        return "f"
    def g(self):
        o1 = self()
        o2 = prototype(self)
        return o1, o2
    o = prototype(f, g)
    x, y = o.g()
    assert x.f() == "f", x.f()
    assert y.f() == "f", y.f()

@autotest
def embedded_object_creation_with_self_as_decorator():
    def f(self):
        @self
        def f():
            return {"a": 42}
        return f
    o = prototype(f, a=24)
    assert o.f().a == 42

@autotest
def create_small_hierarchy_of_object():
    creature = prototype(alive=True)
    @creature
    class person:
        def age(self): return 2015 - self.birth
    me = prototype(person, birth=1990)
    assert me.age() == 25, me
    assert me.alive == True
    me.alive = False
    assert me.alive == False
    assert creature.alive == True
    her = person(birth=1994) # nicer syntax
    assert her.age() == 21
    assert her.alive == True

@autotest
def create_object_with_multiple_prototypes():
    def f1(self):
        return "f1"
    o1 = prototype(f1)
    def f2(self):
        return "f2"
    o2 = prototype(f2)
    o3 = prototype(o1, o2)
    assert o3.f1() == "f1"
    assert o3.f2() == "f2"
    def f2(self):
        return "new f2"
    o4 = prototype(f2)
    o5 = prototype(o3, o4)
    assert o5.f2() == "f2"
    o5 = prototype(o4, o3)
    assert o5.f2() == "new f2"
    def f2(self):
        return "own f2"
    o6 = prototype(o5, o4, o3, o2, o1, f2)
    assert o6.f2() == "own f2"
    assert o6.f1() == "f1"
    
@autotest
def create_single_method_object_aka_functor():
    @prototype
    def f(self):
        return "hello"
    assert f.f() == "hello"

@autotest
def lookup_globals():
    @prototype
    def one():
        def f(self):
            return autotest
        return locals()
    assert one.f() == autotest

@autotest
def lookup_attributes():
    o = prototype(a=1, b=2)
    assert "a" in o
    assert "b" in o
    assert "c" not in o
    assert str(o) == "prototype{'a': 1, 'b': 2}", str(o)

@autotest
def lookup_function():
    @prototype
    class A:
        def f(self):
            return self.g()
        def g(self):
            return "a"
    @A
    class B:
        pass

    assert B.f() == 'a'

@autotest
def This_is_Considered_not_Part_of():

    import this

    @prototype
    class A:
        a = 42
        def f(self): return self.a
        def g(self): return self.this.a
    @A
    class B:
        a = 17
        def h(self): return self.a
        def i(self): return self.this.a
    assert A.a == 42
    assert B.a == 17
    assert A.f() == 42
    assert B.f() == 17, B.f()
    assert A.g() == 42
    assert B.g() == 42, B.g()
    assert B.h() == 17
    assert B.i() == 17

@autotest
def next_gives_access_to_objects_higher_up_in_the_chain():
    @prototype
    class A:
        def f(self): return "A"
    @A
    class B:
        def f(self): return 'B' + self.next.f()
    @B
    class C:
        def f(self): return 'C' + self.next.f()
    assert A.f() == "A"
    assert B.f() == "BA"
    assert C.f() == "CBA"

@autotest
def this_preserves_self_when_binding_and_calling_methods():
    @prototype
    class A:
        x = 'a'
        def f(self):
            return "A + " + self.x
    @A
    class B:
        x = 'b'
        def f(self): return 'B' + self.next.f()
    @B
    class C:
        x = 'c'
        def f(self): return 'C' + self.next.f()
    assert A.f() == "A + a"
    assert B.f() == "BA + b"
    assert C.f() == "CBA + c"

def more_elaborate_example_of_using_this_and_next():
    @prototype
    def Obj():
        a = 42
        def f(self):
            return self, self.this.g()
        def g(self):
            return self.a
        return locals()

    assert Obj.f() == (Obj, 42)
    assert Obj.g() == 42

    @Obj
    def Obj1():
        def g(self):
            return 2 * self.next.g()
        return locals()

    assert Obj1.f() == (Obj1, 42)
    assert Obj1.g() == 84

    @Obj1
    def Obj2():
        a = 12
        def f(self):
            return self.next.f()
        def g(self):
            return self.next.g() * 2
        return locals()
    result = Obj2.f()
    assert result == (Obj2, 12), result
    assert Obj2.g() == 48, Obj2.g()

@autotest
def create_object_with_this():
    @prototype
    class a:
        def f(self):
            return self(b=43), self.this(b=42)
        def g(self):
            return "a.g"
    @a
    class b:
        b = 11
        c = 14
        def g(self):
            return "b.g"
    x, y = b.f()
    assert x.g() == "b.g"
    assert y.g() == "a.g"
    assert x.b == 43
    assert y.b == 42
    assert x.c == 14
    assert y.c == None

#@autotest
def private_functions(): # naah
    @prototype
    class a:
        def f(self):
            try:
                return self._g()
            except AttributeError:
                return self.this._g()
        def _g(self):
            return "g"

    assert a._g() == "?"

    @a
    class b:
        pass

    assert b.f() == "g"
    assert b._g() == "?"

@autotest
def normal_python_classes_can_be_delegated_to():
    class a(object):
        c = 10
        def f(self):
            return 42
        def g(self):
            return self.b # Oh yeah!
    assert isinstance(a, type)
    o = prototype(a, b=67)
    assert o.f() == 42
    assert o.b == 67
    assert o.g() == 67
    assert o.c == 10

@autotest
def normal_python_object_can_be_delegated_to():
    class A(object):
        c = 16
        def f(self):
            return 23
        def g(self):
            return self.d
    a = A()
    a.d = 8
    assert isinstance(a, object)
    o = prototype(a)
    assert o.f() == 23
    assert o.c == 16
    assert o.d == 8
    assert o.g() == 8

@autotest
def prototypes_mixed_with_other_args():
    o1 = prototype(a=1, b=4)
    assert o1._prototypes == (o1,)
    o2 = prototype(o1, a=2)
    assert o2._prototypes == (o2, o1), o2._prototypes
    o3 = prototype(o2, a=3)
    assert o3._prototypes == (o3, o2, o1)
    assert o1.a == 1
    assert o2.a == 2
    assert o3.a == 3
    assert o1.b == 4
    assert o2.b == 4
    assert o2.b == 4
    assert o1.x == None
    assert o2.x == None
    assert o3.x == None
    
@autotest
def compare_this_to_object():
    @prototype
    def p1():
        prop = 1 + 2
        prak = "aa"
        def f(self): return self.this
        return locals()
    assert p1
    assert p1.f()
    assert p1 == p1.f() # <= this versus object itself
    assert p1.prop == 3, p1.prop
    assert p1.prak == "aa"
    @p1
    def p2():
        def g(self): return self
        return locals()
    assert p2
    assert p2._prototypes == (p2, p1), p2._prototypes
    assert p2.prop == 3
    assert p2.f() == p1
    assert p2.g() == p2

@autotest
def dispatch_calls_to_next_prototype_in_chain():
    @prototype
    def o0():
        return locals()
    @o0
    def o1():
        def f(self, s):
            return  "|%s|" % s
        return locals()
    @o1
    def o2():
        def f(self, s):
            return "[%s]" % self.next.f(s)
        return locals()
    o3 = o2()
    assert o1.f("X") == "|X|"
    assert o2.f("Y") == "[|Y|]"
    assert o3.f("Z") == "[|Z|]", o3.f("Z")

@autotest
def contains_proxied():
    def f(self, a):
        return a in self
    o = prototype(f, a=10)
    assert 'a' in o
    assert o.f('a')
    assert not o.f('b')


@autotest
def getitem_proxied():
    def f(self, a):
        return self[a]
    o = prototype(f, a=29)
    assert o['a'] == 29
    assert o.f('a') == 29

@autotest
def equals_proxied_on_self():
    def g(self):
        return self
    def f(self, a):
        return self == a and a == self
    o = prototype(f, g)
    assert o == o.g()
    assert o.g() == o
    assert o.f(o)
    assert not o.f(None)

@autotest
def iterate_public_attrs():
    def f(self): pass
    def _g(self): pass
    o = prototype(f, _g, a=10, _b=20)
    assert [('f', f), ('a', 10)], list(o)

@autotest
def dicts_attrs_become_objects_when_looked_up():
    o = prototype(a={'b':{'c':{'d':3}}})
    assert o.a.b.c.d == 3, o.a.b.c.d
    o = prototype(a={'b':{2:{'d':3}}})
    assert o.a.b[2].d == 3, o.a.b.c.d

@autotest
def some_excercises_with_reflection_with_no_real_result():
    a = 42
    def F(b, c=84, *args, **kwargs):
        d = a
        e = b
        f = c
        def G(g, h=21, *orgs, **kworgs):
            i = a
            j = b
            k = c
            l = d
            m = e
            n = f
            o = g
            p = h
            return 63
        return locals()
    F(12)
    #my_F = FunctionType(code, globals, name, argdefaults, closure)
    assert F.__closure__[0].cell_contents == 42
    assert F.__defaults__ == (84,)
    assert F.__dict__ == {}
    assert F.__class__ == FunctionType
    assert F.__globals__ == globals()
    C = F.__code__
    assert C.co_argcount == 2
    assert C.co_consts[0] == None
    assert C.co_consts[1] == 21
    #assert C.co_consts[3] == 75
    assert C.co_cellvars == ('b', 'c', 'd', 'e', 'f')
    assert C.co_flags == 31, C.co_flags # 19 = no *args/**kwargs 23 = *args, 27 = **kwargs, 31 = *args + **kwargs
    assert C.co_freevars == ('a',)
    assert C.co_name == 'F'
    assert C.co_names == ('locals',), C.co_names
    assert C.co_nlocals == 5, C.co_nlocals
    assert C.co_stacksize == 7 # ??
    assert C.co_varnames == ('b', 'c', 'args', 'kwargs', 'G'), C.co_varnames
    G = C.co_consts[2]
    assert G.co_argcount == 2
    assert G.co_consts == (None, 63)
    assert G.co_cellvars == (), G.co_cellvars
    assert G.co_flags == 31, G.co_flags # 1=optimized | 2=newlocals | 4=*arg | 8=**arg
    assert G.co_freevars == ('a', 'b', 'c', 'd', 'e', 'f'), G.co_freevars
    assert G.co_name == 'G'
    assert G.co_names == (), G.co_names
    assert G.co_nlocals == 12, G.co_nlocals
    assert G.co_stacksize == 1, G.co_stacksize
    assert G.co_varnames == ('g', 'h', 'orgs', 'kworgs', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p'), G.co_varnames
  
    G_globals = F.__globals__
    G_globals.update(locals())
    G_arg_defaults = {} # ??
    G_closure = () # values for freevars come from globals
    G_closure = tuple(G_globals.get(var, "%s?" % var) for var in G.co_freevars)

    l = {}
    g = globals()
    eval("F(13)", g, l)
    assert g == globals()
    assert l == {}

@autotest
def use_prototype_as_replacement_for_object():
    class mythingy(prototype):
        a = 42
        def f1(self):
            return self.a

    assert isinstance(mythingy, prototype)
    assert isinstance(type(mythingy), meta)
    assert mythingy._prototypes == (mythingy,)
    assert hasattr(mythingy, 'f1' )
    assert mythingy.f1() == 42

    class m2(mythingy): # this replaces inheritance with delegation
        def f1(self):
            return self.a * 2
    assert isinstance(m2, prototype)
    assert isinstance(type(m2), meta)
    assert m2._prototypes == (m2, mythingy)
    assert m2.f1() == 84
    mythingy.a = 13
    assert m2.f1() == 26
    m2.a = 19
    assert m2.f1() == 38

