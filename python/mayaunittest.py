"""
Contains functions and classes to aid in the unit testing process within Maya.

Requirements:
    - Tests must be written using the mayaunittest module.
    - Tests must be located in a "tests" directory within a module/package.
    - Test methods must be named with a "test_" prefix.
    - Test case classes must be named with a "Tests" suffix.
    - MAYA_LOCATION environment variable must be set to the Maya installation path.
"""
import logging
import os
import shutil
import sys
import tempfile
import unittest
import uuid


def mayapython():
    """
    Return Maya's site-packages path; raise informative error if not configured.

    We probe a few known layouts because they differ by OS and Maya version.
    """
    maya_loc = os.environ.get("MAYA_LOCATION")
    if not maya_loc:
        raise RuntimeError(
            "MAYA_LOCATION environment variable is not set. "
            "Cannot locate Maya Python site-packages."
        )

    candidates = [
        os.path.join(maya_loc, "Python", "Lib", "site-packages"),  # Windows common
        os.path.join(maya_loc, "Python", "lib", "site-packages"),  # Linux common
        os.path.join(maya_loc, "Python", "lib", "python3", "site-packages"),  # fallback
    ]

    for p in candidates:
        if os.path.isdir(p):
            return p

    raise RuntimeError(
        "Could not find Maya site-packages under MAYA_LOCATION: {0}\n"
        "Tried:\n  - {1}".format(maya_loc, "\n  - ".join(candidates))
    )


def filter_sys_path(literals):
    syspaths = list(sys.path)
    for fp in syspaths:
        if all([l in fp for l in literals]):
            try:
                sys.path.remove(fp)
            except ValueError:
                pass


# Remove auto-completion path that overrides real maya python libs.
filter_sys_path(["pymel", "extras", "completion"])

# Make sure Maya's site-packages comes first before anything else.
maya_site = mayapython()
if maya_site not in sys.path:
    sys.path.insert(0, maya_site)

# Once auto-completion path removed we can import maya modules.
import maya.cmds as cmds  # noqa: E402
import maya.standalone  # noqa: E402


CUSTOM_RUNNER = "DL_UNITTEST"


def run_tests(directories=None, test=None, test_suite=None):
    if test_suite is None:
        test_suite = get_tests(directories, test)

    runner = unittest.TextTestRunner(verbosity=2, resultclass=MayaTestResult)
    runner.failfast = False
    runner.buffer = Settings.buffer_output
    runner.run(test_suite)


def get_tests(directories=None, test=None, test_suite=None):
    """
    Discover and return a unittest.TestSuite containing the tests.
    By default, discovers tests in all Maya module "tests" directories.
    Args:
        directories (iterable of str): Directories to search for tests. If None, uses all Maya module tests directories.
        test (str): Specific test to load (module, class, or method). If None, discovers all tests in the directories.
        test_suite (unittest.TestSuite): An existing test suite to add tests to. If None, a new suite is created.
    Returns:
        unittest.TestSuite: The collected test suite.
    """
    if directories is None:
        directories = maya_module_tests()

    if test_suite is None:
        test_suite = unittest.TestSuite()

    directories_added_to_path = []

    if test:
        # Add test directories to sys.path so loadTestsFromName can import modules
        for p in directories:
            if add_to_path(p):
                directories_added_to_path.append(p)

        discovered_suite = unittest.TestLoader().loadTestsFromName(test)
        if discovered_suite.countTestCases():
            test_suite.addTests(discovered_suite)
    else:
        for p in directories:
            discovered_suite = unittest.TestLoader().discover(p)
            if discovered_suite.countTestCases():
                test_suite.addTests(discovered_suite)

    # Remove the added paths.
    for path in directories_added_to_path:
        try:
            sys.path.remove(path)
        except ValueError:
            pass

    return test_suite


def maya_module_tests():
    """Generator function to iterate over all the Maya module tests directories."""
    module_path = os.environ.get("MAYA_MODULE_PATH", "")
    for path in module_path.split(os.pathsep):
        p = "{0}/tests".format(path)
        if os.path.exists(p):
            yield p


def run_tests_from_commandline(directories=None, test=None, test_suite=None):
    """Runs the tests in Maya standalone mode."""
    maya.standalone.initialize()

    # Ensure PYTHONPATH entries are present in sys.path
    realsyspath = [os.path.realpath(p) for p in sys.path]
    pythonpath = os.environ.get("PYTHONPATH", "")
    for p in pythonpath.split(os.pathsep):
        p = os.path.realpath(p)
        if p and p not in realsyspath:
            sys.path.insert(0, p)

    run_tests(directories, test, test_suite)

    # Starting Maya 2016, we have to call uninitialize
    try:
        if float(cmds.about(v=True)) >= 2016.0:
            maya.standalone.uninitialize()
    except Exception:
        # Be defensive: still try to uninitialize if possible
        try:
            maya.standalone.uninitialize()
        except Exception:
            pass


class Settings:
    temp_dir = os.path.join(tempfile.gettempdir(), "mayaunittest", str(uuid.uuid4()))
    delete_files = True
    buffer_output = True
    file_new = True


def set_temp_dir(directory):
    if os.path.exists(directory):
        Settings.temp_dir = directory
    else:
        raise RuntimeError("{0} does not exist.".format(directory))


def set_delete_files(value):
    Settings.delete_files = value


def set_buffer_output(value):
    Settings.buffer_output = value


def set_file_new(value):
    Settings.file_new = value


def add_to_path(path):
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        return True
    return False


class MayaTestCase(unittest.TestCase):
    files_created = []
    plugins_loaded = set()

    @classmethod
    def load_plugin(cls, plugin):
        cmds.loadPlugin(plugin, qt=True)
        cls.plugins_loaded.add(plugin)

    @classmethod
    def unload_plugins(cls):
        if not cls.plugins_loaded:
            cls.plugins_loaded = set()
            return

        for plugin in list(cls.plugins_loaded):
            try:
                cmds.unloadPlugin(plugin)
            except Exception as e:
                logging.warning("Failed to unload plugin %s: %s", plugin, e)

        cls.plugins_loaded = set()

    @classmethod
    def delete_temp_files(cls):
        if not Settings.delete_files:
            return

        for f in list(cls.files_created):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                logging.warning("Failed to remove temp file %s: %s", f, e)

        cls.files_created = []

        try:
            if os.path.exists(Settings.temp_dir):
                shutil.rmtree(Settings.temp_dir)
        except Exception as e:
            logging.warning("Failed to remove temp dir %s: %s", Settings.temp_dir, e)

    @classmethod
    def tearDownClass(cls):
        super(MayaTestCase, cls).tearDownClass()
        cls.delete_temp_files()
        cls.unload_plugins()

    @classmethod
    def get_temp_filename(cls, file_name):
        temp_dir = Settings.temp_dir
        os.makedirs(temp_dir, exist_ok=True)

        candidate = os.path.join(temp_dir, file_name)
        parent_dir = os.path.dirname(candidate)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        base, ext = os.path.splitext(candidate)
        path = candidate
        count = 0
        while os.path.exists(path):
            count += 1
            path = "{0}{1}{2}".format(base, count, ext)

        cls.files_created.append(path)
        return path

    def assertListAlmostEqual(self, first, second, places=7, msg=None, delta=None):
        self.assertEqual(len(first), len(second), msg)
        for a, b in zip(first, second):
            self.assertAlmostEqual(a, b, places, msg, delta)

    def tearDown(self):
        if Settings.file_new and CUSTOM_RUNNER not in os.environ:
            cmds.file(f=True, new=True)


class MayaTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super(MayaTestResult, self).__init__(stream, descriptions, verbosity)
        self.successes = []

    def startTestRun(self):
        super(MayaTestResult, self).startTestRun()
        os.environ[CUSTOM_RUNNER] = "1"

        ScriptEditorState.suppress_output()
        if Settings.buffer_output:
            logging.disable(logging.CRITICAL)

    def stopTestRun(self):
        if Settings.buffer_output:
            logging.disable(logging.NOTSET)

        ScriptEditorState.restore_output()

        if Settings.delete_files and os.path.exists(Settings.temp_dir):
            try:
                shutil.rmtree(Settings.temp_dir)
            except Exception as e:
                logging.warning("Failed to remove temp dir %s: %s", Settings.temp_dir, e)

        if CUSTOM_RUNNER in os.environ:
            del os.environ[CUSTOM_RUNNER]

        super(MayaTestResult, self).stopTestRun()

    def stopTest(self, test):
        super(MayaTestResult, self).stopTest(test)
        if Settings.file_new:
            cmds.file(f=True, new=True)

    def addSuccess(self, test):
        super(MayaTestResult, self).addSuccess(test)
        self.successes.append(test)


class ScriptEditorState(object):
    suppress_results = None
    suppress_errors = None
    suppress_warnings = None
    suppress_info = None

    @classmethod
    def suppress_output(cls):
        if Settings.buffer_output:
            cls.suppress_results = cmds.scriptEditorInfo(q=True, suppressResults=True)
            cls.suppress_errors = cmds.scriptEditorInfo(q=True, suppressErrors=True)
            cls.suppress_warnings = cmds.scriptEditorInfo(q=True, suppressWarnings=True)
            cls.suppress_info = cmds.scriptEditorInfo(q=True, suppressInfo=True)
            cmds.scriptEditorInfo(
                e=True,
                suppressResults=True,
                suppressInfo=True,
                suppressWarnings=True,
                suppressErrors=True,
            )

    @classmethod
    def restore_output(cls):
        if None not in {cls.suppress_results, cls.suppress_errors, cls.suppress_warnings, cls.suppress_info}:
            cmds.scriptEditorInfo(
                e=True,
                suppressResults=cls.suppress_results,
                suppressInfo=cls.suppress_info,
                suppressWarnings=cls.suppress_warnings,
                suppressErrors=cls.suppress_errors,
            )
