# Sparrow-WiFi packaging.
#
# Builds an installable .deb with fpm from a staged tree. The payload is pure
# Python (only the distro Qt stack is arch-specific, and that comes in via
# package dependencies), so the package is architecture independent:
# Architecture: all.
#
# Usage:
#   make deb            # build the .deb into dist/
#   make VERSION=1.2.0 deb
#   make clean
#
# Requires: fpm (https://github.com/jordansissel/fpm).
#
# NOTE: .rpm support is deferred. Fedora does not package the PyQt5 QtChart
# binding (which the app hard-requires) and it has no pip wheel, so a clean
# Fedora rpm needs a source build of the binding. Tracked as a follow-up.

PKG         := sparrow-wifi
# Version is read from the app's single source of truth (sparrowversion.py).
# Override on the command line if needed: `make deb VERSION=x.y.z`.
VERSION     ?= $(shell awk -F'"' '/^__version__/{print $$2}' sparrowversion.py)
ITERATION   ?= 1
MAINTAINER  := UltronCORE <syndr@ultroncore.net>
URL         := https://github.com/syndr/sparrow-wifi
LICENSE     := GPL-3.0
DESCRIPTION := WiFi/Bluetooth spectral-awareness, spectrum analysis and GPS wardriving tool (PyQt5).

BUILD    := build
PKGROOT  := $(BUILD)/pkgroot
DIST     := dist

# --- payload: what ships under /usr/share/sparrow-wifi ---------------------
# Explicit list (a `sparrow*.py` glob would wrongly pull in sparrow-elastic.py).
APP_PY := \
	sparrow-wifi.py sparrowwifiagent.py sparrowbluetooth.py sparrowcommon.py \
	sparrowdialogs.py sparrowdrone.py sparrowgps.py sparrowhackrf.py \
	sparrowmap.py sparrowrpi.py sparrowtablewidgets.py sparrowtheme.py \
	sparrowversion.py wirelessengine.py telemetry.py __init__.py
APP_DATA := wifi_icon.png LICENSE
APP_DIRS := images plugins

APP_DST := $(PKGROOT)/usr/share/$(PKG)

# --- dependency list -------------------------------------------------------
# python3-dev + a compiler are kept as a safety net: the postinstall builds a
# venv and pip-installs dronekit -> pymavlink; that ships aarch64/amd64 wheels
# today, but the toolchain lets pip fall back to a source build if a wheel is
# ever missing.
DEB_DEPS := \
	python3 python3-venv python3-pip python3-dev build-essential \
	python3-pyqt5 python3-pyqt5.qtchart python3-pyqt5.qsci \
	python3-numpy python3-matplotlib python3-requests python3-dateutil \
	gpsd gpsd-clients pkexec libglib2.0-bin

DEB_DEPENDS := $(foreach d,$(DEB_DEPS),-d $(d))

# --- fpm invocation shared bits --------------------------------------------
FPM_COMMON := \
	-s dir -a all \
	-n $(PKG) -v $(VERSION) --iteration $(ITERATION) \
	--maintainer "$(MAINTAINER)" \
	--url "$(URL)" \
	--license "$(LICENSE)" \
	--description "$(DESCRIPTION)" \
	--after-install  "$(CURDIR)/packaging/postinst" \
	--after-remove   "$(CURDIR)/packaging/postrm" \
	-C $(PKGROOT) -p $(DIST)

.PHONY: all deb stage clean help check-fpm

help:
	@echo "Targets: deb, stage, clean   (override VERSION=x.y.z)"

all: deb

# --- assemble the install tree ---------------------------------------------
stage:
	@echo ">> staging $(PKG) $(VERSION) into $(PKGROOT)"
	rm -rf $(PKGROOT)
	mkdir -p $(APP_DST) \
	         $(PKGROOT)/usr/bin \
	         $(PKGROOT)/usr/share/applications \
	         $(PKGROOT)/usr/share/pixmaps
	# App code + data
	cp -p $(APP_PY) $(APP_DATA) $(APP_DST)/
	cp -rp $(APP_DIRS) $(APP_DST)/
	# Strip build cruft that may sit in the source tree
	find $(APP_DST) -name '__pycache__' -type d -prune -exec rm -rf {} +
	find $(APP_DST) -name '*.pyc' -delete
	# Launcher, desktop entry, icon
	install -m755 packaging/sparrow-wifi.launcher $(PKGROOT)/usr/bin/$(PKG)
	install -m644 packaging/sparrow-wifi.desktop  $(PKGROOT)/usr/share/applications/$(PKG).desktop
	install -m644 wifi_icon.png                   $(PKGROOT)/usr/share/pixmaps/$(PKG).png
	mkdir -p $(DIST)

# --- package builds --------------------------------------------------------
deb: check-fpm stage
	rm -f $(DIST)/$(PKG)_$(VERSION)-$(ITERATION)_all.deb
	fpm -t deb $(DEB_DEPENDS) $(FPM_COMMON) .
	@echo ">> built: $$(ls $(DIST)/*.deb)"

clean:
	rm -rf $(BUILD) $(DIST)

# --- tooling guards --------------------------------------------------------
check-fpm:
	@command -v fpm >/dev/null 2>&1 || { \
		echo "error: fpm not found. Install with: gem install fpm  (needs Ruby)"; exit 1; }
