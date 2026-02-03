"""
Run Maya unit tests for one or more packages across Maya 2022 / 2024 / 2026.

- Safe to launch from system Python 3.7 (it spawns the requested mayapy).
- Runs tests inside mayapy using mayaunittest.run_tests_from_commandline().

Layout assumption per package root:
    <pkg_root>/
        python/      (optional)
        tests/       (required)
        tests/clean_maya_app_dir/ (optional template for clean prefs)

Examples:
    py run_maya_tests.py --maya 2022 --packages D:\projects\pkgA D:\projects\pkgB --pause
    py run_maya_tests.py --maya 2026 --packages D:\projects\pkgA --clean-maya-app-dir
"""

import argparse
import errno
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import time
import json


DEFAULT_MAYA_VERSION = 2022


# ----------------------------
# Filesystem helpers
# ----------------------------

def _remove_read_only(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise


def _join_paths(paths):
    return os.pathsep.join([str(p) for p in paths])


def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


# ----------------------------
# Maya discovery
# ----------------------------

def _normalize_os_key():
    sysname = platform.system().lower()
    if "windows" in sysname:
        return "windows"
    if "darwin" in sysname or "mac" in sysname:
        return "darwin"
    return "linux"


def load_maya_install_map(json_path):
    """
    Load JSON mapping:
      { "windows": { "2022": "...", ... }, "linux": {...}, "darwin": {...} }
    Returns dict or {} if not found.
    """
    if not json_path:
        return {}
    if not os.path.exists(json_path):
        print("Maya install map not found at: {0}".format(json_path))
        return {}
    with open(json_path, "r") as f:
        return json.load(f) or {}


def default_maya_location(os_key, maya_version):
    if os_key == "windows":
        return "C:/Program Files/Autodesk/Maya{0}".format(maya_version)
    if os_key == "darwin":
        return "/Applications/Autodesk/maya{0}/Maya.app/Contents".format(maya_version)
    location = "/usr/autodesk/maya{0}".format(maya_version)
    if maya_version < 2016:
        location += "-x64"
    return location


def resolve_maya_location(maya_version, maya_path, installs_path):
    """
    Priority:
      1) --maya-path (explicit)
      2) --maya version -> JSON lookup (default paths if JSON not exists)
      3) MAYA_LOCATION env (if not maya-path nor maya version passed)
      4) optional old default fallback (kept for convenience)
    """
    # 1) explicit
    if maya_path:
        return maya_path

    # 2) JSON lookup by --maya
    installs = load_maya_install_map(installs_path)
    os_key = _normalize_os_key()
    ver_key = str(maya_version) if maya_version else DEFAULT_MAYA_VERSION
    if ver_key and isinstance(installs, dict):
        os_map = installs.get(os_key, {})
        if isinstance(os_map, dict):
            loc = os_map.get(ver_key)
            if loc:
                return loc

    # 3) environment fallback (lowest priority if --maya is given)
    env = os.environ.get("MAYA_LOCATION")
    if env:
        return env

    # 4) optional old default fallback (kept for convenience)
    return default_maya_location(os_key, maya_version)


def mayapy_exe_from_location(maya_location):
    exe = os.path.join(maya_location, "bin", "mayapy")
    if platform.system() == "Windows":
        exe += ".exe"
    return exe


def is_running_in_mayapy():
    exe = os.path.basename(sys.executable).lower()
    if "mayapy" in exe:
        return True
    try:
        import maya  # noqa: F401
        return True
    except Exception:
        return False


# ----------------------------
# Package model
# ----------------------------

def package_from_root(root_path):
    """Create a package dict from its root path."""
    root = os.path.abspath(root_path)
    if not os.path.exists(root):
        raise RuntimeError("Package root does not exist: {0}".format(root))

    tests_dir = os.path.join(root, "tests")
    if not os.path.exists(tests_dir):
        raise RuntimeError("Missing tests/ in package root: {0}".format(tests_dir))

    python_dir = os.path.join(root, "python")
    if not os.path.exists(python_dir):
        python_dir = None

    return {
        "root": root,
        "name": os.path.basename(root),
        "tests_dir": tests_dir,
        "python_dir": python_dir,
    }


# ----------------------------
# Clean MAYA_APP_DIR
# ----------------------------

def get_clean_maya_app_dir(app_dir=None):
    """Create a clean MAYA_APP_DIR in a temp folder."""
    if app_dir:
        if os.path.exists(app_dir):
            # Using existing dir
            return app_dir

    # if app_dir not specified or app_dir does not exist, create a temp one
    app_dir = os.path.join(tempfile.gettempdir(), "maya_app_dir_{0}".format(uuid.uuid4()))
    os.makedirs(app_dir)
    print("Temp dir created for MAYA_APP_DIR: {0}".format(app_dir))
    return app_dir


def _rmtree_with_retries(path, tries=12, delay_sec=0.25):
    """
    Windows: mayapy/maya can keep files (mayaLog) open briefly.
    Retry delete a few times before giving up.
    """
    if not path or not os.path.exists(path):
        return

    last_err = None
    for _ in range(tries):
        try:
            shutil.rmtree(path, onerror=_remove_read_only)
            return
        except PermissionError as e:
            last_err = e
            time.sleep(delay_sec)

    # If still locked, try renaming then retry once more.
    try:
        parent = os.path.dirname(path)
        base = os.path.basename(path)
        renamed = os.path.join(parent, base + "_delete_later")
        try:
            os.rename(path, renamed)
        except OSError:
            renamed = path  # fallback

        shutil.rmtree(renamed, onerror=_remove_read_only)
        return
    except Exception:
        # Re-raise the last meaningful error
        if last_err:
            raise last_err
        raise


# ----------------------------
# Environment configuration
# ----------------------------

def configure_env_for_packages(packages, maya_app_dir):
    """
    Configure env vars for predictable Maya standalone test runs.

    NOTE: We set MAYA_LOCATION here based on the version (important because your mayaunittest
    module requires MAYA_LOCATION at import-time).
    """
    if maya_app_dir is not None:
        os.environ["MAYA_APP_DIR"] = str(maya_app_dir)

    # Make the run predictable
    os.environ["MAYA_SCRIPT_PATH"] = ""

    # Allow Maya module discovery from all roots
    os.environ["MAYA_MODULE_PATH"] = _join_paths([p["root"] for p in packages])

    # Ensure python/ folders are importable (common studio layout)
    python_dirs = [p["python_dir"] for p in packages if p["python_dir"]]
    if python_dirs:
        existing = os.environ.get("PYTHONPATH", "")
        prefix = _join_paths(python_dirs)
        os.environ["PYTHONPATH"] = prefix + (os.pathsep + existing if existing else "")


# ----------------------------
# Spawn mayapy when needed
# ----------------------------

def spawn_mayapy_and_rerun(mayapy_exe):
    if not os.path.exists(mayapy_exe):
        err = "Cannot find mayapy at: {0}.\nSet --maya-path or --maya or MAYA_LOCATION env!"
        raise RuntimeError(err.format(mayapy_exe))

    script_path = os.path.abspath(__file__)

    forwarded = list(sys.argv[1:])
    if "--_in-mayapy" not in forwarded:
        forwarded.append("--_in-mayapy")

    cmd = [mayapy_exe, script_path] + forwarded
    print("Spawning mayapy:")
    print("  " + " ".join(cmd))

    proc = subprocess.run(cmd, env=os.environ.copy())
    return int(proc.returncode)


# ----------------------------
# CLI
# ----------------------------

def build_arg_parser():
    p = argparse.ArgumentParser(description="Run Maya unit tests for one or more packages.")
    p.add_argument("--maya", type=int,
                   default=DEFAULT_MAYA_VERSION, help="Maya version: 2022, 2024, 2026")

    p.add_argument(
        "--maya-path",
        default=None,
        help="Explicit Maya install root path (overrides --maya and MAYA_LOCATION).",
    )

    p.add_argument(
        "--maya_installs",
        default=os.path.join(_script_dir(), "maya_installs.json"),
        help="Path to maya_installs.json (defaults next to this script).",
    )

    p.add_argument(
        "--packages",
        nargs="+",
        required=True,
        help="One or more package root directories (each must contain tests/).",
    )

    p.add_argument(
        "--clean-maya-app-dir",
        action="store_true",
        default=False,
        help="When it is set, generates a clean MAYA_APP_DIR for each run")

    p.add_argument("--pause", action="store_true",
                   help="Pause at the end (useful when double-clicking).")

    # internal guard
    p.add_argument("--_in-mayapy", action="store_true",
                   help=argparse.SUPPRESS)

    return p


def main():
    args = build_arg_parser().parse_args()

    packages = [package_from_root(p) for p in args.packages]

    # Resolve Maya install location with desired priority
    maya_location = resolve_maya_location(args.maya, args.maya_path, args.maya_installs)

    # IMPORTANT: CLI selection wins -> force MAYA_LOCATION for this run
    # TODO: Does it resets it after run?
    os.environ["MAYA_LOCATION"] = maya_location

    mayapy_exe = mayapy_exe_from_location(maya_location)

    # If not in mayapy, spawn it and rerun.
    if (not is_running_in_mayapy()) and (not getattr(args, "_in_mayapy", False)):
        return spawn_mayapy_and_rerun(mayapy_exe)
    
    # We are inside mayapy here
    maya_app_dir = get_clean_maya_app_dir() if args.clean_maya_app_dir else None

    configure_env_for_packages(packages, maya_app_dir)

    try:
        names = ", ".join([p["name"] for p in packages])
        print("=" * 30, "Maya Unit Test Runner", "=" * 30)
        print("MAYA_LOCATION:", os.environ.get("MAYA_LOCATION"))
        print("sys.executable:", sys.executable)
        print("MAYA_APP_DIR:", os.environ.get("MAYA_APP_DIR"))
        print("\nStarting unittest for packages: {0}".format(names))

        # Import after MAYA_LOCATION is set (your mayaunittest needs it at import time)
        import mayaunittest  # type: ignore

        test_dirs = [p["tests_dir"] for p in packages]
        mayaunittest.run_tests_from_commandline(directories=test_dirs)

        return 0
    finally:
        if args.clean_maya_app_dir:
            if maya_app_dir is not None and os.path.exists(maya_app_dir):
                try:
                    _rmtree_with_retries(maya_app_dir)
                except Exception as e:
                    print("Warning: could not remove temp MAYA_APP_DIR: {0}".format(e))

        if args.pause:
            input("Press [Enter] to continue...")


if __name__ == "__main__":
    raise SystemExit(main())
