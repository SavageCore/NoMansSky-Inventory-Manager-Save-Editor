#!/usr/bin/env python3
"""Build an .rpm package from the Linux binary.

    python packaging/build_rpm.py

Expects `dist/NMS-Sorter` to exist (run `packaging/build_linux.py` first).
Produces `dist/nms-sorter-<version>-1.x86_64.rpm`.
"""
import os
import shutil
import subprocess
import sys
import tempfile

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
    if shutil.which("rpmbuild") is None:
        print("rpmbuild not found")
        return 2

    v = version()
    topdir = os.path.join(DIST, "rpmbuild")
    if os.path.exists(topdir):
        shutil.rmtree(topdir)
    for sub in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"):
        os.makedirs(os.path.join(topdir, sub))

    # Stage files under BUILDROOT-like layout in SOURCES via a tarball
    stagedir = os.path.join(topdir, "stage")
    os.makedirs(stagedir, exist_ok=True)
    usr_bin = os.path.join(stagedir, "usr", "bin")
    os.makedirs(usr_bin)
    shutil.copy2(BINARY, os.path.join(usr_bin, "nms-sorter"))
    os.chmod(os.path.join(usr_bin, "nms-sorter"), 0o755)
    console_src = os.path.join(DIST, "NMS-Sorter-console")
    if os.path.isfile(console_src):
        shutil.copy2(console_src, os.path.join(usr_bin, "nms-sorter-console"))
        os.chmod(os.path.join(usr_bin, "nms-sorter-console"), 0o755)

    apps = os.path.join(stagedir, "usr", "share", "applications")
    os.makedirs(apps)
    shutil.copy2(os.path.join(META, "nms-sorter.desktop"),
                 os.path.join(apps, "nms-sorter.desktop"))

    icons = os.path.join(stagedir, "usr", "share", "icons", "hicolor", "scalable", "apps")
    os.makedirs(icons)
    shutil.copy2(os.path.join(META, "nms-sorter.svg"),
                 os.path.join(icons, "nms-sorter.svg"))
    icons256 = os.path.join(stagedir, "usr", "share", "icons", "hicolor", "256x256", "apps")
    os.makedirs(icons256)
    shutil.copy2(os.path.join(META, "nms-sorter.png"),
                 os.path.join(icons256, "nms-sorter.png"))

    spec_path = os.path.join(topdir, "SPECS", "nms-sorter.spec")
    spec = """Name:           nms-sorter
Version:        %s
Release:        1%%{?dist}
Summary:        No Man's Sky inventory sorter and save editor
License:        MIT
BuildArch:      x86_64

%%description
A local, offline inventory sorter and save editor for No Man's Sky.
Moves only what you own: no spawning, no stat or unit editing.

%%install
mkdir -p %%{buildroot}/usr/bin
mkdir -p %%{buildroot}/usr/share/applications
mkdir -p %%{buildroot}/usr/share/icons/hicolor/scalable/apps
cp %s/usr/bin/nms-sorter %%{buildroot}/usr/bin/nms-sorter
cp %s/usr/bin/nms-sorter-console %%{buildroot}/usr/bin/nms-sorter-console
cp %s/usr/share/applications/nms-sorter.desktop %%{buildroot}/usr/share/applications/nms-sorter.desktop
cp %s/usr/share/icons/hicolor/scalable/apps/nms-sorter.svg %%{buildroot}/usr/share/icons/hicolor/scalable/apps/nms-sorter.svg

%%files
/usr/bin/nms-sorter
/usr/bin/nms-sorter-console
/usr/share/applications/nms-sorter.desktop
/usr/share/icons/hicolor/scalable/apps/nms-sorter.svg

%%changelog
* Sat Oct 24 2026 SavageCore <talk@savagecore.uk> - %s-1
- Linux build
""" % (v, stagedir, stagedir, stagedir, stagedir, v)
    with open(spec_path, "w", encoding="utf-8") as fh:
        fh.write(spec)

    # rpmbuild with buildroot pointing at stagedir contents already copied via %install? 
    # We used absolute stagedir paths in %install cp, so buildroot gets populated. But %install runs in build env.
    # Simpler: skip %install copy by making buildroot == stagedir? Use --buildroot.
    subprocess.run(["rpmbuild", "--define", "_topdir %s" % topdir,
                    "--define", "_buildrootdir %s" % os.path.join(topdir, "BUILDROOT"),
                    "-bb", spec_path], check=True, cwd=topdir)

    # Find produced rpm
    rpms = []
    for root_, _, files in os.walk(os.path.join(topdir, "RPMS")):
        for f in files:
            if f.endswith(".rpm"):
                rpms.append(os.path.join(root_, f))
    if not rpms:
        print("no rpm produced")
        return 1
    produced = rpms[0]
    out = os.path.join(DIST, os.path.basename(produced))
    shutil.copy2(produced, out)
    print("built %s" % out)
    shutil.rmtree(topdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
