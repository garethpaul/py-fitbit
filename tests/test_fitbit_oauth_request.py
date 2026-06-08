#!/usr/bin/env python2
"""Mocked tests for the legacy Fitbit OAuth request path."""

import os
import shutil
import StringIO
import sys
import tempfile
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class FakeOAuthConsumer(object):
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


class FakeOAuthSignatureMethodPlaintext(object):
    pass


class FakeOAuthToken(object):
    parsed_values = []

    def __init__(self, key='access-key', secret='access-secret'):
        self.key = key
        self.secret = secret

    @classmethod
    def from_string(cls, token_string):
        cls.parsed_values.append(token_string)
        return cls()

    def to_string(self):
        return 'oauth_token=%s&oauth_token_secret=%s' % (self.key, self.secret)


class FakeOAuthRequest(object):
    created = []

    def __init__(self, consumer, token=None, http_url=None, parameters=None):
        self.consumer = consumer
        self.token = token
        self.http_url = http_url
        self.parameters = parameters or {}
        self.signed_with = None

    @classmethod
    def from_consumer_and_token(cls, consumer, token=None, http_url=None, parameters=None):
        request = cls(consumer, token=token, http_url=http_url, parameters=parameters)
        cls.created.append(request)
        return request

    def sign_request(self, signature_method, consumer, token):
        self.signed_with = (signature_method, consumer, token)

    def to_header(self, realm=None):
        return {'Authorization': 'OAuth realm=%s' % realm}

    def to_url(self):
        return self.http_url


def install_stub_modules():
    settings = types.ModuleType('settings')
    settings.CONSUMER_KEY = 'test-consumer-key'
    settings.CONSUMER_SECRET = 'test-consumer-secret'

    oauth_package = types.ModuleType('oauth')
    oauth_module = types.ModuleType('oauth.oauth')
    oauth_module.OAuthConsumer = FakeOAuthConsumer
    oauth_module.OAuthSignatureMethod_PLAINTEXT = FakeOAuthSignatureMethodPlaintext
    oauth_module.OAuthToken = FakeOAuthToken
    oauth_module.OAuthRequest = FakeOAuthRequest
    oauth_package.oauth = oauth_module

    sys.modules['settings'] = settings
    sys.modules['oauth'] = oauth_package
    sys.modules['oauth.oauth'] = oauth_module


install_stub_modules()
import fitbit


class FakeHTTPResponse(object):
    def read(self):
        return '{"ok": true}'


class FakeHTTPSConnection(object):
    instances = []

    def __init__(self, server):
        self.server = server
        self.requests = []
        FakeHTTPSConnection.instances.append(self)

    def request(self, method, url, body=None, headers=None):
        self.requests.append((method, url, headers))

    def getresponse(self):
        return FakeHTTPResponse()


class FitbitOAuthRequestTest(unittest.TestCase):
    def setUp(self):
        FakeOAuthRequest.created = []
        FakeOAuthToken.parsed_values = []
        FakeHTTPSConnection.instances = []
        self.original_connection = fitbit.httplib.HTTPSConnection
        self.original_cwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        fitbit.httplib.HTTPSConnection = FakeHTTPSConnection
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        fitbit.httplib.HTTPSConnection = self.original_connection
        shutil.rmtree(self.tempdir)

    def test_cached_access_token_signs_protected_resource_request(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(token_string)

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            data = fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertEqual('{"ok": true}', data)
        self.assertEqual([token_string], FakeOAuthToken.parsed_values)
        self.assertEqual(1, len(FakeOAuthRequest.created))

        oauth_request = FakeOAuthRequest.created[0]
        self.assertEqual('/1/user/-/profile.json', oauth_request.http_url)
        self.assertEqual('test-consumer-key', oauth_request.consumer.key)
        self.assertIsNotNone(oauth_request.signed_with)
        signature_method, signed_consumer, signed_token = oauth_request.signed_with
        self.assertIsInstance(signature_method, FakeOAuthSignatureMethodPlaintext)
        self.assertEqual(oauth_request.consumer, signed_consumer)
        self.assertEqual(oauth_request.token, signed_token)

        self.assertEqual(1, len(FakeHTTPSConnection.instances))
        connection = FakeHTTPSConnection.instances[0]
        self.assertEqual(fitbit.SERVER, connection.server)
        self.assertEqual(
            [('GET', '/1/user/-/profile.json', {'Authorization': 'OAuth realm=api.fitbit.com'})],
            connection.requests,
        )


if __name__ == '__main__':
    unittest.main()
