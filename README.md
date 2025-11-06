# Delegate

True delegation in Python 3.


### Inheritance vs Delegation

Inheritance based on objects is simpler and more powerful than using classes.
This has been described for example [SELF: The Power of Simplicity](https://bibliography.selflanguage.org/_static/self-power.pdf)

Simplicity comes from three facts:

 1. All objects are really equal.
 2. Every lookup is equal.
 3. Every method binding is equal.

What one would call a class method or static method is really just a method call on another object. Every method invocation behaves the same.

SELF was an inspiration for my mini-project, but I do not try to replicate the SELF lookup algorithms. These come with their own problems, and I want to stick to Python a bit more.


### An Example

OK, now let's look at an example:

```python
    from prototype import prototype

    a = prototype(area=lambda self: self.x * self.y)  # our base object, not a class
    b = prototype(a, x = 3)                             # b has parent a and defines x
    c = prototype(a, y = 4)                             # c also has parent a and defines y
    d = prototype(b, c)                                 # d has parents b and c, inherits x and y

    print(d.area())
    >>> 12
```

Here we create the objects `a`, `b`, `c` and `d`. Objects `b` and `c` have parent `a`, while `d` has two parents `b` and `c`. We'll introduce other syntax for this later.


### All Object are Equal

The first thing to note is that all objects are really equal. In Python a class is also an object but it is very special in many ways. This leads to difficult concepts such as classmethods, staticmethods and metaclasses. These distinctions do not exist in prototyping. Instead these concepts are all mapped to the trivally simple concept of method lookup.


### Lookup

Method lookup in delegation is a very straightforward process. It makes a dependency graph from all the parents and traverses that in static order, see [Python graphlib](https://docs.python.org/3/library/graphlib.html).

This coincidentally is equivalent to the C3 linearization algorithm that Python uses for method lookup.


### Binding self, this and super

Perhaps the most critical is the proper binding of the methods in the objects.  My code works by looking up each function on any object and then bind it to `self`, `this` and `super`. Any binding performed by Python is first undone.

So all functions have aforementioned arguments. It is as simple as that. No exceptions. No decorators needed.

`self` is what you'd expect: it *always* is the object the lookup took place on in: `<self>.<function>`. No exceptions.

`this` is the object the method is found on. No exceptions.

`super` represent the parents of `this` and can be used to refine a method and then invoke the refined method.

Actually, there is an optimization: you can leave out any or all of them, and there won't be a complaint.

Oh, yes, there is one more thing: if you use `cls` instead of `self`, you will get another value: not `self` but `this`. This is such a typical example of the exceptions we want to get rid of, but it exists to allow for delegation to Python objects and classes.


### Using class Syntax

It is also possible to write:

```python
    from prototype import prototype

    class a(prototype):
        def area(self):
            return self.x * self.y

    b = prototype(a, x = 3)
    ... and so on
```

This creates exactly the same *object* `a` as above. For prototype objects that are to be used as parent, defining them using `class` syntax isn't too much a stretch.  You can also think of it as a desecration, but then you probably wouldn't be here.  Anyway, it shows how powerful Python is.


### Where Next?

If you are interested, it is best to look at the in-source unit tests in main file: [prototype.py](./prototype.py). These contain all the working ways to create objects.
