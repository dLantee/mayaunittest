"""
Plain pytest tests for the Maya-independent helper functions in python/cli.py.

Kept separate from tests/ (which is scanned by mayaunittest's own Maya-based
test discovery) since these run with plain pytest and never need a real
Maya/mayapy installation.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

import cli


# ----------------------------
# _normalize_os_key
# ----------------------------

@pytest.mark.parametrize("system_name,expected", [
    ("Windows", "windows"),
    ("Darwin", "darwin"),
    ("Linux", "linux"),
    ("SunOS", "linux"),
])
def test_normalize_os_key(monkeypatch, system_name, expected):
    monkeypatch.setattr(cli.platform, "system", lambda: system_name)
    assert cli._normalize_os_key() == expected


# ----------------------------
# default_maya_location
# ----------------------------

def test_default_maya_location_windows():
    assert cli.default_maya_location("windows", 2026) == "C:/Program Files/Autodesk/Maya2026"


def test_default_maya_location_darwin():
    assert cli.default_maya_location("darwin", 2026) == \
        "/Applications/Autodesk/maya2026/Maya.app/Contents"


def test_default_maya_location_linux():
    assert cli.default_maya_location("linux", 2022) == "/usr/autodesk/maya2022"


def test_default_maya_location_linux_pre_2016_uses_x64_suffix():
    assert cli.default_maya_location("linux", 2015) == "/usr/autodesk/maya2015-x64"


# ----------------------------
# load_maya_install_map
# ----------------------------

def test_load_maya_install_map_no_path_returns_empty_dict():
    assert cli.load_maya_install_map(None) == {}


def test_load_maya_install_map_missing_file_returns_empty_dict(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.json"
    assert cli.load_maya_install_map(str(missing)) == {}
    assert "not found" in capsys.readouterr().out


def test_load_maya_install_map_reads_json(tmp_path):
    data = {"windows": {"2026": "C:/Maya2026"}}
    p = tmp_path / "custom_installs.json"
    p.write_text(json.dumps(data))
    assert cli.load_maya_install_map(str(p)) == data


# ----------------------------
# resolve_maya_location
# ----------------------------

def test_resolve_maya_location_maya_path_wins_over_everything(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_normalize_os_key", lambda: "windows")
    monkeypatch.setenv("MAYA_LOCATION", "C:/env/location")
    result = cli.resolve_maya_location(2026, "C:/explicit/path", str(tmp_path / "missing.json"))
    assert result == "C:/explicit/path"


def test_resolve_maya_location_uses_installs_json(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_normalize_os_key", lambda: "windows")
    installs = tmp_path / "custom_installs.json"
    installs.write_text(json.dumps({"windows": {"2024": "C:/from/json"}}))
    monkeypatch.delenv("MAYA_LOCATION", raising=False)
    result = cli.resolve_maya_location(2024, None, str(installs))
    assert result == "C:/from/json"


def test_resolve_maya_location_falls_back_to_env(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_normalize_os_key", lambda: "windows")
    monkeypatch.setenv("MAYA_LOCATION", "C:/env/location")
    missing = tmp_path / "missing.json"
    result = cli.resolve_maya_location(2024, None, str(missing))
    assert result == "C:/env/location"


def test_resolve_maya_location_falls_back_to_default(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_normalize_os_key", lambda: "windows")
    monkeypatch.delenv("MAYA_LOCATION", raising=False)
    missing = tmp_path / "missing.json"
    result = cli.resolve_maya_location(2026, None, str(missing))
    assert result == "C:/Program Files/Autodesk/Maya2026"


# ----------------------------
# mayapy_exe_from_location
# ----------------------------

def test_mayapy_exe_from_location_windows(monkeypatch):
    monkeypatch.setattr(cli.platform, "system", lambda: "Windows")
    assert cli.mayapy_exe_from_location("C:/Maya2026") == \
        os.path.join("C:/Maya2026", "bin", "mayapy") + ".exe"


def test_mayapy_exe_from_location_non_windows(monkeypatch):
    monkeypatch.setattr(cli.platform, "system", lambda: "Linux")
    assert cli.mayapy_exe_from_location("/usr/autodesk/maya2026") == \
        os.path.join("/usr/autodesk/maya2026", "bin", "mayapy")


# ----------------------------
# is_running_in_mayapy
# ----------------------------

def test_is_running_in_mayapy_true_when_executable_named_mayapy(monkeypatch):
    monkeypatch.setattr(cli.sys, "executable", "/usr/autodesk/maya2026/bin/mayapy")
    assert cli.is_running_in_mayapy() is True


# ----------------------------
# package_from_root
# ----------------------------

def test_package_from_root_missing_root_raises(tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(RuntimeError, match="does not exist"):
        cli.package_from_root(str(missing))


def test_package_from_root_missing_tests_dir_raises(tmp_path):
    with pytest.raises(RuntimeError, match="Missing tests/"):
        cli.package_from_root(str(tmp_path))


def test_package_from_root_without_python_dir(tmp_path):
    (tmp_path / "tests").mkdir()
    pkg = cli.package_from_root(str(tmp_path))
    assert pkg["name"] == tmp_path.name
    assert pkg["tests_dir"] == str(tmp_path / "tests")
    assert pkg["python_dir"] is None


def test_package_from_root_with_python_dir(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "python").mkdir()
    pkg = cli.package_from_root(str(tmp_path))
    assert pkg["python_dir"] == str(tmp_path / "python")


# ----------------------------
# _join_paths
# ----------------------------

def test_join_paths():
    assert cli._join_paths(["a", "b", "c"]) == os.pathsep.join(["a", "b", "c"])
