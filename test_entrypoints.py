"""Catch missing project imports when serverless runtimes load API files."""
import subprocess
import sys
import unittest
from pathlib import Path


class EntrypointTests(unittest.TestCase):
    def test_api_imports_without_project_on_python_path(self):
        root = Path(__file__).resolve().parent
        for file in ('history.py', 'telegram.py'):
            with self.subTest(file=file):
                result = subprocess.run([sys.executable, '-I', '-c',
                    'import runpy; runpy.run_path(' + repr(str(root / 'api' / file)) + ')'],
                    cwd='/tmp', capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
