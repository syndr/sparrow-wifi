#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# sparrowtheme.py — light/dark UI theming for Sparrow-WiFi.
#
# Scope by design: this themes the application "chrome" (menus, dialogs,
# combos, labels, backgrounds, buttons) via a Fusion style + light/dark
# QPalette applied once to the QApplication. The network table and the
# 2.4/5 GHz charts keep their own dark styling and are intentionally NOT
# touched here.
#
# System-theme detection is deliberately layered so it survives the pkexec
# elevation used to run the scanner as root: the launcher (which runs as the
# invoking user, where the session bus is reachable) detects the scheme and
# passes it in via the SPARROW_SYSTEM_THEME env var. When the app is run
# un-elevated as the user, we can also query the XDG portal / gsettings
# directly.

import os
import subprocess

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleFactory


def detect_system_theme():
    # Returns 'dark' or 'light'. Tries, in order: the launcher-provided env
    # var (reliable under root), the XDG desktop portal, then gsettings.
    env = os.environ.get('SPARROW_SYSTEM_THEME', '').strip().lower()
    if env in ('dark', 'light'):
        return env

    # XDG desktop portal: org.freedesktop.appearance color-scheme
    #   0 = no preference, 1 = prefer dark, 2 = prefer light
    try:
        out = subprocess.run(
            ['gdbus', 'call', '--session',
             '--dest', 'org.freedesktop.portal.Desktop',
             '--object-path', '/org/freedesktop/portal/desktop',
             '--method', 'org.freedesktop.portal.Settings.Read',
             'org.freedesktop.appearance', 'color-scheme'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=2).stdout.decode('utf-8', 'ignore')
        if 'uint32 1' in out:
            return 'dark'
        if 'uint32 2' in out:
            return 'light'
    except Exception:
        pass

    # gsettings (GNOME): 'prefer-dark' / 'prefer-light' / 'default'
    try:
        out = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=2).stdout.decode('utf-8', 'ignore').lower()
        if 'dark' in out:
            return 'dark'
        if 'light' in out:
            return 'light'
    except Exception:
        pass

    return 'light'


def resolve_theme(pref):
    # Map a stored preference (auto/light/dark) to a concrete theme name.
    pref = (pref or 'auto').strip().lower()
    if pref in ('dark', 'light'):
        return pref
    return detect_system_theme()


def dark_palette():
    p = QPalette()
    p.setColor(QPalette.Window, QColor(53, 53, 53))
    p.setColor(QPalette.WindowText, Qt.white)
    p.setColor(QPalette.Base, QColor(35, 35, 35))
    p.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
    p.setColor(QPalette.ToolTipText, Qt.white)
    p.setColor(QPalette.Text, Qt.white)
    p.setColor(QPalette.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText, Qt.white)
    p.setColor(QPalette.BrightText, Qt.red)
    p.setColor(QPalette.Link, QColor(42, 130, 218))
    p.setColor(QPalette.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.HighlightedText, Qt.black)
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    return p


def light_palette():
    p = QPalette()
    p.setColor(QPalette.Window, QColor(239, 239, 239))
    p.setColor(QPalette.WindowText, Qt.black)
    p.setColor(QPalette.Base, Qt.white)
    p.setColor(QPalette.AlternateBase, QColor(247, 247, 247))
    p.setColor(QPalette.ToolTipBase, Qt.white)
    p.setColor(QPalette.ToolTipText, Qt.black)
    p.setColor(QPalette.Text, Qt.black)
    p.setColor(QPalette.Button, QColor(239, 239, 239))
    p.setColor(QPalette.ButtonText, Qt.black)
    p.setColor(QPalette.BrightText, Qt.red)
    p.setColor(QPalette.Link, QColor(0, 100, 200))
    p.setColor(QPalette.Highlight, QColor(48, 140, 198))
    p.setColor(QPalette.HighlightedText, Qt.white)
    return p


def status_bar_style(themeName):
    # The status bar carries an explicit stylesheet, so the palette alone won't
    # reach it; supply a matching one per theme.
    if themeName == 'dark':
        return ("QStatusBar{background:rgba(53,53,53,255);color:white;"
                "border: 1px solid rgba(42,130,218,255); border-radius: 1px;}")
    return ("QStatusBar{background:rgba(192,192,192,255);color:black;"
            "border: 1px solid blue; border-radius: 1px;}")


def apply_theme(app, themeName):
    # Apply a resolved theme ('dark' or 'light') to the whole application.
    # Fusion is used because it honors custom palettes consistently, unlike the
    # native platform styles which often ignore palette roles.
    app.setStyle(QStyleFactory.create('Fusion'))
    if themeName == 'dark':
        app.setPalette(dark_palette())
    else:
        app.setPalette(light_palette())
