#!/usr/bin/env python3
# sparrowversion.py — single source of truth for the Sparrow-WiFi version.
#
# This is the ONE place the version is defined. It is surfaced in the GUI
# (window title + About dialog) and read by the packaging Makefile so the
# built .deb version tracks the code automatically. Bump this, then tag the
# release `v<this value>` (e.g. v2.1.0) — CI verifies the tag matches.

__version__ = "2.1.1"
