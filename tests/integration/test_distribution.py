from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DistributionIntegration(unittest.TestCase):
    def test_installed_package_imports_without_host_or_working_directory(self):
        code = '''
import sys
from veriarbor import model, graph, verification, learning, lifecycle, search, scheduling, review, protocols
assert not any(key == 'cgkn' or key.startswith('cgkn.') for key in sys.modules)
assert model.stable_hash({'a': 1, 'b': 2}) == model.stable_hash({'b': 2, 'a': 1})
'''
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-I', '-c', code], cwd=directory, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
