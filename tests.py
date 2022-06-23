#!/usr/bin/env python
# coding: utf-8

import unittest
import sys

from pymitter import EventEmitter


class EmitterProvider(object):

    def ee1(self, **kwargs):
        return EventEmitter(**kwargs)

    def ee2(self, **kwargs):
        return EventEmitter(wildcard=True, **kwargs)

    def ee3(self, **kwargs):
        return EventEmitter(wildcard=True, delimiter=":", **kwargs)

    def ee4(self, **kwargs):
        return EventEmitter(new_listener=True, **kwargs)

    def ee5(self, **kwargs):
        return EventEmitter(max_listeners=1, **kwargs)


class SyncTestCase(unittest.TestCase, EmitterProvider):

    def test_callback_usage(self):
        ee = self.ee1()
        stack = []

        def handler(arg):
            stack.append("callback_usage_" + arg)

        ee.on("callback_usage", handler)

        ee.emit("callback_usage", "foo")
        self.assertTrue(stack[-1] == "callback_usage_foo")

    def test_decorator_usage(self):
        ee = self.ee1()
        stack = []

        @ee.on("decorator_usage")
        def handler(arg):
            stack.append("decorator_usage_" + arg)

        ee.emit("decorator_usage", "bar")
        self.assertTrue(stack[-1] == "decorator_usage_bar")

    def test_ttl_on(self):
        ee = self.ee1()
        stack = []

        @ee.on("ttl_on", ttl=1)
        def handler(arg):
            stack.append("ttl_on_" + arg)

        ee.emit("ttl_on", "foo")
        self.assertTrue(stack[-1] == "ttl_on_foo")

        ee.emit("ttl_on", "bar")
        self.assertTrue(stack[-1] == "ttl_on_foo")

    def test_ttl_once(self):
        ee = self.ee1()
        stack = []

        @ee.once("ttl_once")
        def handler(arg):
            stack.append("ttl_once_" + arg)

        ee.emit("ttl_once", "foo")
        self.assertTrue(stack[-1] == "ttl_once_foo")

        ee.emit("ttl_once", "bar")
        self.assertTrue(stack[-1] == "ttl_once_foo")

    def test_on_all(self):
        ee = self.ee2()
        stack = []

        @ee.on("on_all.*")
        def handler():
            stack.append("on_all")

        ee.emit("on_all.foo")
        self.assertTrue(stack[-1] == "on_all")

    def test_emit_all(self):
        ee = self.ee2()
        stack = []

        @ee.on("emit_all.foo")
        def handler():
            stack.append("emit_all.foo")

        ee.emit("emit_all.*")
        self.assertTrue(stack[-1] == "emit_all.foo")

    def test_delimiter(self):
        ee = self.ee3()
        stack = []

        @ee.on("delimiter:*")
        def handler():
            stack.append("delimiter")

        ee.emit("delimiter:foo")
        self.assertTrue(stack[-1] == "delimiter")

    def test_new(self):
        ee = self.ee4()
        stack = []

        @ee.on("new_listener")
        def handler(func, event=None):
            stack.append((func, event))

        def newhandler():
            pass
        ee.on("new", newhandler)

        self.assertTrue(stack[-1] == (newhandler, "new"))

    def test_max(self):
        ee = self.ee5()
        stack = []

        @ee.on("max")
        def handler1():
            stack.append("max_1")

        @ee.on("max")
        def handler2():
            stack.append("max_2")

        ee.emit("max")
        self.assertTrue(stack[-1] == "max_1")


if sys.version_info[:2] >= (3, 8):

    class AsyncTestCase(unittest.IsolatedAsyncioTestCase, EmitterProvider):

        def test_async_callback_usage(self):
            ee = self.ee1()
            stack = []

            async def handler(arg):
                stack.append("async_callback_usage_" + arg)

            ee.on("async_callback_usage", handler)

            ee.emit("async_callback_usage", "foo")
            self.assertTrue(stack[-1] == "async_callback_usage_foo")

        def test_async_decorator_usage(self):
            ee = self.ee1()
            stack = []

            @ee.on("async_decorator_usage")
            async def handler(arg):
                stack.append("async_decorator_usage_" + arg)

            ee.emit("async_decorator_usage", "bar")
            self.assertTrue(stack[-1] == "async_decorator_usage_bar")

        async def test_await_async_callback_usage(self):
            ee = self.ee1()
            stack = []

            async def handler(arg):
                stack.append("await_async_callback_usage_" + arg)

            ee.on("await_async_callback_usage", handler)

            res = ee.emit_async("await_async_callback_usage", "foo")
            self.assertEqual(len(stack), 0)

            await res
            self.assertTrue(stack[-1] == "await_async_callback_usage_foo")

        async def test_await_async_decorator_usage(self):
            ee = self.ee1()
            stack = []

            @ee.on("await_async_decorator_usage")
            async def handler(arg):
                stack.append("await_async_decorator_usage_" + arg)

            res = ee.emit_async("await_async_decorator_usage", "bar")
            self.assertEqual(len(stack), 0)

            await res
            self.assertTrue(stack[-1] == "await_async_decorator_usage_bar")


if __name__ == "__main__":
    unittest.main()
