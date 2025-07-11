import asyncio
import unittest

from pymitter import EventEmitter


class SyncTestCase(unittest.TestCase):
    def test_callback_usage(self):
        ee = EventEmitter()
        stack = []

        def handler(arg):
            stack.append("callback_usage_" + arg)

        ee.on("callback_usage", handler)

        ee.emit("callback_usage", "foo")
        assert tuple(stack) == ("callback_usage_foo",)

    def test_decorator_usage(self):
        ee = EventEmitter()
        stack = []

        @ee.on("decorator_usage")
        def handler(arg):
            stack.append("decorator_usage_" + arg)

        ee.emit("decorator_usage", "bar")
        assert tuple(stack) == ("decorator_usage_bar",)

    def test_ttl_on(self):
        ee = EventEmitter()
        stack = []

        @ee.on("ttl_on", ttl=1)
        def handler(arg):
            stack.append("ttl_on_" + arg)

        ee.emit("ttl_on", "foo")
        assert tuple(stack) == ("ttl_on_foo",)

        ee.emit("ttl_on", "bar")
        assert tuple(stack) == ("ttl_on_foo",)

    def test_ttl_once(self):
        ee = EventEmitter()
        stack = []

        @ee.once("ttl_once")
        def handler(arg):
            stack.append("ttl_once_" + arg)

        ee.emit("ttl_once", "foo")
        assert tuple(stack) == ("ttl_once_foo",)

        ee.emit("ttl_once", "bar")
        assert tuple(stack) == ("ttl_once_foo",)

    def test_walk_nodes(self):
        # helper to recursively convert itertables to tuples
        def t(iterable):
            return tuple((obj if isinstance(obj, str) else t(obj)) for obj in iterable)

        ee = EventEmitter(wildcard=True)
        assert t(ee._event_tree.walk_nodes()) == ()

        # normal traversal
        ee.on("foo.bar.test")(lambda: None)
        ee.on("foo.bar.test2")(lambda: None)
        assert t(ee._event_tree.walk_nodes()) == (
            ("foo", ("foo",), ("bar",)),
            ("bar", ("foo", "bar"), ("test", "test2")),
            ("test", ("foo", "bar", "test"), ()),
            ("test2", ("foo", "bar", "test2"), ()),
        )

        # empty tree after removing all listeners
        ee.off_all()
        assert t(ee._event_tree.walk_nodes()) == ()

        # traversal with in-place updates
        ee.on("foo.bar.test")(lambda: None)
        ee.on("foo.bar.test2")(lambda: None)
        stack = []
        for name, path, children in ee._event_tree.walk_nodes():
            stack.append(t((name, path, children)))
            if name == "bar":
                children.remove("test2")
        assert t(stack) == (
            ("foo", ("foo",), ("bar",)),
            ("bar", ("foo", "bar"), ("test", "test2")),
            ("test", ("foo", "bar", "test"), ()),
        )

    def test_on_wildcards(self):
        def hits(handle: str, emit: str) -> bool:
            ee = EventEmitter(wildcard=True)
            stack = []
            token = object()

            @ee.on(handle)
            def handler():
                stack.append(token)

            ee.emit(emit)
            return tuple(stack) == (token,)

        assert hits("on_all.*", "on_all.foo")
        assert hits("on_all.foo", "on_all.*")
        assert hits("on_all.*", "on_all.*")

        assert hits("on_all.foo.bar", "on_all.*.bar")
        assert hits("on_all.*.bar", "on_all.foo.bar")

        assert hits("on_all.fo?", "on_all.foo")  # codespell:ignore
        assert hits("on_all.foo", "on_all.fo?")  # codespell:ignore
        assert hits("on_all.?", "on_all.?")

        assert not hits("on_all.f?", "on_all.foo")
        assert not hits("on_all.foo", "on_all.f?")
        assert not hits("on_all.f?", "on_all.?")
        assert not hits("on_all.?", "on_all.f?")

        assert not hits("on_all.foo.bar", "on_all.*")
        assert not hits("on_all.*", "on_all.foo.bar")

    def test_on_any(self):
        ee = EventEmitter()
        stack = []

        @ee.on("foo")
        def handler1():
            stack.append("foo")

        @ee.on_any()
        def handler2():
            stack.append("bar")

        ee.emit("foo")
        assert tuple(stack) == ("foo", "bar")

    def test_off_any(self):
        ee = EventEmitter()
        stack = []

        @ee.on_any
        def handler1():
            stack.append("foo")

        ee.emit("xyz")
        assert tuple(stack) == ("foo",)

        del stack[:]
        ee.off_any(handler1)

        ee.emit("xyz")
        assert tuple(stack) == ()
        assert ee.num_listeners == 0

    def test_off_all(self):
        ee = EventEmitter()

        @ee.on_any
        def handler1():
            pass

        @ee.on("foo")
        def handler2():
            pass

        assert ee.num_listeners == 2

        ee.off_all()
        assert ee.num_listeners == 0

    def test_off_event(self):
        ee = EventEmitter(wildcard=True)

        ee.on("foo.bar")(lambda: None)
        ee.on("foo.baz")(lambda: None)

        assert ee.num_listeners == 2
        assert len(nodes := ee._event_tree.find_nodes("foo.bar")) == 1
        assert nodes[0].num_listeners() == 1
        assert nodes[0].name == "bar"

        ee.off("foo.bar")
        assert ee.num_listeners == 1
        assert len(nodes := ee._event_tree.find_nodes("foo.bar")) == 1
        assert nodes[0].num_listeners() == 0

        ee.on("foo.bar")(lambda: None)
        assert ee.num_listeners == 2

        ee.off("foo.*")
        assert ee.num_listeners == 0

    def test_listeners(self):
        ee = EventEmitter(wildcard=True)

        @ee.on("foo")
        def h1():
            pass

        @ee.on("foo")
        def h2():
            pass

        @ee.on("bar")
        def h3():
            pass

        @ee.once("baz")
        def h4():
            pass

        @ee.on_any
        def h5():
            pass

        assert tuple(ee.listeners_any()) == (h5,)
        assert tuple(ee.listeners_all()) == (h1, h2, h3, h4, h5)
        assert tuple(ee.listeners("foo")) == (h1, h2)
        assert tuple(ee.listeners("bar")) == (h3,)
        assert tuple(ee.listeners("ba?")) == (h3, h4)

    def test_emit_all(self):
        ee = EventEmitter(wildcard=True)
        stack = []

        @ee.on("emit_all.foo")
        def handler():
            stack.append("emit_all.foo")

        ee.emit("emit_all.*")
        assert stack[-1] == "emit_all.foo"

    def test_on_reverse_pattern(self):
        ee = EventEmitter(wildcard=True)
        stack = []

        @ee.on("foo.bar")
        def handler1():
            stack.append("on_foo_bar")

        @ee.on("foo.baz")
        def handler2():
            stack.append("on_foo_baz")

        @ee.on("foo.bar.baz.test")
        def handler3():
            stack.append("on_foo_bar_baz_test")

        ee.emit("foo.ba?")
        assert tuple(stack) == ("on_foo_bar", "on_foo_baz")

        del stack[:]
        ee.emit("foo.bar.*.test")
        assert tuple(stack) == ("on_foo_bar_baz_test",)

    def test_delimiter(self):
        ee = EventEmitter(wildcard=True, delimiter=":")
        stack = []

        @ee.on("delimiter:*")
        def handler():
            stack.append("delimiter")

        ee.emit("delimiter:foo")
        assert tuple(stack) == ("delimiter",)

    def test_new(self):
        ee = EventEmitter(new_listener=True)
        stack = []

        @ee.on("new_listener")
        def handler(func, event=None):
            stack.append((func, event))

        def newhandler():
            pass

        ee.on("new", newhandler)
        ee.on_any(newhandler)

        assert tuple(stack) == ((newhandler, "new"), (newhandler, None))

    def test_max(self):
        ee = EventEmitter(max_listeners=1)
        stack = []

        @ee.on("max")
        def handler1():
            stack.append("max_1")

        @ee.on("max")
        def handler2():
            stack.append("max_2")

        ee.emit("max")
        assert tuple(stack) == ("max_1",)

    def test_tree(self):
        ee = EventEmitter()
        stack = []

        @ee.on("max")
        def handler1():
            stack.append("max_1")

        @ee.once("max")
        def handler2():
            stack.append("max_2")

        assert ee.num_listeners == 2
        assert len(ee._event_tree.nodes["max"].listeners) == 2

        ee.emit("max")
        assert tuple(stack) == ("max_1", "max_2")
        del stack[:]

        ee.emit("max")
        assert tuple(stack) == ("max_1",)
        del stack[:]

        assert ee.num_listeners == 1
        assert "max" in ee._event_tree.nodes
        assert len(ee._event_tree.nodes["max"].listeners) == 1

        ee.off("max", handler1)
        assert ee.num_listeners == 0


class AsyncTestCase(unittest.IsolatedAsyncioTestCase):
    def test_async_callback_usage(self):
        ee = EventEmitter()
        stack = []

        async def handler(arg):  # noqa: RUF029
            stack.append("async_callback_usage_" + arg)

        ee.on("async_callback_usage", handler)

        ee.emit("async_callback_usage", "foo")
        assert tuple(stack) == ("async_callback_usage_foo",)

    def test_async_decorator_usage(self):
        ee = EventEmitter()
        stack = []

        @ee.on("async_decorator_usage")
        async def handler(arg):  # noqa: RUF029
            stack.append("async_decorator_usage_" + arg)

        ee.emit("async_decorator_usage", "bar")
        assert tuple(stack) == ("async_decorator_usage_bar",)

    async def test_await_async_callback_usage(self):
        ee = EventEmitter()
        stack = []

        async def handler(arg):  # noqa: RUF029
            stack.append("await_async_callback_usage_" + arg)

        ee.on("await_async_callback_usage", handler)

        res = ee.emit_async("await_async_callback_usage", "foo")
        assert len(stack) == 0

        await res
        assert tuple(stack) == ("await_async_callback_usage_foo",)

    async def test_await_async_decorator_usage(self):
        ee = EventEmitter()
        stack = []

        @ee.on("await_async_decorator_usage")
        async def handler(arg):  # noqa: RUF029
            stack.append("await_async_decorator_usage_" + arg)

        res = ee.emit_async("await_async_decorator_usage", "bar")
        assert len(stack) == 0

        await res
        assert tuple(stack) == ("await_async_decorator_usage_bar",)

    async def test_emit_future(self):
        ee = EventEmitter()
        stack = []

        @ee.on("emit_future")
        async def handler(arg):  # noqa: RUF029
            stack.append("emit_future_" + arg)

        async def test():
            ee.emit_future("emit_future", "bar")
            assert len(stack) == 0

            # let all non-deferred events on the event loop pass
            await asyncio.sleep(0)

            assert tuple(stack) == ("emit_future_bar",)

        await test()

    def test_supports_async_callables(self):
        ee = EventEmitter()
        stack = []

        class EventHandler:
            async def __call__(self, arg):
                stack.append(arg)

        ee.on("event", EventHandler())

        ee.emit("event", "arg")
        assert tuple(stack) == ("arg",)
