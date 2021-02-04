import os
import sys
import unittest

if __name__ == "__main__":
    this_dir = os.path.dirname(__file__)
    tests = unittest.TestLoader().discover(start_dir=this_dir)

    result = unittest.TextTestRunner().run(tests)
    if result.failures:
        sys.exit(1)
