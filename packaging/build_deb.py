#!/usr/bin/env python3
"""Build a .deb package from the Linux binary.

    python packaging/build_deb.py

Expects `dist/NMS-Sorter` to exist (run `packaging/build_linux.py` first).
Produces `dist/nms-sorter_<version>_amd64.deb`.
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


def main():
    if not os.path.isfile(BINARY):
        print("missing %s; run packaging/build_linux.py first" % BINARY)
        return 2
    if shutil.which("dpkg-deb") is None:
        print("dpkg-deb not found")
        return 2

    v = version()
    stage = os.path.join(DIST, "deb-stage")
    if os.path.exists(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)

    # Layout
    usr_bin = os.path.join(stage, "usr", "bin")
    os.makedirs(usr_bin)
    shutil.copy2(BINARY, os.path.join(usr_bin, "nms-sorter"))
    os.chmod(os.path.join(usr_bin, "nms-sorter"), 0o755)

    # console alias (same binary on Linux)
    console_src = os.path.join(DIST, "NMS-Sorter-console")
    if os.path.isfile(console_src):
        shutil.copy2(console_src, os.path.join(usr_bin, "nms-sorter-console"))
        os.chmod(os.path.join(usr_bin, "nms-sorter-console"), 0o755)

    apps = os.path.join(stage, "usr", "share", "applications")
    os.makedirs(apps)
    shutil.copy2(os.path.join(META, "nms-sorter.desktop"),
                 os.path.join(apps, "nms-sorter.desktop"))

    icons = os.path.join(stage, "usr", "share", "icons", "hicolor", "scalable", "apps")
    os.makedirs(icons)
    shutil.copy2(os.path.join(META, "nms-sorter.svg"),
                 os.path.join(icons, "nms-sorter.svg"))
    icons256 = os.path.join(stage, "usr", "share", "icons", "hicolor", "256x256", "apps")
    os.makedirs(icons256)
    shutil.copy2(os.path.join(META, "nms-sorter.png"),
                 os.path.join(icons256, "nms-sorter.png"))

    doc = os.path.join(stage, "usr", "share", "doc", "nms-sorter")
    os.makedirs(doc)
    for name in ("README.md", "LICENSE"):
        src = os.path.join(ROOT, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(doc, name))

    meta = os.path.join(stage, "DEBIAN")
    os.makedirs(meta)
    control = """Package: nms-sorter
Version: %s
Section: games
Priority: optional
Architecture: amd64
Maintainer: SavageCore <talk@savagecore.uk>
Description: No Man's Sky inventory sorter and save editor
 A local, offline inventory sorter and save editor for No Man's Sky.
 Moves only what you own: no spawning, no stat or unit editing.
""" % v
    with open(os.path.join(meta, "control"), "w", encoding="utf-8") as fh:
        fh.write(control)

    out = os.path.join(DIST, "nms-sorter_%s_amd64.deb" % v)
    if os.path.exists(out):
        os.remove(out)
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", stage, out],
                   check=True)
    print("built %s" % out)
    shutil.rmtree(stage, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
