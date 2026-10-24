#!/usr/bin/env python3
"""Build a Flatpak bundle from the source tree.

    python packaging/build_flatpak.py

Produces `dist/com.savagecore.NmsSorter.flatpak`. Requires `flatpak-builder`
and the org.freedesktop.Sdk/Platform 24.08 runtime.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
MANIFEST = os.path.join(HERE, "flatpak", "com.savagecore.NmsSorter.yml")


def version():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import nms_sorter
    return nms_sorter.__version__


def main():
    if shutil.which("flatpak-builder") is None:
        print("flatpak-builder not found")
        return 2
    if not os.path.isfile(MANIFEST):
        print("missing manifest %s" % MANIFEST)
        return 2

    v = version()
    workdir = os.path.join(DIST, "flatpak-build")
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)

    repo = os.path.join(DIST, "flatpak-repo")
    if os.path.exists(repo):
        shutil.rmtree(repo)

    subprocess.run([
        "flatpak-builder", "--force-clean", "--repo", repo,
        os.path.join(workdir, "build"), MANIFEST,
    ], check=True, cwd=ROOT)

    bundle = os.path.join(DIST, "com.savagecore.NmsSorter.flatpak")
    if os.path.exists(bundle):
        os.remove(bundle)
    subprocess.run([
        "flatpak", "build-bundle", repo, bundle, "com.savagecore.NmsSorter",
    ], check=True)
    print("built %s" % bundle)
    shutil.rmtree(workdir, ignore_errors=True)
    shutil.rmtree(repo, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
