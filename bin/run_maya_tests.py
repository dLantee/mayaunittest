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
    py tools/run_maya_tests.py --maya 2022 --packages D:\\projects\\pkgA D:\\projects\\pkgB --pause
    py tools/run_maya_tests.py --maya 2026 --packages D:\\projects\\pkgA --no-clean-env
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


# ----------------------------
# Maya discovery
# ----------------------------

def get_maya_location(maya_version):
    """
    Return Maya install dir.
    If MAYA_LOCATION is set, it wins.
    """
    env = os.environ.get("MAYA_LOCATION")
    if env:
        return env

    sysname = platform.system()
    if sysname == "Windows":
        return "C:/Program Files/Autodesk/Maya{0}".format(maya_version)
    if sysname == "Darwin":
        return "/Applications/Autodesk/maya{0}/Maya.app/Contents".format(maya_version)

    # Linux
    location = "/usr/autodesk/maya{0}".format(maya_version)
    if maya_version < 2016:
        location += "-x64"
    return location


def mayapy_exe(maya_version):
    base = get_maya_location(maya_version)
    exe = os.path.join(base, "bin", "mayapy")
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

def spawn_mayapy_and_rerun(maya_version):
    exe = mayapy_exe(maya_version)
    if not os.path.exists(exe):
        raise RuntimeError(
            "Cannot find mayapy for Maya {0} at: {1}\n"
            "Set MAYA_LOCATION environment variable!".format(maya_version, exe)
        )

    script_path = os.path.abspath(__file__)

    forwarded = list(sys.argv[1:])
    if "--_in-mayapy" not in forwarded:
        forwarded.append("--_in-mayapy")

    cmd = [exe, script_path] + forwarded
    print("Spawning mayapy:")
    print("  " + " ".join(cmd))

    # Pass through env (now including MAYA_LOCATION etc.)
    proc = subprocess.run(cmd, env=os.environ.copy())
    return int(proc.returncode)


# ----------------------------
# CLI
# ----------------------------

def build_arg_parser():
    p = argparse.ArgumentParser(description="Run Maya unit tests for one or more packages.")
    p.add_argument("--maya", type=int, default=DEFAULT_MAYA_VERSION, help="Maya version: 2022, 2024, 2026")

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
        help=("Generates a clean MAYA_APP_DIR for each run by default. \
        Use this flag to disable clean env."),
    )

    p.add_argument("--pause", action="store_true", help="Pause at the end (useful when double-clicking).")

    # internal guard
    p.add_argument("--_in-mayapy", action="store_true", help=argparse.SUPPRESS)

    return p


def main():
    args = build_arg_parser().parse_args()

    # IMPORTANT: set MAYA_LOCATION from version if not already set
    if not os.environ.get("MAYA_LOCATION"):
        os.environ["MAYA_LOCATION"] = get_maya_location(args.maya)

    packages = [package_from_root(p) for p in args.packages]

    # If not in mayapy, spawn it and rerun.
    if (not is_running_in_mayapy()) and (not args._in_mayapy):
        return spawn_mayapy_and_rerun(args.maya)

    # We are in mayapy here
    maya_app_dir = get_clean_maya_app_dir() if args.clean_maya_app_dir else None

    try:
        names = ", ".join([p["name"] for p in packages])
        print("Starting unittest for packages: {0}".format(names))

        configure_env_for_packages(packages, maya_app_dir)

        # Import after env is configured (mayaunittest wants MAYA_LOCATION at import time)
        import mayaunittest  # type: ignore

        # Run with Maya standalone init/uninit
        test_dirs = [p["tests_dir"] for p in packages]
        mayaunittest.run_tests_from_commandline(directories=test_dirs)

        return 0
    finally:
        if args.clean_maya_app_dir:
            if maya_app_dir is not None and os.path.exists(maya_app_dir):
                _rmtree_with_retries(maya_app_dir)
        if args.pause:
            input("Press [Enter] to continue...")


if __name__ == "__main__":
    raise SystemExit(main())
