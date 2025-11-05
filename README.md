# Delegate

True delegation in Python 3.

Inheritance based on objects is simpler and more powerful than using classes.
This has been described for example [SELF: The Power of Simplicity](https://bibliography.selflanguage.org/_static/self-power.pdf)

Let look at an example:

```python
    from prototype import prototype

    a = prototype(length=lambda self: self.x * self.y)  # our base object, not a class
    b = prototype(a, x = 3)                             # b has parent a and defines x
    c = prototype(a, y = 4)                             # c also has parent a and defines y
    d = prototype(b, c)                                 # d has parents b and c, inherits x and y

    print(d.length())
    >>> 12
```

Here we create the objects `a`, `b`, `c` and `d`. Objects `b` and `c` have parent `a`, while `d` has two parents `b` and `c`. We'll introduce other syntax for this later.

The first thing to note is that what all objects are really equal. In Python a class is also an object but it is very special in many ways. This leads to difficult concepts such as classmethods, staticmethods and metaclasses. These distinctions do not exist in prototyping. Instead these concepts are all mapped to the trivally simple concept of method lookup.

Method lookup in delegation is a very straightforward process. The lookup for `length` start with the object `d`. If it is not there, it is looked up in the parents, following the chain up until there are no more parents.  The process is depth-first.