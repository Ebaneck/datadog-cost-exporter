import unittest
from unittest.mock import patch
from io import StringIO
import tempfile
import os

from config.config import get_configs


class TestGetConfigs(unittest.TestCase):
    def setUp(self):
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_config_filename = self.temp_config_file.name

    def tearDown(self):
        os.remove(self.temp_config_filename)

    def test_get_configs_valid_config(self):
        with patch("sys.argv", ["main.py", "-c", self.temp_config_filename]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                # Create a valid temporary config file
                with open(self.temp_config_filename, "w") as temp_config:
                    temp_config.write(
                        "dd_api_key: your_api_key\n" "dd_app_key: your_app_key\n"
                    )

                result = get_configs()

                # Validate the result
                self.assertEqual(result["dd_api_key"], "your_api_key")
                self.assertEqual(result["dd_app_key"], "your_app_key")
                self.assertEqual(mock_stdout.getvalue(), "")

    def test_get_configs_missing_config(self):
        with patch("sys.argv", ["main.py", "-c", "nonexistent_config.yaml"]):
            with self.assertRaises(SystemExit) as cm:
                get_configs()

            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
