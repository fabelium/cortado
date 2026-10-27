#!/usr/bin/env python3
"""Thin entry-point shim. The real CLI lives in ``coffee.cli``."""

from coffee.cli import main

raise SystemExit(main())
