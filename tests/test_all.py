# coding: utf-8

import unittest
import sys
import asyncio

from pymitter import EventEmitter


class SyncTestCase(unittest.TestCase):

    def test_callback_usage(self):
        ee = EventEmitter()
        stack = []

        def handler(arg):
            stack.append("callback_usage_" + arg)

        ee.on("callback_usage", handler)

        ee.emit("callback_usage", "foo")
        self.assertTrue(tuple(stack) == ("callback_usage_foo",))

    def test_decorator_usage(self):
        ee = EventEmitter()
        stack = []

        @ee.on("decorator_usage")
        def handler(arg):
            stack.append("decorator_usage_" + arg)

        ee.emit("decorator_usage", "bar")
        self.assertTrue(tuple(stack) == ("decorator_usage_bar",))

    def test_ttl_on(self):
        ee = EventEmitter()
        stack = []

        @ee.on("ttl_on", ttl=1)
        def handler(arg):
            stack.append("ttl_on_" + arg)

        ee.emit("ttl_on", "foo")
        self.assertTrue(tuple(stack) == ("ttl_on_foo",))

        ee.emit("ttl_on", "bar")
        self.assertTrue(tuple(stack) == ("ttl_on_foo",))

    def test_ttl_once(self):
        ee = EventEmitter()
        stack = []

        @ee.once("ttl_once")
        def handler(arg):
            stack.append("ttl_once_" + arg)

        ee.emit("ttl_once", "foo")
        self.assertTrue(tuple(stack) == ("ttl_once_foo",))

        ee.emit("ttl_once", "bar")
        self.assertTrue(tuple(stack) == ("ttl_once_foo",))

    def test_walk_nodes(self):
        # helper to recursively convert itertables to tuples
        def t(iterable):
            return tuple((obj if isinstance(obj, str) else t(obj)) for obj in iterable)

        ee = EventEmitter()
        self.assertEqual(
            t(ee._event_tree.walk_nodes()),
            (),
        )

        # normal traversal
        ee.on("foo.bar.test")(lambda: None)
        ee.on("foo.bar.test2")(lambda: None)
        self.assertEqual(
            t(ee._event_tree.walk_nodes()),
            (
                ("foo", ("foo",), ("bar",)),
                ("bar", ("foo", "bar"), ("test", "test2")),
                ("test", ("foo", "bar", "test"), ()),
                ("test2", ("foo", "bar", "test2"), ()),
            ),
        )

        # empty tree after removing all listeners
        ee.off_all()
        self.assertEqual(
            t(ee._event_tree.walk_nodes()),
            (),
        )

        # traversal with in-place updates
        ee.on("foo.bar.test")(lambda: None)
        ee.on("foo.bar.test2")(lambda: None)
        stack = []
        for name, path, children in ee._event_tree.walk_nodes():
            stack.append(t((name, path, children)))
            if name == "bar":
                children.remove("test2")
        self.assertEqual(
            t(stack),
            (
                ("foo", ("foo",), ("bar",)),
                ("bar", ("foo", "bar"), ("test", "test2")),
                ("test", ("foo", "bar", "test"), ()),
            ),
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

        self.assertTrue(hits("on_all.*", "on_all.foo"))
        self.assertTrue(hits("on_all.foo", "on_all.*"))
        self.assertTrue(hits("on_all.*", "on_all.*"))

        self.assertTrue(hits("on_all.foo.bar", "on_all.*.bar"))
        self.assertTrue(hits("on_all.*.bar", "on_all.foo.bar"))

        self.assertTrue(hits("on_all.fo?", "on_all.foo"))
        self.assertTrue(hits("on_all.foo", "on_all.fo?"))
        self.assertTrue(hits("on_all.?", "on_all.?"))

        self.assertFalse(hits("on_all.f?", "on_all.foo"))
        self.assertFalse(hits("on_all.foo", "on_all.f?"))
        self.assertFalse(hits("on_all.f?", "on_all.?"))
        self.assertFalse(hits("on_all.?", "on_all.f?"))

        self.assertFalse(hits("on_all.foo.bar", "on_all.*"))
        self.assertFalse(hits("on_all.*", "on_all.foo.bar"))

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
        self.assertEqual(tuple(stack), ("foo", "bar"))

    def test_off_any(self):
        ee = EventEmitter()
        stack = []

        @ee.on_any
        def handler1():
            stack.append("foo")

        ee.emit("xyz")
        self.assertEqual(tuple(stack), ("foo",))

        del stack[:]
        ee.off_any(handler1)

        ee.emit("xyz")
        self.assertEqual(tuple(stack), ())
        self.assertEqual(ee.num_listeners, 0)

    def test_off_all(self):
        ee = EventEmitter()

        @ee.on_any
        def handler1():
            pass

        @ee.on("foo")
        def handler2():
            pass

        self.assertEqual(ee.num_listeners, 2)

        ee.off_all()
        self.assertEqual(ee.num_listeners, 0)

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

        self.assertEqual(tuple(ee.listeners_any()), (h5,))
        self.assertEqual(tuple(ee.listeners_all()), (h1, h2, h3, h4, h5))
        self.assertEqual(tuple(ee.listeners("foo")), (h1, h2))
        self.assertEqual(tuple(ee.listeners("bar")), (h3,))
        self.assertEqual(tuple(ee.listeners("ba?")), (h3, h4))

    def test_emit_all(self):
        ee = EventEmitter(wildcard=True)
        stack = []

        @ee.on("emit_all.foo")
        def handler():
            stack.append("emit_all.foo")

        ee.emit("emit_all.*")
        self.assertTrue(stack[-1] == "emit_all.foo")

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
        self.assertTrue(tuple(stack) == ("on_foo_bar", "on_foo_baz"))

        del stack[:]
        ee.emit("foo.bar.*.test")
        self.assertTrue(tuple(stack) == ("on_foo_bar_baz_test",))

    def test_delimiter(self):
        ee = EventEmitter(wildcard=True, delimiter=":")
        stack = []

        @ee.on("delimiter:*")
        def handler():
            stack.append("delimiter")

        ee.emit("delimiter:foo")
        self.assertTrue(tuple(stack) == ("delimiter",))

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

        self.assertTrue(tuple(stack) == ((newhandler, "new"), (newhandler, None)))

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
        self.assertTrue(tuple(stack) == ("max_1",))

    def test_tree(self):
        ee = EventEmitter()
        stack = []

        @ee.on("max")
        def handler1():
            stack.append("max_1")

        @ee.once("max")
        def handler2():
            stack.append("max_2")

        self.assertEqual(ee.num_listeners, 2)
        self.assertEqual(len(ee._event_tree.nodes["max"].listeners), 2)

        ee.emit("max")
        self.assertTrue(tuple(stack) == ("max_1", "max_2"))
        del stack[:]

        ee.emit("max")
        self.assertTrue(tuple(stack) == ("max_1",))
        del stack[:]

        self.assertEqual(ee.num_listeners, 1)
        self.assertTrue("max" in ee._event_tree.nodes)
        self.assertEqual(len(ee._event_tree.nodes["max"].listeners), 1)

        ee.off("max", handler1)
        self.assertEqual(ee.num_listeners, 0)


if sys.version_info[:2] >= (3, 8):

    class AsyncTestCase(unittest.IsolatedAsyncioTestCase):

        def test_async_callback_usage(self):
            ee = EventEmitter()
            stack = []

            async def handler(arg):
                stack.append("async_callback_usage_" + arg)

            ee.on("async_callback_usage", handler)

            ee.emit("async_callback_usage", "foo")
            self.assertEqual(tuple(stack), ("async_callback_usage_foo",))

        def test_async_decorator_usage(self):
            ee = EventEmitter()
            stack = []

            @ee.on("async_decorator_usage")
            async def handler(arg):
                stack.append("async_decorator_usage_" + arg)

            ee.emit("async_decorator_usage", "bar")
            self.assertEqual(tuple(stack), ("async_decorator_usage_bar",))

        async def test_await_async_callback_usage(self):
            ee = EventEmitter()
            stack = []

            async def handler(arg):
                stack.append("await_async_callback_usage_" + arg)

            ee.on("await_async_callback_usage", handler)

            res = ee.emit_async("await_async_callback_usage", "foo")
            self.assertEqual(len(stack), 0)

            await res
            self.assertEqual(tuple(stack), ("await_async_callback_usage_foo",))

        async def test_await_async_decorator_usage(self):
            ee = EventEmitter()
            stack = []

            @ee.on("await_async_decorator_usage")
            async def handler(arg):
                stack.append("await_async_decorator_usage_" + arg)

            res = ee.emit_async("await_async_decorator_usage", "bar")
            self.assertEqual(len(stack), 0)

            await res
            self.assertEqual(tuple(stack), ("await_async_decorator_usage_bar",))

        async def test_emit_future(self):
            ee = EventEmitter()
            stack = []

            @ee.on("emit_future")
            async def handler(arg):
                stack.append("emit_future_" + arg)

            async def test():
                ee.emit_future("emit_future", "bar")
                self.assertEqual(len(stack), 0)

                # let all non-deferred events on the event loop pass
                await asyncio.sleep(0)

                self.assertEqual(tuple(stack), ("emit_future_bar",))

            await test()

        def test_supports_async_callables(self):
            ee = EventEmitter()
            stack = []

            class EventHandler:
                async def __call__(self, arg):
                    stack.append(arg)

            ee.on("event", EventHandler())

            ee.emit("event", "arg")
            self.assertEqual(stack, ["arg"])
