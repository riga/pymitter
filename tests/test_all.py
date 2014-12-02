#!/usr/bin/env python
# -*- coding: utf-8 -*-


# python imports
import os
import sys
import unittest


# adjust the path to import pymitter
base = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.insert(0, base)


# local imports
from pymitter import EventEmitter


class AllTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(AllTestCase, self).__init__(*args, **kwargs)

        self.ee1 = EventEmitter()
        self.ee2 = EventEmitter(wildcard=True)
        self.ee3 = EventEmitter(wildcard=True, delimiter=":")
        self.ee4 = EventEmitter(new_listener=True)
        self.ee5 = EventEmitter(max_listeners=1)

        self.stack = []

    def test_1_callback_usage(self):
        def handler(arg):
            self.stack.append("1_callback_usage_" + arg)

        self.ee1.on("1_callback_usage", handler)

        self.ee1.emit("1_callback_usage", "foo")
        self.assertTrue(self.stack[-1] == "1_callback_usage_foo")

    def test_1_decorator_usage(self):
        @self.ee1.on("1_decorator_usage")
        def handler(arg):
            self.stack.append("1_decorator_usage_" + arg)

        self.ee1.emit("1_decorator_usage", "bar")
        self.assertTrue(self.stack[-1] == "1_decorator_usage_bar")

    def test_1_ttl(self):
        # same as once
        @self.ee1.on("1_ttl", ttl=1)
        def handler(arg):
            self.stack.append("1_ttl_" + arg)

        self.ee1.emit("1_ttl", "foo")
        self.assertTrue(self.stack[-1] == "1_ttl_foo")

        self.ee1.emit("1_ttl", "bar")
        self.assertTrue(self.stack[-1] == "1_ttl_foo")

    def test_2_on_all(self):
        @self.ee2.on("2_on_all.*")
        def handler():
            self.stack.append("2_on_all")

        self.ee2.emit("2_on_all.foo")
        self.assertTrue(self.stack[-1] == "2_on_all")

    def test_2_emit_all(self):
        @self.ee2.on("2_emit_all.foo")
        def handler():
            self.stack.append("2_emit_all.foo")

        self.ee2.emit("2_emit_all.*")
        self.assertTrue(self.stack[-1] == "2_emit_all.foo")

    def test_3_delimiter(self):
        @self.ee3.on("3_delimiter:*")
        def handler():
            self.stack.append("3_delimiter")

        self.ee3.emit("3_delimiter:foo")
        self.assertTrue(self.stack[-1] == "3_delimiter")

    def test_4_new(self):
        @self.ee4.on("new_listener")
        def handler(func, event=None):
            self.stack.append((func, event))

        def newhandler():
            pass
        self.ee4.on("4_new", newhandler)

        self.assertTrue(self.stack[-1] == (newhandler, "4_new"))

    def test_5_max(self):
        @self.ee5.on("5_max")
        def handler1():
            self.stack.append("5_max_1")

        @self.ee5.on("5_max")
        def handler2():
            self.stack.append("5_max_2")

        self.ee5.emit("5_max")
        self.assertTrue(self.stack[-1] == "5_max_1")


if __name__ == "__main__":
    unittest.main()
