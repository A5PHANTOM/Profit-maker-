"""Catch missing project imports when serverless runtimes load API files."""
import subprocess
import sys
import unittest
from pathlib import Path
import io
from api.history import handler


class EntrypointTests(unittest.TestCase):
    def test_vercel_adapter_dispatch_does_not_collide_with_handler(self):
        # Vercel's runtime wraps user classes and defines handle_request(self).
        class VercelHandler(handler):
            def handle_request(self):
                getattr(self, 'do_' + self.command)()
                self.wfile.flush()

        instance = object.__new__(VercelHandler)
        instance.command = 'GET'
        instance.headers = {}
        instance.wfile = io.BytesIO()
        responses = []
        instance.respond = lambda status, data: responses.append((status, data))
        instance.handle_request()
        self.assertEqual(responses[0][0], 401)

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
