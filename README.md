![A local image example](./images/unittest_for_maya_wallpaper.png)
# Maya Unit Testing Framework

🛠️ Developed for: **Autodesk Maya 2022+**  
🐍 Python version: **3.7+**

Contains functions and classes to aid in the unit testing process within Maya.
It starts a standalone Maya session, discovers and runs unit tests, and reports results
in a readable format. It opens a new scene between each test to ensure test isolation.

Source: https://www.chadvernon.com/blog/unit-testing-in-maya/

### Howto
1. Put mayaunittest module somewhere in your PYTHONPATH. (with command line not needed)
2. Create a **"/tests"** directory in your Maya module/package.
3. Write test cases by deriving from `mayaunittest.MayaTestCase`.
4. Use `bin/run_maya_tests.py` to run tests from command line or
   use `mayaunittest.run_tests()` to run tests from within Maya.


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

Running test from command line makes development more convinient since you don't have to
constantly restart Maya manually. When you run `run_maya_tests.py` it spwans
a standalone Maya session in the background, runs the tests, and then closes Maya when done.

Flags:
- --maya : Specify the Maya version to use (e.g., 2022, 2023, 2024, 2025, 2026).
- --packages : Space-separated list of paths to Maya modules/packages containing tests.
- --pause : Pause the Maya session after tests complete for inspection.
- --clean-maya-app-dir : Generates a temporary clean maya app dir.
- --maya-path: Specify a custom Maya installation path.
- --maya-config: Specify a custom Maya installation look up map.
- --maya-installs: Specify a JSON file containing Maya installation paths. (Good for custom setups)

```commandline
cd path\to\mayaunittest
py "bin\run_maya_tests.py" --maya 2026 --packages D:\projects\pkgA D:\projects\pkgB --pause
py "bin\run_maya_tests.py" --packages D:\projects\pkgA --clean-maya-app-dir
py "bin\run_maya_tests.py" --maya-path "C:\Program Files\Autodesk\Maya2024" --packages D:\projects\pkgA
py "bin\run_maya_tests.py" --maya-installs "path\to\custom_maya_installs.json" --packages D:\projects\pkgA
```

### Priority of Maya executable resolution
1. --maya-path argument
2. --maya-installs argument
3. MAYA_LOCATION environment variable
4. Default installation paths based on --maya argument

### Example test case
```python
from maya import cmds
from mayaunittest import MayaTestCase

class SampleTests(MayaTestCase):
    def test_create_sphere(self):
        sphere = cmds.polySphere(n='mySphere')[0]
        self.assertEqual('mySphere', sphere)
        self.assertIsInstance(sphere, str)
```

> **_NOTE:_**
More self.assert* function references can be found in the official unittest documentation:
https://docs.python.org/3/library/unittest.html#classes-and-functions

### To run test case in Maya
```python
import mayaunittest
mayaunittest.run_tests(test='test_sample.SampleTests')

# To run an individual test in a test case
mayaunittest.run_tests(test='test_sample.SampleTests.test_create_sphere')

# To run all tests in Maya Modules
# MAYA_MODULE_PATH must be set to include the modules
mayaunittest.run_tests()
```

### Math module example

```python
# mypackage/python/mymodule.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
```


```python
# mypackage/tests/test_mymodule.py
from maya import cmds
from mayaunittest import MayaTestCase
import mymodule

class MyModuleTests(MayaTestCase):
    def test_add(self):
        result = mymodule.add(3, 5)
        self.assertEqual(result, 8)

    def test_subtract(self):
        result = mymodule.subtract(10, 4)
        self.assertEqual(result, 6)
```

### Advanced example
```python
from maya import cmds
from mayaunittest import MayaTestCase

class AdvSampleTests(MayaTestCase):
    def test_create_attribute(self):
        sphere = cmds.polySphere(n='mySphere')[0]
        cmds.addAttr(sphere, longName='myCustomAttr', attributeType='float', defaultValue=1.0)
        cmds.xform(sphere, translation=(0, 5, 0))
        
        self.assertEqual('mySphere', sphere)
        self.assertIsInstance(sphere, str)
        self.assertTrue(cmds.attributeQuery('myCustomAttr', node=sphere, exists=True))
        self.assertEqual(cmds.getAttr(f'{sphere}.myCustomAttr'), 1.0)
        self.assertListEqual(cmds.xform(sphere, query=True, translation=True), [0.0, 5.0, 0.0])
```