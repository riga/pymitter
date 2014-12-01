# -*- coding: utf-8 -*-

# python imports
from distutils.core import setup


setup(
    name         = "pymitter",
    version      = "0.1.3",
    packages     = ["pymitter"],
    description  = "Python port of the extended Node.js EventEmitter2 approach"
                   "providing namespaces, wildcards and TTL.",
    author       = "Marcel Rieger",
    author_email = "marcelrieger@icloud.com",
    url          = "https://github.com/riga/pymitter",
    keywords     = [
        "event", "emitter", "eventemitter", "wildcard", "node", "nodejs"
    ],
    classifiers  = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ],
    long_description = """\
pymitter
========

Python port of the extended Node.js EventEmitter2 approach providing namespaces,
wildcards and TTL.


Example
-------

::

    from pymitter import EventEmitter

    ee = EventEmitter()

    # decorator usage
    @ee.on("myevent")
    def handler1(arg):
        print "handler1 called with", arg

    # callback usage
    def handler2(arg):
        print "handler2 called with", arg
    ee.on("myotherevent", handler2)

    # emit
    ee.emit("myevent", "foo")
    # -> "handler1 called with foo"

    ee.emit("myotherevent", "bar")
    # -> "handler2 called with bar"


Source code and more info at https://github.com/riga/pymitter.

"""
)