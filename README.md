# Maya Unit Testing Framework

🛠️ Developed for: **Autodesk Maya 2022+**  
🐍 Python version: **3.7**

Contains functions and classes to aid in the unit testing process within Maya.

Source: https://www.chadvernon.com/blog/unit-testing-in-maya/

### Requirements

  - Tests must be written using the `mayaunittest` module.
  - Tests must be located in a **"/tests"** directory within a module/package.
  - Test methods must be named with a **"test_"** prefix.
  - Test case classes must be named with a **"Tests"** suffix.
  - **MAYA_LOCATION** environment variable must be set to the Maya installation path.

### The main classes
- **MayaTestCase** :
  A derived class of `unittest.TestCase` which add convenience functionality
  such as auto plug-in loading/unloading, and auto temporary file name generation
  and cleanup.
- **MayaTestResult**:
  A derived class of `unittest.TextTestResult` which customizes
  the test result so we can do things like do a file new between
  each test and suppress script editor output.

### Example commandline usage

- --maya : Specify the Maya version to use (e.g., 2022, 2023, 2024, 2025, 2026).
- --packages : Space-separated list of paths to Maya modules/packages containing tests.
- --pause : Pause the Maya session after tests complete for inspection.
- --maya-app-dir : Specify a custom Maya application directory. (Generates a temporary clean one if not provided or doesn't exist.)

```commandline
py "path\to\run_maya_tests.py" --maya 2022 --packages D:\projects\pkgA D:\projects\pkgB --pause
py "path\to\run_maya_tests.py" --maya 2026 --packages D:\projects\pkgA --maya-app-dir F:\Extensions\maya\2022
```

### Example test case
```python
from maya import cmds
from mayaunittest import MayaTestCase

class SampleTests(MayaTestCase):
    def test_create_sphere(self):
        sphere = cmds.polySphere(n='mySphere')[0]
        self.assertEqual('mySphere', sphere)
```

### To run just this test case in Maya
```python
import mayaunittest
mayaunittest.run_tests(test='test_sample.SampleTests')
```

### To run an individual test in a test case
```python
import mayaunittest
mayaunittest.run_tests(test='test_sample.SampleTests.test_create_sphere')
```

### To run all tests in Maya Modules
```python
mayaunittest.run_tests()
```

### Settings

```Python
import mayaunittest
mayaunittest.Settings.cleanup_temp_files = True
# Specifies where files generated during tests should be stored
mayaunittest.Settings.mayaunittest.Settings.temp_dir = ""
# Controls whether temp files should be deleted after running all tests in the test case
mayaunittest.Settings.delete_files = True
# Specifies whether the standard output and standard error streams are buffered during the test run.
mayaunittest.Settings.buffer_output = True
```