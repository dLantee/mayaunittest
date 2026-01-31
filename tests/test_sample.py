import mayaunittest

class SampleTestCase(mayaunittest.MayaTestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)

    def test_subtraction(self):
        self.assertEqual(5 - 3, 2)