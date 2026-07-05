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
import glob
import subprocess

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyleFactory


def qt5ct_available():
    # qt5ct governs Qt5 apps (this app is PyQt5); qt6ct only affects Qt6 apps.
    # Usable only if the Qt5 platformtheme plugin is installed AND the user has a
    # qt5ct config to apply. Honors XDG_CONFIG_HOME (the launcher points this at
    # the invoking user's config so it works under the pkexec root elevation).
    plugin = (glob.glob('/usr/lib/*/qt5/plugins/platformthemes/libqt5ct.so')
              + glob.glob('/usr/lib/qt5/plugins/platformthemes/libqt5ct.so')
              + glob.glob('/usr/lib64/qt5/plugins/platformthemes/libqt5ct.so'))
    if not plugin:
        return False
    cfgbase = os.environ.get('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
    return os.path.isfile(os.path.join(cfgbase, 'qt5ct', 'qt5ct.conf'))


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


def table_header_style():
    # The data tables are always dark (black body, white text) regardless of the
    # chrome theme, so their headers must be dark too. Forcing both background
    # AND text here keeps them readable even under a light or custom (qt5ct)
    # palette that would otherwise draw header text from its own foreground color.
    # QHeaderView{...} styles the header's own background, which shows in the
    # empty area below the last section (e.g. when a filter leaves only a few
    # rows); ::section styles the individual header cells.
    return ("QHeaderView{background-color: rgb(45,45,45);} "
            "QHeaderView::section{background-color: rgb(45,45,45);"
            "border: 1px solid rgb(85,85,85);color: white;} "
            "QHeaderView::down-arrow,QHeaderView::up-arrow {background: none;}")


def apply_data_table(table):
    # Style a data table (body + headers) for the active theme.
    #
    # Under qt5ct we paint the table explicitly from the qt5ct *chrome* colors
    # (Window/WindowText, the same roles the menus use) rather than clearing the
    # stylesheet. Clearing would let the widget style draw the item view, and
    # some styles (e.g. Kvantum) paint item-view backgrounds from their own theme
    # / the Base role — which can be light even when the chrome is dark, leaving
    # the table white. Using the chrome colors keeps the table matching the rest
    # of the UI whatever the style does.
    #
    # Otherwise (Fusion light/dark or the detected fallback) we force the classic
    # dark table: the per-row SSID and chart-series colors are tuned for a dark
    # background, so we keep the body dark even in "light" mode.
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if bool(app.property('sparrowUsingQt5ct')):
        pal = app.palette()
        win = pal.color(QPalette.Window).name()
        winText = pal.color(QPalette.WindowText).name()
        btn = pal.color(QPalette.Button).name()
        btnText = pal.color(QPalette.ButtonText).name()
        grid = "rgba(128,128,128,90)"   # subtle, readable on light or dark
        table.setStyleSheet("QTableView {background-color: %s;color: %s;gridline-color: %s;} "
                            "QTableCornerButton::section{background-color: %s;}"
                            % (win, winText, grid, btn))
        hs = ("QHeaderView{background-color: %s;} "
              "QHeaderView::section{background-color: %s;color: %s;border: 1px solid %s;} "
              "QHeaderView::down-arrow,QHeaderView::up-arrow {background: none;}"
              % (btn, btn, btnText, grid))
        table.horizontalHeader().setStyleSheet(hs)
        table.verticalHeader().setStyleSheet(hs)
    else:
        table.setStyleSheet("QTableView {background-color: black;gridline-color: white;"
                            "color: white} QTableCornerButton::section{background-color: rgb(45,45,45);}")
        hs = table_header_style()
        table.horizontalHeader().setStyleSheet(hs)
        table.verticalHeader().setStyleSheet(hs)


def apply_theme(app, themeName):
    # Apply a resolved theme ('dark' or 'light') to the whole application.
    # Fusion is used because it honors custom palettes consistently, unlike the
    # native platform styles which often ignore palette roles.
    app.setStyle(QStyleFactory.create('Fusion'))
    if themeName == 'dark':
        app.setPalette(dark_palette())
    else:
        app.setPalette(light_palette())
