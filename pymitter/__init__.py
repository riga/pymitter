# coding: utf-8

"""
Python port of the extended Node.js EventEmitter 2 approach providing namespaces, wildcards and TTL.
"""

from __future__ import annotations

__author__ = "Marcel Rieger"
__author_email__ = "github.riga@icloud.com"
__copyright__ = "Copyright 2014-2024, Marcel Rieger"
__credits__ = ["Marcel Rieger"]
__contact__ = "https://github.com/riga/pymitter"
__license__ = "BSD-3-Clause"
__status__ = "Development"
__version__ = "0.5.1"
__all__ = ["EventEmitter", "Listener"]

import time
import fnmatch
import asyncio
from typing import Callable, Awaitable, Sequence, Any, Generator


class EventEmitter(object):
    """
    The EventEmitter class, ported from Node.js EventEmitter 2.

    When *wildcard* is *True*, wildcards in event names are taken into account. Event names have
    namespace support with each namspace being separated by a *delimiter* which defaults to ``"."``.

    When *new_listener* is *True*, a ``"new_listener"`` event is emitted every time a new listener
    is registered with arguments ``(func, event=None)``. *max_listeners* configures the total
    maximum number of event listeners. A negative numbers means that this number is unlimited.
    """

    new_listener_event = "new_listener"

    def __init__(
        self,
        *,
        delimiter: str = ".",
        wildcard: bool = False,
        new_listener: bool = False,
        max_listeners: int = -1,
    ) -> None:
        super().__init__()

        # store attributes
        self.new_listener = new_listener
        self.max_listeners = max_listeners

        # tree of nodes keeping track of nested events
        self._event_tree = Tree(wildcard=wildcard, delimiter=delimiter)

        # flat list of listeners triggerd on "any" event
        self._any_listeners: list[Listener] = []

    @property
    def num_listeners(self) -> int:
        return self._event_tree.num_listeners() + len(self._any_listeners)

    def on(
        self,
        event: str,
        func: Callable | None = None,
        ttl: int = -1,
    ) -> Callable:
        """
        Registers a function to an event. *ttl* defines the times to listen with negative values
        meaning infinity. When *func* is *None*, decorator usage is assumed. Returns the wrapped
        function.
        """
        def on(func: Callable) -> Callable:
            # do not register the function when the maximum would be exceeded
            if 0 <= self.max_listeners <= self.num_listeners:
                return func

            # create a new listener and add it
            self._event_tree.add_listener(event, Listener(func, event, ttl))

            if self.new_listener and event != self.new_listener_event:
                self.emit(self.new_listener_event, func, event)

            return func

        return on(func) if func else on  # type: ignore[return-value]

    def once(self, event: str, func: Callable | None = None) -> Callable:
        """
        Registers a function to an event that is called once. When *func* is *None*, decorator usage
        is assumed. Returns the wrapped function.
        """
        return self.on(event, func=func, ttl=1)

    def on_any(self, func: Callable | None = None, ttl: int = -1) -> Callable:
        """
        Registers a function that is called every time an event is emitted. *ttl* defines the times
        to listen with negative values meaning infinity. When *func* is *None*, decorator usage is
        assumed. Returns the wrapped function.
        """
        def on_any(func: Callable) -> Callable:
            # do not register the function when the maximum would be exceeded
            if 0 <= self.max_listeners <= self.num_listeners:
                return func

            # create a new listener and add it
            self._any_listeners.append(Listener(func, "", ttl))

            if self.new_listener:
                self.emit(self.new_listener_event, func)

            return func

        return on_any(func) if func else on_any  # type: ignore[return-value]

    def off(self, event: str, func: Callable | None = None) -> Callable:
        """
        Removes a function that is registered to an event. When *func* is *None*, decorator usage is
        assumed. Returns the wrapped function.
        """
        def off(func: Callable) -> Callable:
            self._event_tree.remove_listeners_by_func(event, func)

            return func

        return off(func) if func else off  # type: ignore[return-value]

    def off_any(self, func: Callable | None = None) -> Callable:
        """
        Removes a function that was registered via :py:meth:`on_any`. When *func* is *None*,
        decorator usage is assumed. Returns the wrapped function.
        """
        def off_any(func: Callable) -> Callable:
            self._any_listeners[:] = [
                listener
                for listener in self._any_listeners
                if listener.func != func
            ]

            return func

        return off_any(func) if func else off_any  # type: ignore[return-value]

    def off_all(self) -> None:
        """
        Removes all registered functions.
        """
        self._event_tree.clear()
        del self._any_listeners[:]

    def listeners(self, event: str) -> list[Callable]:
        """
        Returns all functions that are registered to an event.
        """
        return [listener.func for listener in self._event_tree.find_listeners(event)]

    def listeners_any(self) -> list[Callable]:
        """
        Returns all functions that were registered using :py:meth:`on_any`.
        """
        return [listener.func for listener in self._any_listeners]

    def listeners_all(self) -> list[Callable]:
        """
        Returns all registered functions, ordered by their registration time.
        """
        listeners = list(self._any_listeners)
        nodes = list(self._event_tree.nodes.values())
        while nodes:
            node = nodes.pop(0)
            nodes.extend(node.nodes.values())
            listeners.extend(node.listeners)

        # sort them
        listeners = sorted(listeners, key=lambda listener: listener.time)

        return [listener.func for listener in listeners]

    def _emit(self, event: str, *args, **kwargs) -> list[Awaitable]:
        listeners = self._event_tree.find_listeners(event)
        if event != self.new_listener_event:
            listeners.extend(self._any_listeners)
        listeners = sorted(listeners, key=lambda listener: listener.time)

        # call listeners in order, keep track of awaitables from coroutines functions
        awaitables = []
        for listener in listeners:
            # since listeners can emit events themselves,
            # deregister them before calling if needed
            if listener.ttl == 1:
                self.off(listener.event, func=listener.func)

            res = listener(*args, **kwargs)
            if listener.is_coroutine or listener.is_async_callable:
                awaitables.append(res)

        return awaitables

    def emit(self, event: str, *args, **kwargs) -> None:
        """
        Emits an *event*. All functions of events that match *event* are invoked with *args* and
        *kwargs* in the exact order of their registration, with the exception of async functions
        that are invoked in a separate event loop.
        """
        # emit normal functions and get awaitables of async ones
        awaitables = self._emit(event, *args, **kwargs)

        # handle awaitables
        if awaitables:
            async def start():
                await asyncio.gather(*awaitables)
            asyncio.run(start())

    async def emit_async(self, event: str, *args, **kwargs) -> None:
        """
        Awaitable version of :py:meth:`emit`. However, this method does not start a new event loop
        but uses the existing one.
        """
        # emit normal functions and get awaitables of async ones
        awaitables = self._emit(event, *args, **kwargs)

        # handle awaitables
        if awaitables:
            await asyncio.gather(*awaitables)

    def emit_future(self, event: str, *args, **kwargs) -> None:
        """
        Deferred version of :py:meth:`emit` with all awaitable events being places at the end of the
        existing event loop (using :py:func:`asyncio.ensure_future`).
        """
        # emit normal functions and get awaitables of async ones
        awaitables = self._emit(event, *args, **kwargs)

        # handle awaitables
        if awaitables:
            asyncio.ensure_future(asyncio.gather(*awaitables))


class BaseNode(object):

    def __init__(self, wildcard: bool, delimiter: str) -> None:
        super().__init__()

        self.wildcard = wildcard
        self.delimiter = delimiter
        self.parent = None
        self.nodes: dict[str, Node] = {}

    def clear(self) -> None:
        self.nodes.clear()

    def add_node(self, node: "Node") -> "Node":
        # when there is a node with the exact same name (pattern), merge listeners
        if node.name in self.nodes:
            _node = self.nodes[node.name]
            _node.listeners.extend(node.listeners)
            return _node

        # otherwise add it and set its parent
        self.nodes[node.name] = node
        node.parent = self  # type: ignore[assignment]

        return node

    def walk_nodes(self) -> Generator[tuple[str, tuple[str, ...], list[str]], None, None]:
        queue = [
            (name, [name], node)
            for name, node in self.nodes.items()
        ]
        while queue:
            name, path, node = queue.pop(0)

            # get names of child names
            child_names = list(node.nodes)

            # yield the name, the path leading to the node and names of child nodes that can be
            # adjusted in place by the outer context to change the traversal (similar to os.walk)
            yield (name, tuple(path), child_names)

            # add remaining child nodes
            queue.extend([
                (child_name, path + [child_name], node.nodes[child_name])
                for child_name in child_names
            ])


class Node(BaseNode):
    """
    Actual named nodes containing listeners.
    """

    @classmethod
    def str_is_pattern(cls, s: str) -> bool:
        return "*" in s or "?" in s

    def __init__(self, name: str, *args) -> None:
        super().__init__(*args)

        self.name = name
        self.listeners: list[Listener] = []

    def num_listeners(self, recursive: bool = True) -> int:
        n = len(self.listeners)

        if recursive:
            n += sum(node.num_listeners(recursive=recursive) for node in self.nodes.values())

        return n

    def remove_listeners_by_func(self, func: Callable) -> None:
        self.listeners[:] = [listener for listener in self.listeners if listener.func != func]

    def add_listener(self, listener: Listener) -> None:
        self.listeners.append(listener)

    def check_name(self, pattern: str) -> bool:
        if self.wildcard:
            if self.str_is_pattern(pattern):
                return fnmatch.fnmatch(self.name, pattern)
            if self.str_is_pattern(self.name):
                return fnmatch.fnmatch(pattern, self.name)

        return self.name == pattern

    def find_nodes(self, event: str | Sequence[str]) -> list[Node]:
        # trivial case
        if not event:
            return []

        # parse event
        if isinstance(event, (list, tuple)):
            pattern, sub_patterns = event[0], event[1:]
        else:
            pattern, *sub_patterns = event.split(self.delimiter)  # type: ignore[attr-defined]

        # first make sure that pattern matches _this_ name
        if not self.check_name(pattern):
            return []

        # when there are no sub patterns, return this one
        if not sub_patterns:
            return [self]

        # recursively match sub names with nodes
        return sum((node.find_nodes(sub_patterns) for node in self.nodes.values()), [])


class Tree(BaseNode):
    """
    Top-level node without a name or listeners, but providing higher-level node access.
    """

    def num_listeners(self) -> int:
        return sum(node.num_listeners(recursive=True) for node in self.nodes.values())

    def find_nodes(self, *args, **kwargs) -> list[Node]:
        return sum((node.find_nodes(*args, **kwargs) for node in self.nodes.values()), [])

    def add_listener(self, event: str, listener: Listener) -> None:
        # add nodes without evaluating wildcards, this is done during node lookup only
        names = event.split(self.delimiter)

        # lookup the deepest existing parent
        node = self
        while names:
            name = names.pop(0)
            if name in node.nodes:
                node = node.nodes[name]  # type: ignore[assignment]
            else:
                new_node = Node(name, self.wildcard, self.delimiter)
                node.add_node(new_node)
                node = new_node  # type: ignore[assignment]

        # add the listeners
        node.add_listener(listener)  # type: ignore[arg-type, call-arg]

    def remove_listeners_by_func(self, event: str, func: Callable) -> None:
        for node in self.find_nodes(event):
            node.remove_listeners_by_func(func)

    def find_listeners(self, event: str, sort: bool = True) -> list[Listener]:
        listeners = sum((node.listeners for node in self.find_nodes(event)), [])

        # sort by registration time
        if sort:
            listeners = sorted(listeners, key=lambda listener: listener.time)

        return listeners


class Listener(object):
    """
    A simple event listener class that wraps a function *func* for a specific *event* and that keeps
    track of the times to listen left.
    """

    def __init__(self: Listener, func: Callable, event: str, ttl: int) -> None:
        super().__init__()

        self.func = func
        self.event = event
        self.ttl = ttl

        # store the registration time
        self.time = time.monotonic()

    @property
    def is_coroutine(self) -> bool:
        return asyncio.iscoroutinefunction(self.func)

    @property
    def is_async_callable(self) -> bool:
        return asyncio.iscoroutinefunction(getattr(self.func, "__call__", None))

    def __call__(self, *args, **kwargs) -> Any:
        """
        Invokes the wrapped function when ttl is non-zero, decreases the ttl value when positive and
        returns its return value.
        """
        result = None
        if self.ttl != 0:
            result = self.func(*args, **kwargs)

        if self.ttl > 0:
            self.ttl -= 1

        return result
