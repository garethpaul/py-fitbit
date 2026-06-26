#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CheckerIntegrityTest(unittest.TestCase):
    def test_structured_response_error_mutation_is_rejected(self):
        working_directory = tempfile.mkdtemp(prefix="py-fitbit-structured-error-")
        self.addCleanup(shutil.rmtree, working_directory)
        checkout = os.path.join(working_directory, "checkout")
        shutil.copytree(
            ROOT,
            checkout,
            ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"),
        )

        source_path = os.path.join(checkout, "fitbit.py")
        with open(source_path, "r") as handle:
            source = handle.read()
        weakened_source = source.replace(
            "class FitbitResponseError(IOError):",
            "class FitbitResponseError(Exception):",
        )
        self.assertNotEqual(source, weakened_source)
        with open(source_path, "w") as handle:
            handle.write(weakened_source)

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            [sys.executable, "scripts/check_legacy_fitbit.py"],
            cwd=checkout,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        self.assertNotEqual(0, process.returncode, stdout + stderr)
        self.assertIn(b"structured Fitbit response error contract failed", stderr)

    def test_encoded_json_response_validation_mutation_is_rejected(self):
        working_directory = tempfile.mkdtemp(prefix="py-fitbit-json-validation-")
        self.addCleanup(shutil.rmtree, working_directory)
        checkout = os.path.join(working_directory, "checkout")
        shutil.copytree(
            ROOT,
            checkout,
            ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"),
        )

        source_path = os.path.join(checkout, "fitbit.py")
        with open(source_path, "r") as handle:
            source = handle.read()
        weakened_source = source.replace(
            "if api_call_requires_json_validation(api_call):",
            "if urlparse.urlsplit(api_call).path.lower().endswith('.json'):",
        )
        self.assertNotEqual(source, weakened_source)
        with open(source_path, "w") as handle:
            handle.write(weakened_source)

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            [sys.executable, "scripts/check_legacy_fitbit.py"],
            cwd=checkout,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        self.assertNotEqual(0, process.returncode, stdout + stderr)
        self.assertIn(b"encoded JSON response validation contract failed", stderr)

    def test_legacy_runtime_and_current_fitbit_boundary_mutation_is_rejected(self):
        working_directory = tempfile.mkdtemp(prefix="py-fitbit-doc-boundary-")
        self.addCleanup(shutil.rmtree, working_directory)
        checkout = os.path.join(working_directory, "checkout")
        shutil.copytree(
            ROOT,
            checkout,
            ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"),
        )

        readme_path = os.path.join(checkout, "README.md")
        with open(readme_path, "r") as handle:
            readme_source = handle.read()
        weakened_source = readme_source.replace("`oauth==1.0.1`", "an OAuth package")
        weakened_source = weakened_source.replace(
            "Current Fitbit Web API documentation uses OAuth 2.0.",
            "Fitbit supports OAuth.",
        )
        with open(readme_path, "w") as handle:
            handle.write(weakened_source)

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            [sys.executable, "scripts/check_legacy_fitbit.py"],
            cwd=checkout,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        self.assertNotEqual(0, process.returncode, stdout + stderr)
        self.assertIn(b"README must document historical runtime dependency", stderr)
        self.assertIn(b"README must document the current Fitbit OAuth 2.0 boundary", stderr)

    def test_combined_loader_and_test_disable_mutation_is_rejected(self):
        working_directory = tempfile.mkdtemp(prefix="py-fitbit-checker-")
        self.addCleanup(shutil.rmtree, working_directory)
        checkout = os.path.join(working_directory, "checkout")
        shutil.copytree(
            ROOT,
            checkout,
            ignore=shutil.ignore_patterns(".git", "*.pyc", "__pycache__"),
        )

        settings_path = os.path.join(checkout, "settings.py")
        with open(settings_path, "r") as handle:
            settings_source = handle.read()
        fail_open_source = settings_source.replace(
            "and value == value.strip()\n",
            "",
        )
        self.assertNotEqual(settings_source, fail_open_source)
        with open(settings_path, "w") as handle:
            handle.write(fail_open_source)

        test_path = os.path.join(checkout, "tests", "test_settings.py")
        with open(test_path, "w") as handle:
            handle.write(
                "#!/usr/bin/env python\n"
                "import unittest\n\n"
                "class DisabledSettingsTest(unittest.TestCase):\n"
                "    def test_nothing(self):\n"
                "        pass\n\n"
                "if __name__ == '__main__':\n"
                "    unittest.main()\n"
            )

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.Popen(
            [sys.executable, "scripts/check_legacy_fitbit.py"],
            cwd=checkout,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()

        self.assertNotEqual(0, process.returncode, stdout + stderr)
        self.assertIn(b"settings.py runtime contract failed", stderr)


if __name__ == "__main__":
    unittest.main()
