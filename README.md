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
on. The object that defined the current method is refered to as `self.this`.

Suppose we have three objects in a chain and `object_b` defines `f`.

    object_a.f()         def f(self):
       \                     return 42
        \
        object_a         object_b         object_c
            \_____next_____/ \_____next_____/

         self            self.this        self.next

When we call `object_a.f()`, `f` will be found on `object_b` and executed 
with `self` bound to `object_a`, `self.this` bound to `object_b` and `self.next` 
pointing to `object_c`.  

This scheme will always be the same, on each level.


## Basic Object Creation

The Python class `prototype` creates the objects to work with by calling
it and supplying initializers: functions, attributes, objects, etc:

    a = prototype()                     # creates an empty object
    b = prototype(a)                    # creates b, delegating to a
    a = prototype(c=10)                 # initializes a.c to be 10
    a = prototype(lambda: {'b': 10})    # idem
    a = prototype(f=lambda self: 42)    # adds method a.f()
    def f(self):
        return 42
    a = prototype(f)                    # idem

All arguments above can be mixed and used at the same time. Given an
existing object `a`, you can replace `prototype` with `a`. This will let
the new object delegate to x:

    b = a()                             # equivalent to a = prototype(a)

## Convenient Object Creation:

Old and new style class definitions are convenient to create prototypes
with several related attributes and methods. All forms create objects
(instances) not classes. Forget about classes.

### From Old Style Class Definition
For old style classes you can use `prototype` or an object as a decorator:

    @prototype
    class a:                            # creates object a
        c = 10
        def f(self):
            return 42

    @a                                  # creates b, delegating to a
    class b:
        c = 42

### From New Style Class Definition
For new style classes you can use `prototype` or and object as type in
your class definition:

    class a(prototype):                 # creates object a
        c = 10
        def f(self):
            return 42

    class b(a):                         # creates b, delegating to a
        c = 42

### From Initializers
It is also possible to use `def` to define an initializer function:

    @prototype
    def a():                            # creates a from initializer
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

    def f(self):
        return 42
    a = prototype(f)
    a.f()                               # returns 42

Alternatively, the name can be given explicitly:

    a = prototype(g=f)
    a.g()                               # returns 42

This makes it possible to define functions inline with lambda:

    a = prototype(f=lambda self: 42)

### Self
A function must at least define `self` as the first argument for it to be
accepted as method. The actual argument will point to the object the method
is called on, not the object the method is defined on.

### This
A method can use `self.this` to refer to the object on which the method is
defined. To be precise: the object the method is found on during lookup.

### Next
The attribute `self.next` points to the next delegate in the chain. This is 
the one just after `self.this`. This is convenient for if a method refines behaviour
of another method up in the chain (alas class thinking ;-). You can invoke the
method you are refining via `self.next`.

### Example

    class top(prototype):
        a = 16
        def f(self):
            return self.a
        def g(self):
            return self.this.a

    class middle(top):
        def f(self):
            return 2 * self.next.f()

    class bottom(middle):
        a = 42

    bottom.f()                           # will return 84
    bottom.g()                           # will return 16

### Closing Remarks
Delegation is formally a more general concept than inheritance. You can build
inheritance using delegation, but not the other way around. I found the inheritance-
based languages like Java and Python (and to some extent Smalltalk) not very easy
to understand. In fact I believe the inheritance lingo obfuscates things that are,
in essence, not that hard.  

Sometime in 2004 I created `Delegator`: true delegation in Java,
(https://sourceforge.net/projects/delegator/) which I showed off on the Object
 Technology Conference (now SPA). Now there is also true delegation for Python!  

I have created a Python version of delegation aiming to replace inheritance alltogether.
For Python, that would relief programmers of the burden of understanding the Python
object-lingo which is, I am sorry, very complicated.  

As to the main cause of why things in Python are so complicated I have a possible clue.
I think is is primarily due to the fact that the chain of creation does not follow
the chain of inheritance.  

The chain of creating is roughly: `type -> metaclass -> class -> instance`. Although the
class-instance relation is easy to use, extending this further requires the use of
special metaclasses (__metaclass__). So this does not look the same depending on the level,
and is quite confusing.  

The chain of inheritance depends on the base classes you use, which is an orthogonal 
concept (to the chain of creation). Base classes are what you think of in the first
place when thinking about inheritance in Python. These appear between () in the class
statements:

	class a(b, c, d):
		pass

The classes b, c, and d are the base classes. Of course each of these can have other
bases. More or less similar is:

	class d(object):
		pass
	class c(d):
		pass
	class c(c):
		pass

The father of all bases is `object`, while the mother of all (meta-) classes is 'type'.  

The base class of `type` is `object`, and the class of `object` is `type`. Of course.  

Now try to think of these two concepts, bases and types, as one in vertical direction and
the other in the horizontal direction. You now have a 2-dimensional inheritance solution.  

The Python VM calculates an Method Resolution Order (MRO) for each class that takes into account both
dimensions and gives you an undisputed, consistent (and deterministic) series of bases 
and types that are visited in order to perform attribute lookup.  

I you want to understand that, try reading this explaination of ionel: https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/.  

My point is: I do not have enough room in my head for that kind of complicated schemes.
I forget them. They swap out. Other stuff competes for my brain. As a result,
powerful use of meta-classes remains reserved for very special cases and is not suitable for daily
use.  

I want the concepts of metaclasses to be so easy that I can use it on a daily bases erm, basis. Just like
Javascript users use prototyping on a daily basis, perhaps without even noticing it.  

I did that by replacing inheritance with delegation AND unifying the chain of creation with
the chain of lookup.
