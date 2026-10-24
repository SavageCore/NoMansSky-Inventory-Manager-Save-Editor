#!/usr/bin/env python3
"""Build the two Linux executables, `SHA256SUMS` and the release tarball.

    python packaging/build_linux.py
    python packaging/build_linux.py --dry-run      # print the command, build nothing

Produces, in `dist/`:

    NMS-Sorter            the double-click one; no console window (on Linux this
                          is the same binary with stdout attached to the terminal)
    NMS-Sorter-console    the same program with a console, for diagnostics
    SHA256SUMS            `sha256sum -c` format, one line per file
    NMS-Sorter-<v>-linux-x86_64.tar.gz   those two, flat, plus the four documents
    NMS-Sorter-<v>-linux-x86_64.tar.gz.sha256   that tarball's own hash

Mirrors `build_exe.py`: PyInstaller is run from `packaging/NMS-Sorter.spec`,
which is platform-aware (no `runtime_tmpdir` off Windows). There is no
cross-compilation; the release is built on Linux.
"""
import argparse
import glob
import hashlib
import io
import os
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPEC = os.path.join(HERE, "NMS-Sorter.spec")
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "build")
SUMS = os.path.join(DIST, "SHA256SUMS")

EXPECTED = ("NMS-Sorter", "NMS-Sorter-console")

ZIP_DOCS = ("README.md", "docs/GUIDE.md", "docs/RULES.md",
            "docs/TROUBLESHOOTING.md")

PLATFORM_TAG = "linux-x86_64"

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

_LINK = None
import re
_LINK = re.compile(r"(!?)\[([^\]]*)\]\(\s*([^)\s]+?)\s*\)")
_ABSOLUTE = ("http://", "https://", "mailto:", "#", "<")


def command(spec=SPEC, dist=DIST, work=WORK):
    return [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
            "--distpath", dist, "--workpath", work, spec]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sums(dist=DIST, out=SUMS):
    rows = []
    for name in sorted(os.listdir(dist)):
        path = os.path.join(dist, name)
        if not os.path.isfile(path) or os.path.abspath(path) == os.path.abspath(out):
            continue
        rows.append((name, sha256(path), os.path.getsize(path)))
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for name, digest, _size in rows:
            fh.write("%s *%s\n" % (digest, name))
    return rows


def version(root=ROOT):
    if root not in sys.path:
        sys.path.insert(0, root)
    import nms_sorter
    return nms_sorter.__version__


def archive_name(ver=None):
    return "NMS-Sorter-%s-%s.tar.gz" % (ver or version(), PLATFORM_TAG)


def rewrite_for_archive(text, names):
    def one(m):
        bang, label, target = m.group(1), m.group(2), m.group(3)
        if bang or target.lower().endswith(IMAGE_SUFFIXES):
            return ""
        if target.startswith(_ABSOLUTE):
            return m.group(0)
        label = label.replace("docs/", "")
        bare = os.path.basename(target.split("#")[0])
        if bare in names and target.split("#")[0] in (bare, "docs/" + bare):
            anchor = ("#" + target.split("#", 1)[1]) if "#" in target else ""
            return "[%s](%s%s)" % (label, bare, anchor)
        return label
    out = _LINK.sub(one, text)
    out = re.sub(r"\n[ \t]*\n([ \t]*\n)+", "\n\n", out)
    return out


def write_archive(dist=DIST, root=ROOT, ver=None):
    path = os.path.join(dist, archive_name(ver))
    missing = [n for n in EXPECTED + ("SHA256SUMS",)
               if not os.path.isfile(os.path.join(dist, n))]
    if missing:
        raise IOError("not in %s: %s" % (dist, ", ".join(missing)))
    names = EXPECTED + ("SHA256SUMS",) + tuple(
        os.path.basename(p) for p in ZIP_DOCS)
    with tarfile.open(path, "w:gz") as tf:
        for name in EXPECTED + ("SHA256SUMS",):
            tf.add(os.path.join(dist, name), arcname=name)
        for rel in ZIP_DOCS:
            src = os.path.join(root, rel.replace("/", os.sep))
            with io.open(src, encoding="utf-8") as fh:
                body = rewrite_for_archive(fh.read(), names)
            data = body.replace("\r\n", "\n").encode("utf-8")
            info = tarfile.TarInfo(name=os.path.basename(rel))
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return path


def write_archive_hash(archive_path):
    digest = sha256(archive_path)
    out = archive_path + ".sha256"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%s *%s\n" % (digest, os.path.basename(archive_path)))
    return out, digest


def clear_previous_archives(dist=DIST):
    gone = []
    for pattern in ("NMS-Sorter-*-%s.tar.gz" % PLATFORM_TAG,
                    "NMS-Sorter-*-%s.tar.gz.sha256" % PLATFORM_TAG):
        for path in sorted(glob.glob(os.path.join(dist, pattern))):
            os.remove(path)
            gone.append(os.path.basename(path))
    return gone


def main(argv=None):
    ap = argparse.ArgumentParser(prog="build_linux",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the PyInstaller command and exit")
    args = ap.parse_args(argv)

    cmd = command()
    print(" ".join(cmd))
    print("archive: %s" % archive_name())
    if args.dry_run:
        return 0

    if not os.path.isfile(SPEC):
        print("no spec file at %s" % SPEC)
        return 2
    started = time.time()
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        print("PyInstaller failed with %d" % proc.returncode)
        return proc.returncode
    took = time.time() - started

    missing = [n for n in EXPECTED if not os.path.isfile(os.path.join(DIST, n))]
    if missing:
        print("built, but these are not in dist/: %s" % ", ".join(missing))
        return 1

    for name in clear_previous_archives():
        print("removed a previous %s" % name)
    rows = write_sums()
    archive = write_archive()
    hash_path, archive_digest = write_archive_hash(archive)

    print("")
    print("built in %.0f s" % took)
    for name, digest, size in rows:
        print("  %-26s %8.1f MB  %s" % (name, size / 1048576.0, digest[:16]))
    print("  %-26s %s" % ("SHA256SUMS", SUMS))
    print("  %-26s %8.1f MB  %s" % (os.path.basename(archive),
                                    os.path.getsize(archive) / 1048576.0,
                                    archive_digest[:16]))
    print("  %-26s %s" % (os.path.basename(hash_path), hash_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
