# Shim to allow py.test to run without panzee being installed inside
# the Python package directory; i.e, in-place
import sys
import os
sys.path.append(os.path.abspath(os.pardir))
