from __future__ import annotations

__all__: list[str] = []

import os
import sys

# adjust the path to import pymitter
base = os.path.normpath(os.path.join(os.path.abspath(__file__), "../.."))
sys.path.append(base)

from pymitter import *  # noqa: E402, F403, I001
from .test_all import *  # noqa: E402, F403, I001
