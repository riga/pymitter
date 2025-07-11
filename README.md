<!-- marker-before-logo -->

<p align="center">
  <img src="https://media.githubusercontent.com/media/riga/pymitter/master/assets/logo.png" width="400" />
</p>

<!-- marker-after-logo -->

<!-- marker-before-badges -->

<p align="center">
  <a href="http://pymitter.readthedocs.io">
    <img alt="Documentation status" src="https://readthedocs.org/projects/pymitter/badge/?version=latest" />
  </a>
  <img alt="Python version" src="https://img.shields.io/badge/Python-%E2%89%A53.9-blue" />
  <a href="https://pypi.python.org/pypi/pymitter">
    <img alt="Package version" src="https://img.shields.io/pypi/v/pymitter.svg?style=flat" />
  </a>
  <a href="https://pypi.python.org/pypi/pymitter">
    <img alt="Package downloads" src="https://img.shields.io/pypi/dm/pymitter.svg" />
  </a>
  <a href="https://codecov.io/gh/riga/pymitter">
    <img alt="Code coverage" src="https://codecov.io/gh/riga/pymitter/branch/master/graph/badge.svg?token=MePbStZF7U" />
  </a>
  <a href="https://github.com/riga/pymitter/actions/workflows/lint_and_test.yml">
    <img alt="Build status" src="https://github.com/riga/pymitter/actions/workflows/lint_and_test.yml/badge.svg" />
  </a>
  <a href="https://github.com/riga/pymitter/blob/master/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/riga/pymitter.svg" />
  </a>
</p>

<!-- marker-after-badges -->

<!-- marker-before-header -->

Python port of the extended Node.js EventEmitter 2 approach of https://github.com/asyncly/EventEmitter2 providing namespaces, wildcards and TTL.

Original source hosted at [GitHub](https://github.com/riga/pymitter).

<!-- marker-after-header -->

<!-- marker-before-body -->

## Features

- Namespaces with wildcards
- Times to listen (TTL)
- Usage via decorators or callbacks
- Coroutine support
- Lightweight implementation, good performance

## Installation

Simply install via [pip](https://pypi.python.org/pypi/pymitter):

```shell
pip install pymitter
```

- The last version supporting Python 2 was [v0.3.2](https://github.com/riga/pymitter/tree/v0.3.2) ([PyPI](https://pypi.org/project/pymitter/0.3.2)).
- The last version supporting Python ≤3.8 was [v1.0.0](https://github.com/riga/pymitter/tree/v1.0.0) ([PyPI](https://pypi.org/project/pymitter/1.0.0)).

## Examples

### Basic usage

```python
from pymitter import EventEmitter


ee = EventEmitter()


# decorator usage
@ee.on("my_event")
def handler1(arg):
    print("handler1 called with", arg)


# callback usage
def handler2(arg):
    print("handler2 called with", arg)


ee.on("my_other_event", handler2)


# support for coroutine functions
@ee.on("my_third_event")
async def handler3(arg):
    print("handler3 called with", arg)


# emit
ee.emit("my_event", "foo")
# -> "handler1 called with foo"

ee.emit("my_other_event", "bar")
# -> "handler2 called with bar"

ee.emit("my_third_event", "baz")
# -> "handler3 called with baz"
```

### Coroutines

Wrapping `async` functions outside an event loop will start an internal event loop and calls to `emit` return synchronously.

```python
from pymitter import EventEmitter


ee = EventEmitter()


# register an async function
@ee.on("my_event")
async def handler1(arg):
    print("handler1 called with", arg)


# emit
ee.emit("my_event", "foo")
# -> "handler1 called with foo"
```

Wrapping `async` functions inside an event loop will use the same loop and `emit_async` is awaitable.

```python
from pymitter import EventEmitter


ee = EventEmitter()


async def main():
    # emit_async
    awaitable = ee.emit_async("my_event", "foo")
    # -> nothing printed yet

    await awaitable
    # -> "handler1 called with foo"
```

Use `emit_future` to not return awaitable objects but to place them at the end of the existing event loop (using `asyncio.ensure_future` internally).

### TTL (times to listen)

```python
from pymitter import EventEmitter


ee = EventEmitter()


@ee.once("my_event")
def handler1():
    print("handler1 called")


@ee.on("my_event", ttl=2)
def handler2():
    print("handler2 called")


ee.emit("my_event")
# -> "handler1 called"
# -> "handler2 called"

ee.emit("my_event")
# -> "handler2 called"

ee.emit("my_event")
# nothing called anymore
```

### Wildcards

```python
from pymitter import EventEmitter


ee = EventEmitter(wildcard=True)


@ee.on("my_event.foo")
def handler1():
    print("handler1 called")


@ee.on("my_event.bar")
def handler2():
    print("handler2 called")


@ee.on("my_event.*")
def hander3():
    print("handler3 called")


ee.emit("my_event.foo")
# -> "handler1 called"
# -> "handler3 called"

ee.emit("my_event.bar")
# -> "handler2 called"
# -> "handler3 called"

ee.emit("my_event.*")
# -> "handler1 called"
# -> "handler2 called"
# -> "handler3 called"
```

## API

### `EventEmitter(*, wildcard=False, delimiter=".", new_listener=False, max_listeners=-1)`

EventEmitter constructor. **Note**: always use *kwargs* for configuration.
When *wildcard* is *True*, wildcards are used as shown in [this example](#wildcards).
*delimiter* is used to separate namespaces within events.
If *new_listener* is *True*, the *"new_listener"* event is emitted every time a new listener is registered.
Functions listening to this event are passed `(func, event=None)`.
*max_listeners* defines the maximum number of listeners per event.
Negative values mean infinity.

- #### `on(event, func=None, ttl=-1)`
    Registers a function to an event.
    When *func* is *None*, decorator usage is assumed.
    *ttl* defines the times to listen. Negative values mean infinity.
    Returns the function.

- #### `once(event, func=None)`
    Registers a function to an event with `ttl = 1`.
    When *func* is *None*, decorator usage is assumed.
    Returns the function.

- #### `on_any(func=None)`
    Registers a function that is called every time an event is emitted.
    When *func* is *None*, decorator usage is assumed.
    Returns the function.

- #### `off(event, func=None)`
    Removes a function that is registered to an event and returns it.
    When *func* is *None*, all functions of *event* are removed and *None* is returned.

- #### `off_any(func=None)`
    Removes a function that was registered via `on_any()`.
    When *func* is *None*, decorator usage is assumed.
    Returns the function.

- #### `off_all()`
    Removes all functions of all events.

- #### `listeners(event)`
    Returns all functions that are registered to an event.
    Wildcards are not applied.

- #### `listeners_any()`
    Returns all functions that were registered using `on_any()`.

- #### `listeners_all()`
    Returns all registered functions.

- #### `emit(event, *args, **kwargs)`
    Emits an event.
    All functions of events that match *event* are invoked with *args* and *kwargs* in the exact order of their registration.
    Async functions are called in a new event loop.
    There is no return value.

- #### `(async) emit_async(event, *args, **kwargs)`
    Emits an event.
    All functions of events that match *event* are invoked with *args* and *kwargs* in the exact order of their registration.
    Awaitable objects returned by async functions are awaited in the outer event loop.
    Returns an `Awaitable`.

- #### `emit_future(event, *args, **kwargs)`
    Emits an event.
    All functions of events that match *event* are invoked with *args* and *kwargs* in the exact order of their registration.
    Awaitable objects returned by async functions are placed at the end of the event loop using `asyncio.ensure_future`.
    There is no return value.

## Development

- Source hosted at [GitHub](https://github.com/riga/pymitter)
- Python module hosted at [PyPI](https://pypi.python.org/pypi/pymitter)
- Report issues, questions, feature requests on [GitHub Issues](https://github.com/riga/pymitter/issues)

<!-- marker-after-body -->
