# Maya Unit Testing Framework

🛠️ Developed for: **Autodesk Maya 2026**  
🐍 Python version: **3.11**

Contains functions and classes to aid in the unit testing process within Maya.

Source: https://www.chadvernon.com/blog/unit-testing-in-maya/

### Requirements

- Tests must be written using the unittest module.
- Tests must be located in a "tests" directory within a Maya module.
- Test methods must be named with a "test_" prefix.
- Test case classes must be named with a "Test" suffix.
- MAYA_LOCATION environment variable must be set to the Maya installation path.

### The main classes
- **TestCase** :
  A derived class of unittest.TestCase which add convenience functionality
  such as auto plug-in loading/unloading, and auto temporary file name generation
  and cleanup.
- **TestResult**:
  A derived class of unittest.TextTestResult which customizes
  the test result so we can do things like do a file new between
  each test and suppress script editor output.

### To write tests for this system you need to
    a) Derive from TestCase
    b) Write one or more tests that use the unittest module's assert methods to validate the results.

### Example usage

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

### To run all tests
```python
mayaunittest.run_tests()
```

### Settings

You can customize the behavior of the test framework by setting the following environment variables:
- **MAYA_TEST_TEMP_DIR**: Specifies the directory where temporary files created during tests will be stored. If not set, a default temporary directory will be used.
- **MAYA_TEST_CLEANUP**: If set to "1", temporary files created
- during tests will be deleted after the tests complete. If not set or set to "0", temporary files will be retained for inspection.

Set Settings.


### License