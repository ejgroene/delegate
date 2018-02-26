# Delegate
True delegation in Python

# Introduction

This module defines `prototype` which replaces inheritance with delegation.
It solves the 'self-problem' by using a single lineair delegate list. This
list of delegates is traversed when looking up attributes. This happens in
the same way, always and everywhere: object, type, class, classmethod,
staticmethod, metaclass, meta-meta-metaclass made easy!  

Instead of a class, each object has a prototype, which is nothing more
than another object, referenced as `self.next`. This object can also
have a prototype and so on. All objects in the chain behave the same way.  

Within methods `self` always refers to the object the methods was called
on. The object that defined the current method is refered to as `this`.

Suppose we have three objects in a chain and `object_b` defines `f`.

    object_a.f()         def f(self, this):
       \                     return 42
        \
        object_a         object_b         object_c
            \_____next_____/ \_____next_____/

         self              this          self.next

When we call `object_a.f()`, `f` will be found on `object_b` and executed 
with `self` bound to `object_a`, `this` bound to `object_b` and `self.next` 
pointing to `object_c`.  

This scheme will always be the same, on each level.


## Basic Object Creation

The Python class `prototype` creates the objects to work with by calling
it and supplying initializers: functions, attributes, objects, etc:

    a = object()                         # creates an empty object
    b = object(a)                        # creates b, delegating to a
    a = object(c=10)                     # initializes a.c to be 10
    a = object(lambda: {'b': 10})        # idem
    a = object(f=lambda self: 42)        # adds method a.f()
    def f(self):
        return 42
    a = object(f)                        # idem

All arguments above can be mixed and used at the same time. Given an
existing object `a`, you can replace `object` with `a`. This will let
the new object delegate to x:

    b = a()                              # equivalent to a = object(a)

## Convenient object creation:

Old and new style class definitions are convenient to create prototypes
with several related attributes and methods. All from create objects
(instances) not classes. Forget about classes.

### From Old Style Class Definition
For old style classes you can use `prototype` or an object as a decorator:

    @prototype
    class a:                             # creates object a
        c = 10
        def f(self):
            return 42

    @a                                   # creates b, delegating to a
    class b:
        c = 42

### From New Style Class Definition
For new style classes you can use `prototype` or and object as type in
your class definition:

    class a(prototype):                  # creates object a
        c = 10
        def f(self):
            return 42

    class b(a):                          # creates b, delegating to a
        c = 42

### From Initializers
It is also possible to use `def` to define an initializer function:

    @object
    def a():                             # creates a from initializer
        c = 10
        def f(self):
            return 42
        return locals()

    @a                                  # creates b, delegating to a
    def b():
        c = 42

## Methods, Self, This and Next

Any function passed to a prototype during creation is turned into a method.
The name of the method is derived from the name of the function:

    a = prototype
