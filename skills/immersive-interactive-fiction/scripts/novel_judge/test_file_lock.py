"""Prove contention and release after process death on the current OS."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from .file_lock import exclusive_file_lock

class PortableLockTests(unittest.TestCase):
    def test_timeout_is_cross_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "branch.lock"
            code = ("from novel_judge.file_lock import exclusive_file_lock; from pathlib import Path; "
                    "import sys; "
                    "with_lock=exclusive_file_lock(Path(sys.argv[1]), timeout=0.1); with_lock.__enter__()")
            with exclusive_file_lock(path):
                result = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"TimeoutError", result.stderr)
            with exclusive_file_lock(path, timeout=0):
                pass

    def test_process_death_releases_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "branch.lock"
            code = ("from novel_judge.file_lock import exclusive_file_lock; from pathlib import Path; "
                    "import sys,time; "
                    "lock=exclusive_file_lock(Path(sys.argv[1])); lock.__enter__(); "
                    "print('locked',flush=True); time.sleep(30)")
            child = subprocess.Popen([sys.executable, "-c", code, str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                self.assertEqual(child.stdout.readline().strip(), b"locked")
                child.kill()
                child.wait(timeout=10)
                with exclusive_file_lock(path, timeout=1):
                    pass
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=10)
                child.stdout.close()
                child.stderr.close()

if __name__ == "__main__":
    unittest.main()
