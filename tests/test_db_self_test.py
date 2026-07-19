import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "awaek" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import db


class SelfTestIsolationTests(unittest.TestCase):
    def setUp(self):
        self.original_data_dir = db.DATA_DIR
        self.original_db_path = db.DB_PATH

    def tearDown(self):
        db.DATA_DIR = self.original_data_dir
        db.DB_PATH = self.original_db_path

    def configure_unwritten_database(self, root):
        db.DATA_DIR = root / "configured-data"
        db.DB_PATH = db.DATA_DIR / "awaek.db"

    def test_self_test_does_not_write_the_configured_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.configure_unwritten_database(Path(temp_dir))

            result = db.run_self_test()

            self.assertTrue(result["ok"])
            self.assertTrue(result["isolated"])
            self.assertEqual(result["upsert"]["inserted"], 1)
            self.assertFalse(db.DB_PATH.exists())

    def test_self_test_restores_paths_after_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.configure_unwritten_database(Path(temp_dir))
            configured_data_dir = db.DATA_DIR
            configured_db_path = db.DB_PATH

            with mock.patch.object(db, "init_db", side_effect=RuntimeError("failed")):
                with self.assertRaisesRegex(RuntimeError, "failed"):
                    db.run_self_test()

            self.assertEqual(db.DATA_DIR, configured_data_dir)
            self.assertEqual(db.DB_PATH, configured_db_path)
            self.assertFalse(db.DB_PATH.exists())


if __name__ == "__main__":
    unittest.main()
