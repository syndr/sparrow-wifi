# Packaging

Builds an installable **`.deb`** package for Sparrow-WiFi with
[`fpm`](https://github.com/jordansissel/fpm) from a staged tree, driven by the
top-level `Makefile`. CI in `.github/workflows/package.yml` builds it,
install-tests it on amd64 **and** arm64, and publishes it to a GitHub Release on
version tags.

> **`.rpm` is deferred** — see [RPM (deferred)](#rpm-deferred) below.

## What the package installs

| Path | Contents |
|------|----------|
| `/usr/share/sparrow-wifi/` | the app tree (curated — see `Makefile` `APP_*` lists) |
| `/usr/bin/sparrow-wifi` | launcher: `pkexec`-elevates to root, forwards the display, cd's to the writable state dir |
| `/usr/share/applications/sparrow-wifi.desktop` | menu entry |
| `/usr/share/pixmaps/sparrow-wifi.png` | icon |
| `/var/lib/sparrow-wifi/venv/` | dedicated venv, built by the post-install |
| `/var/lib/sparrow-wifi/` | writable working dir (OUI db + `sparrowwifiagent.cfg`) |

### Dependency model

The Qt/numpy stack is pulled from **distro packages** (declared as package
dependencies — see `DEB_DEPS` in the `Makefile`). The three deps that aren't in
the distro — `gps3`, `dronekit`, `manuf` — are installed by the **post-install**
into the venv (`--system-site-packages`, so it reuses the distro Qt). `dronekit`
pulls `pymavlink`; it ships prebuilt aarch64/amd64 wheels today, but a compiler +
Python headers are kept as deps so pip can fall back to a source build, and
**network access is required at install time**.

The package payload is pure Python, so the package is architecture independent
(`Architecture: all`); the only arch-specific pieces are the distro Qt bindings
resolved by the package manager on the target host.

## Building locally

Requires `fpm` (`gem install fpm`, needs Ruby).

```sh
make deb                 # version read from sparrowversion.py -> dist/sparrow-wifi_2.1.0-1_all.deb
make VERSION=9.9.9 deb   # override the version if you must
make clean
```

The package version comes from **`sparrowversion.py`** (`__version__`) — the same
value the app shows in its window title and About dialog. Bump that one line to
change the version everywhere.

Inspect the result:

```sh
dpkg-deb -c dist/*.deb   # file list
dpkg-deb -I dist/*.deb   # metadata + Depends
```

Install / remove (Debian/Ubuntu):

```sh
sudo apt-get install -y ./dist/*.deb
sudo apt-get purge   -y sparrow-wifi     # also wipes /var/lib/sparrow-wifi
```

## Releasing

1. Bump `__version__` in `sparrowversion.py`.
2. Push a matching tag: `v<version>` (e.g. `v2.1.0`).

CI reads the version from `sparrowversion.py`, **fails if the tag doesn't match**
(`vX.Y.Z` must equal `v$__version__`), builds the `.deb`, runs the dual-arch
install tests, and attaches it to a GitHub Release.

## RPM (deferred)

`fpm` can emit an `.rpm` from the same staged tree in one extra invocation, but a
package that actually **installs cleanly on Fedora** is not that simple:

- The app hard-imports `PyQt5.QtChart` (`sparrow-wifi.py`, `telemetry.py`).
- Fedora ships `python3-qt5` (QtWidgets), `python3-qscintilla-qt5` (Qsci), and
  the C++ `qt5-qtcharts` library — but **no PyQt5 QtChart Python binding** (only
  the PyQt6 one, `python3-pyqt6-charts`).
- `pip install PyQtChart` has no wheel for Fedora's Python and falls back to a
  source build needing a full Qt/sip toolchain.

So a Fedora rpm needs either a source build of just the QtChart binding (against
`qt5-qtcharts-devel` + PyQt5), the app ported to PyQt6, or the QtChart import made
optional. Tracked as a follow-up. Other rpm distros (e.g. openSUSE, which
packages the PyQt5 charts binding) may work with only a dependency-name change.

## Not using a package?

`scripts/install.sh` remains the from-checkout install path (venv + apt deps +
pkexec launcher, with an `--update` mode). The package simply wraps the same
approach into a proper `.deb` artifact.
