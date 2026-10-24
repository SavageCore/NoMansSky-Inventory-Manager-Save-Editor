"""Linux packaging guards: scripts parse, metadata present, drivers expose names."""
import ast
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PACKAGING = os.path.join(ROOT, "packaging")
LINUX = os.path.join(PACKAGING, "linux")
FLATPAK = os.path.join(PACKAGING, "flatpak")


def _read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def test_build_linux_parses_and_dry_runs():
    path = os.path.join(PACKAGING, "build_linux.py")
    ast.parse(_read(path), filename=path)
    out = subprocess.run([sys.executable, path, "--dry-run"],
                         cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "PyInstaller" in out.stdout
    assert "linux-x86_64" in out.stdout


def test_linux_metadata_files_exist_and_parse():
    import xml.etree.ElementTree as ET
    for name in ("nms-sorter.desktop", "nms-sorter.svg", "metainfo.xml"):
        assert os.path.isfile(os.path.join(LINUX, name)), name
    ET.parse(os.path.join(LINUX, "metainfo.xml"))
    desktop = _read(os.path.join(LINUX, "nms-sorter.desktop"))
    assert "Exec=nms-sorter" in desktop
    assert "Icon=nms-sorter" in desktop


def test_icon_png_exists():
    assert os.path.isfile(os.path.join(LINUX, "nms-sorter.png"))


def test_flatpak_manifest_exists_and_parses():
    import yaml
    path = os.path.join(FLATPAK, "com.savagecore.NmsSorter.yml")
    assert os.path.isfile(path)
    with io.open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert data["app-id"] == "com.savagecore.NmsSorter"
    assert data["runtime-version"] == "24.08"


def test_build_scripts_parse():
    for name in ("build_deb.py", "build_rpm.py", "build_appimage.py",
                 "build_flatpak.py"):
        ast.parse(_read(os.path.join(PACKAGING, name)),
                  filename=os.path.join(PACKAGING, name))
