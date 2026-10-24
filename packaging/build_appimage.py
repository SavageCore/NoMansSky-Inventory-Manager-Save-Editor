#!/usr/bin/env python3
"""Build an AppImage from the Linux binary.

    python packaging/build_appimage.py

Expects `dist/NMS-Sorter` to exist (run `packaging/build_linux.py` first).
Produces `dist/NMS-Sorter-<version>-x86_64.AppImage`.

Requires `appimagetool` on PATH (or APPIMAGETOOL env var pointing at it).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
META = os.path.join(HERE, "linux")
BINARY = os.path.join(DIST, "NMS-Sorter")


def version():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import nms_sorter
    return nms_sorter.__version__


def find_appimagetool():
    tool = os.environ.get("APPIMAGETOOL")
    if tool and os.path.isfile(tool):
        return tool
    return shutil.which("appimagetool")


def main():
    if not os.path.isfile(BINARY):
        print("missing %s; run packaging/build_linux.py first" % BINARY)
        return 2
    tool = find_appimagetool()
    if tool is None:
        print("appimagetool not found; set APPIMAGETOOL or install it")
        return 2

    v = version()
    appdir = os.path.join(DIST, "AppDir")
    if os.path.exists(appdir):
        shutil.rmtree(appdir)
    os.makedirs(appdir)

    # AppRun -> binary
    shutil.copy2(BINARY, os.path.join(appdir, "AppRun"))
    os.chmod(os.path.join(appdir, "AppRun"), 0o755)

    # .desktop and icon at root (appimagetool convention)
    shutil.copy2(os.path.join(META, "nms-sorter.desktop"),
                 os.path.join(appdir, "nms-sorter.desktop"))
    shutil.copy2(os.path.join(META, "nms-sorter.svg"),
                 os.path.join(appdir, "nms-sorter.svg"))

    # also under usr for convention
    for sub in ("usr/bin", "usr/share/applications", "usr/share/icons/hicolor/scalable/apps"):
        os.makedirs(os.path.join(appdir, sub), exist_ok=True)
    shutil.copy2(BINARY, os.path.join(appdir, "usr", "bin", "nms-sorter"))
    os.chmod(os.path.join(appdir, "usr", "bin", "nms-sorter"), 0o755)
    shutil.copy2(os.path.join(META, "nms-sorter.desktop"),
                 os.path.join(appdir, "usr", "share", "applications", "nms-sorter.desktop"))
    shutil.copy2(os.path.join(META, "nms-sorter.svg"),
                 os.path.join(appdir, "usr", "share", "icons", "hicolor", "scalable", "apps", "nms-sorter.svg"))

    out = os.path.join(DIST, "NMS-Sorter-%s-x86_64.AppImage" % v)
    if os.path.exists(out):
        os.remove(out)

    env = dict(os.environ)
    env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
    subprocess.run([tool, appdir, out], check=True, env=env)
    print("built %s" % out)
    shutil.rmtree(appdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
