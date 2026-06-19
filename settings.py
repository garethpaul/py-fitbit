"""
Secret-free Fitbit API configuration.

Set the required values in the environment before running fitbit.py:

    FITBIT_CONSUMER_KEY
    FITBIT_CONSUMER_SECRET
"""
import os


def _required_env(name):
    value = os.environ.get(name)
    if value and value.strip():
        return value
    raise RuntimeError(
        "Missing required environment variable %s. Set Fitbit OAuth "
        "credentials in the environment before running fitbit.py." % name)


CONSUMER_KEY = _required_env("FITBIT_CONSUMER_KEY")
CONSUMER_SECRET = _required_env("FITBIT_CONSUMER_SECRET")
