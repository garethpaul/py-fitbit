#!/usr/bin/env python2
"""Mocked tests for the legacy Fitbit OAuth request path."""

import os
import shutil
import StringIO
import stat
import sys
import tempfile
import types
import unittest
import urlparse


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
        values = dict(urlparse.parse_qsl(token_string))
        return cls(
            values.get('oauth_token', 'access-key'),
            values.get('oauth_token_secret', 'access-secret'),
        )

    def to_string(self):
        return 'oauth_token=%s&oauth_token_secret=%s' % (self.key, self.secret)


class FakeOAuthRequest(object):
    created = []

    def __init__(self, consumer, token=None, http_url=None, parameters=None):
        self.consumer = consumer
        self.token = token
        self.http_url = http_url
        self.parameters = parameters or {}
        self.http_method = 'GET'
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
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body


class FakeHTTPSConnection(object):
    instances = []
    response_bodies = []

    def __init__(self, server):
        self.server = server
        self.requests = []
        FakeHTTPSConnection.instances.append(self)

    def request(self, method, url, body=None, headers=None):
        self.requests.append((method, url, headers))

    def getresponse(self):
        if FakeHTTPSConnection.response_bodies:
            return FakeHTTPResponse(FakeHTTPSConnection.response_bodies.pop(0))
        return FakeHTTPResponse('{"ok": true}')


class FitbitOAuthRequestTest(unittest.TestCase):
    def setUp(self):
        FakeOAuthRequest.created = []
        FakeOAuthToken.parsed_values = []
        FakeHTTPSConnection.instances = []
        FakeHTTPSConnection.response_bodies = ['{"ok": true}']
        self.original_connection = fitbit.httplib.HTTPSConnection
        self.original_raw_input = getattr(fitbit, 'raw_input', None)
        self.original_cwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        fitbit.httplib.HTTPSConnection = FakeHTTPSConnection
        fitbit.raw_input = lambda prompt: 'verifier-code'
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        fitbit.httplib.HTTPSConnection = self.original_connection
        if self.original_raw_input is None:
            delattr(fitbit, 'raw_input')
        else:
            fitbit.raw_input = self.original_raw_input
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

    def test_protected_resource_path_is_trimmed(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(token_string)

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            data = fitbit.fitbit(' /1/user/-/profile.json ')
        finally:
            sys.stdout = original_stdout

        self.assertEqual('{"ok": true}', data)
        self.assertEqual(1, len(FakeOAuthRequest.created))
        self.assertEqual('/1/user/-/profile.json', FakeOAuthRequest.created[0].http_url)
        self.assertEqual(1, len(FakeHTTPSConnection.instances))
        connection = FakeHTTPSConnection.instances[0]
        self.assertEqual(
            [('GET', '/1/user/-/profile.json', {'Authorization': 'OAuth realm=api.fitbit.com'})],
            connection.requests,
        )

    def test_protected_resource_path_preserves_non_secret_query(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(token_string)

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            data = fitbit.fitbit('/1/user/-/profile.json?limit=1')
        finally:
            sys.stdout = original_stdout

        self.assertEqual('{"ok": true}', data)
        self.assertEqual(1, len(FakeOAuthRequest.created))
        self.assertEqual(
            '/1/user/-/profile.json?limit=1',
            FakeOAuthRequest.created[0].http_url,
        )
        self.assertEqual(1, len(FakeHTTPSConnection.instances))
        connection = FakeHTTPSConnection.instances[0]
        self.assertEqual(
            [('GET', '/1/user/-/profile.json?limit=1', {'Authorization': 'OAuth realm=api.fitbit.com'})],
            connection.requests,
        )

    def test_rejects_non_api_paths_before_network(self):
        invalid_api_calls = [
            '1/user/-/profile.json',
            'http://example.test/1/user/-/profile.json',
            '//example.test/1/user/-/profile.json',
            '/1/user/-/profile json',
            '/1/user/-/profile.json\nHost: example.test',
            '/1/user/-/profile.json#access-token',
            '/1/user/-/profile.json?oauth_token=secret',
            '/1/user/-/profile.json?access_token=secret',
            '/1/user/-/profile.json?client_secret=secret',
            '/1/user/-/../profile.json',
            '/1/user/-/./profile.json',
            None,
        ]

        for api_call in invalid_api_calls:
            with self.assertRaises(ValueError):
                fitbit.fitbit(api_call)

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_access_token_cache_uses_owner_only_permissions(self):
        fitbit.write_access_token_string('oauth_token=cached&oauth_token_secret=secret')

        mode = stat.S_IMODE(os.stat(fitbit.ACCESS_TOKEN_STRING_FNAME).st_mode)
        self.assertEqual(0600, mode)
        self.assertEqual(
            'oauth_token=cached&oauth_token_secret=secret',
            fitbit.read_access_token_string(),
        )

    def test_request_token_flow_writes_owner_only_access_token_cache(self):
        request_token = 'oauth_token=request-key&oauth_token_secret=request-secret'
        access_token = 'oauth_token=access-key&oauth_token_secret=access-secret'
        FakeHTTPSConnection.response_bodies = [
            request_token,
            access_token,
            '{"profile": true}',
        ]

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            data = fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertEqual('{"profile": true}', data)
        self.assertEqual([request_token, access_token], FakeOAuthToken.parsed_values)
        self.assertEqual(3, len(FakeOAuthRequest.created))

        request_token_request = FakeOAuthRequest.created[0]
        self.assertEqual(fitbit.REQUEST_TOKEN_URL, request_token_request.http_url)
        self.assertIsNone(request_token_request.token)

        access_token_request = FakeOAuthRequest.created[1]
        self.assertEqual(fitbit.ACCESS_TOKEN_URL, access_token_request.http_url)
        self.assertEqual('request-key', access_token_request.token.key)
        self.assertEqual({'oauth_verifier': 'verifier-code'}, access_token_request.parameters)

        protected_resource_request = FakeOAuthRequest.created[2]
        self.assertEqual('/1/user/-/profile.json', protected_resource_request.http_url)
        self.assertEqual('access-key', protected_resource_request.token.key)

        mode = stat.S_IMODE(os.stat(fitbit.ACCESS_TOKEN_STRING_FNAME).st_mode)
        self.assertEqual(0600, mode)
        self.assertEqual(access_token, fitbit.read_access_token_string())

        self.assertEqual(1, len(FakeHTTPSConnection.instances))
        connection = FakeHTTPSConnection.instances[0]
        self.assertEqual([
            ('GET', fitbit.REQUEST_TOKEN_URL, None),
            ('GET', fitbit.ACCESS_TOKEN_URL, None),
            ('GET', '/1/user/-/profile.json', {'Authorization': 'OAuth realm=api.fitbit.com'}),
        ], connection.requests)

    def test_oauth_endpoints_use_https(self):
        self.assertEqual('https://api.fitbit.com/oauth/request_token', fitbit.REQUEST_TOKEN_URL)
        self.assertEqual('https://api.fitbit.com/oauth/access_token', fitbit.ACCESS_TOKEN_URL)
        self.assertEqual('https://api.fitbit.com/oauth/authorize', fitbit.AUTHORIZATION_URL)


if __name__ == '__main__':
    unittest.main()
