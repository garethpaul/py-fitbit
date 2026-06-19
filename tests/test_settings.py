#!/usr/bin/env python
from __future__ import print_function

import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_NAME = "FITBIT_CONSUMER_KEY"
SECRET_NAME = "FITBIT_CONSUMER_SECRET"
KEY_VALUE = "synthetic-key-value"
SECRET_VALUE = "synthetic-secret-value"
KEY_PLACEHOLDERS = (
    "changeme",
    "CHANGE ME",
    " change-me ",
    "replace-me",
    " RePlAcE_Me ",
    "YOUR_FITBIT_CONSUMER_KEY",
    " your fitbit consumer key ",
    "<consumer-key>",
    " Example Key ",
)
SECRET_PLACEHOLDERS = (
    "changeme",
    "CHANGE ME",
    " change-me ",
    "replace-me",
    " RePlAcE_Me ",
    "YOUR_FITBIT_CONSUMER_SECRET",
    " your fitbit consumer secret ",
    "<consumer-secret>",
    " Example Secret ",
)


class SettingsContractTest(unittest.TestCase):
    def run_import(self, key=KEY_VALUE, secret=SECRET_VALUE, assertions=""):
        working_directory = tempfile.mkdtemp(prefix="py-fitbit-settings-")
        self.addCleanup(shutil.rmtree, working_directory)

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = ROOT
        if key is None:
            environment.pop(KEY_NAME, None)
        else:
            environment[KEY_NAME] = key
        if secret is None:
            environment.pop(SECRET_NAME, None)
        else:
            environment[SECRET_NAME] = secret

        command = "import settings"
        if assertions:
            command += "; " + assertions
        process = subprocess.Popen(
            [sys.executable, "-c", command],
            cwd=working_directory,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr, os.listdir(working_directory)

    def assert_rejected(self, name, key=KEY_VALUE, secret=SECRET_VALUE):
        returncode, stdout, stderr, created = self.run_import(key, secret)
        self.assertNotEqual(0, returncode)
        self.assertEqual(b"", stdout)
        self.assertIn(name.encode("ascii"), stderr)
        self.assertNotIn(KEY_VALUE.encode("ascii"), stderr)
        self.assertNotIn(SECRET_VALUE.encode("ascii"), stderr)
        self.assertEqual([], created)

    def test_configured_values_are_exposed_unchanged(self):
        assertions = (
            "assert settings.CONSUMER_KEY == %r; "
            "assert settings.CONSUMER_SECRET == %r"
        ) % (KEY_VALUE, SECRET_VALUE)
        returncode, stdout, stderr, created = self.run_import(
            assertions=assertions
        )
        self.assertEqual(0, returncode, stderr)
        self.assertEqual(b"", stdout)
        self.assertEqual(b"", stderr)
        self.assertEqual([], created)

    def test_missing_key_is_rejected(self):
        self.assert_rejected(KEY_NAME, key=None)

    def test_missing_secret_is_rejected(self):
        self.assert_rejected(SECRET_NAME, secret=None)

    def test_empty_key_is_rejected(self):
        self.assert_rejected(KEY_NAME, key="")

    def test_empty_secret_is_rejected(self):
        self.assert_rejected(SECRET_NAME, secret="")

    def test_whitespace_only_key_is_rejected(self):
        self.assert_rejected(KEY_NAME, key=" \t")

    def test_whitespace_only_secret_is_rejected(self):
        self.assert_rejected(SECRET_NAME, secret=" \t")

    def test_key_with_surrounding_whitespace_is_rejected(self):
        self.assert_rejected(KEY_NAME, key=" valid-key ")

    def test_secret_with_control_character_is_rejected(self):
        self.assert_rejected(SECRET_NAME, secret="valid-secret\ncontinued")

    def test_placeholder_like_keys_are_rejected(self):
        for value in KEY_PLACEHOLDERS:
            self.assert_rejected(KEY_NAME, key=value)

    def test_placeholder_like_secrets_are_rejected(self):
        for value in SECRET_PLACEHOLDERS:
            self.assert_rejected(SECRET_NAME, secret=value)

    def test_non_placeholder_values_with_similar_words_are_preserved(self):
        key = "changeme-live-9f4b2"
        secret = "example-secret-live-a7c8d"
        assertions = (
            "assert settings.CONSUMER_KEY == %r; "
            "assert settings.CONSUMER_SECRET == %r"
        ) % (key, secret)
        returncode, stdout, stderr, created = self.run_import(
            key=key,
            secret=secret,
            assertions=assertions,
        )
        self.assertEqual(0, returncode, stderr)
        self.assertEqual(b"", stdout)
        self.assertEqual(b"", stderr)
        self.assertEqual([], created)


if __name__ == "__main__":
    unittest.main()
