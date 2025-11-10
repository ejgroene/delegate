# Delegate

A prototype-based delegation system for Python 3 that replaces class-based inheritance with object composition through delegation.

## Overview

This library implements a SELF-inspired delegation model that eliminates the complexity of Python's class system while maintaining compatibility with existing Python code. By treating all objects uniformly, it removes the need for classmethods, staticmethods, and metaclasses, replacing these constructs with a single, consistent method lookup mechanism.

## Motivation

Traditional class-based inheritance introduces unnecessary complexity through special cases and exceptions. Prototype-based delegation offers a simpler model built on three principles:

1. **Uniform object model** - All objects have equal status; no distinction between classes and instances
2. **Consistent lookup** - Method resolution follows a single, predictable algorithm
3. **Uniform binding** - All methods bind identically, without special decorators or descriptors

This approach is inspired by [SELF: The Power of Simplicity](https://bibliography.selflanguage.org/_static/self-power.pdf), adapted to work within Python's ecosystem while maintaining interoperability with standard Python classes and objects.

## Installation

This is a single-file library with minimal dependencies. Install the required testing framework:

```bash
pip install selftest
```

Then import the module:

```python
from prototype import prototype
```

## Core Concepts

### Object Creation

Objects are created directly without classes. Parents and attributes are specified at instantiation:

```python
from prototype import prototype

# Base object with a method
base = prototype(area=lambda self: self.x * self.y)

# Objects with parents and attributes
obj_x = prototype(base, x=3)
obj_y = prototype(base, y=4)

# Multiple inheritance through delegation
composite = prototype(obj_x, obj_y)

print(composite.area())  # 12
```

### Method Resolution

Method lookup uses C3 linearization (identical to Python's MRO) implemented via topological sort. The algorithm constructs a dependency graph from parent relationships and traverses it in deterministic order, ensuring consistent resolution in complex delegation hierarchies.

### Parameter Injection

Methods receive up to three automatically injected parameters based on their signature:

- **`self`** - The object on which the method was invoked (receiver)
- **`this`** - The object where the method was defined (definer)
- **`super`** - Proxy to parent objects for method refinement

Parameters are injected by introspecting function signatures. Declare only the parameters you need:

```python
# Access to receiver only
obj = prototype(get_x=lambda self: self.x)

# Access to definer and receiver
obj = prototype(identify=lambda self, this: (self, this))

# Method refinement with super
base = prototype(compute=lambda n: n * 3)
refined = prototype(base, compute=lambda super, n: 2 * super.compute(n))

refined.compute(5)  # 30
```

The `super` parameter provides access to parent implementations, enabling method refinement without explicit parent references.

### Compatibility with Python Classes

The system interoperates with standard Python classes and objects:

```python
class PythonClass:
    def method(self):
        return 42

# Delegate to a class
obj = prototype(PythonClass)
obj.method()  # 42

# Delegate to an instance
instance = PythonClass()
obj = prototype(instance)
obj.method()  # 42
```

For compatibility, functions using `cls` as the first parameter receive `this` instead of `self`, matching Python's classmethod behavior.

### Class Syntax

Prototype objects can be defined using class syntax for familiarity:

```python
class Shape(prototype):
    def area(self):
        return self.x * self.y

class rectangle(Shape):
    x = 3
    y = 4

rectangle.area()  # 12
```

This syntax creates prototype objects, not classes. The metaclass intercepts class creation and returns prototype instances.

## Technical Details

### Implementation

The library consists of three core components:

- **`prototype`** - Main class representing all objects, stores parents in `__bases__` and attributes in `__dict__`
- **`method`** - Bound method wrapper that handles parameter injection and serves as the `super` proxy
- **`meta`** - Metaclass that enables class syntax by intercepting class definitions

### Method Lookup Algorithm

```python
def linearize(obj):
    """C3 compatible linearization via topological sort"""
    # Build dependency graph from parent relationships
    # Traverse in static order
    # Return linearized list of objects
```

The `lookup()` method traverses this linearization, checking each object's `__dict__` for the requested attribute. When found, functions are wrapped in `method` objects that handle parameter injection.

### Dunder Method Handling

Special methods (`__call__`, `__eq__`, `__hash__`, etc.) are looked up in the instance before falling back to the class, matching Python's behavior while maintaining delegation semantics.

## Examples

### Diamond Inheritance

```python
class A(prototype):
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

D.product()  # 15
```

### Method Refinement

```python
# Base implementation
logger = prototype(
    log=lambda msg: print(f"[LOG] {msg}")
)

# Refined implementation
timestamped_logger = prototype(
    logger,
    log=lambda super, msg: super.log(f"{time.time()}: {msg}")
)

# Further refinement
filtered_logger = prototype(
    timestamped_logger,
    log=lambda self, super, msg: super.log(msg) if self.level > 0 else None,
    level=1
)
```

### Dynamic Object Composition

```python
# Create objects at runtime
def make_counter(start=0):
    def increment(self):
        self.value += 1
        return self.value
    
    def decrement(self):
        self.value -= 1
        return self.value
    
    return prototype(
        value=start,
        increment=increment,
        decrement=decrement
    )

counter = make_counter(10)
counter.increment()  # 11
counter.decrement()  # 10
```

## Testing

The library includes comprehensive inline tests using the `@test` decorator. Tests cover:

- Object creation and initialization
- Method lookup and binding
- Parameter injection
- Python class/object delegation
- C3 linearization
- Dunder method handling
- Edge cases and error conditions

Refer to [prototype.py](./prototype.py) for complete test coverage and additional usage examples.

## Requirements

- Python 3.9+ (requires `graphlib.TopologicalSorter`)
- `selftest` - Testing framework for inline tests

## License

GNU General Public License v3.0

## References

- [SELF: The Power of Simplicity](https://bibliography.selflanguage.org/_static/self-power.pdf) - Original inspiration
- [Python C3 Linearization](https://www.python.org/download/releases/2.3/mro/) - Method resolution order
- [Python graphlib](https://docs.python.org/3/library/graphlib.html) - Topological sorting implementation
