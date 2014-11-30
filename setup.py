# -*- coding: utf-8 -*-

# python imports
from distutils.core import setup


setup(
    name         = "pymitter",
    version      = "0.1.0",
    packages     = ["pymitter"],
    description  = "Python port of the extended Node.js EventEmitter2 approach.",
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
    ]
)