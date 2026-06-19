"""
Secret-free Fitbit API configuration.

Set the required values in the environment before running fitbit.py:

    FITBIT_CONSUMER_KEY
    FITBIT_CONSUMER_SECRET
"""
import os
import re


_COMMON_PLACEHOLDERS = ("changeme", "replaceme")
_NAMED_PLACEHOLDERS = {
    "FITBIT_CONSUMER_KEY": (
        "yourfitbitconsumerkey",
        "consumerkey",
        "examplekey",
    ),
    "FITBIT_CONSUMER_SECRET": (
        "yourfitbitconsumersecret",
        "consumersecret",
        "examplesecret",
    ),
}


def _is_placeholder(name, value):
    normalized = re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    return normalized in _COMMON_PLACEHOLDERS + _NAMED_PLACEHOLDERS[name]


def _required_env(name):
    value = os.environ.get(name)
    if value and value.strip() and not _is_placeholder(name, value):
        return value
    raise RuntimeError(
        "Missing required environment variable %s. Set Fitbit OAuth "
        "credentials in the environment before running fitbit.py." % name)


CONSUMER_KEY = _required_env("FITBIT_CONSUMER_KEY")
CONSUMER_SECRET = _required_env("FITBIT_CONSUMER_SECRET")
