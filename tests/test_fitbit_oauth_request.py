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
sys.dont_write_bytecode = True


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
    instances = []
    read_sizes = []

    def __init__(self, body, status=200, read_error=None):
        self.body = body
        self.status = status
        self.read_error = read_error
        self.close_calls = 0
        self.__class__.instances.append(self)

    def read(self, size=None):
        self.__class__.read_sizes.append(size)
        if self.read_error is not None:
            raise self.read_error
        return self.body if size is None else self.body[:size]

    def close(self):
        self.close_calls += 1


class FakeHTTPSConnection(object):
    instances = []
    response_bodies = []
    response_statuses = []

    def __init__(self, server):
        self.server = server
        self.requests = []
        self.debug_levels = []
        self.close_calls = 0
        FakeHTTPSConnection.instances.append(self)

    def set_debuglevel(self, level):
        self.debug_levels.append(level)

    def request(self, method, url, body=None, headers=None):
        self.requests.append((method, url, headers))

    def getresponse(self):
        status = 200
        if FakeHTTPSConnection.response_statuses:
            status = FakeHTTPSConnection.response_statuses.pop(0)
        if FakeHTTPSConnection.response_bodies:
            return FakeHTTPResponse(FakeHTTPSConnection.response_bodies.pop(0), status)
        return FakeHTTPResponse('{"ok": true}', status)

    def close(self):
        self.close_calls += 1


class FitbitOAuthRequestTest(unittest.TestCase):
    def setUp(self):
        FakeOAuthRequest.created = []
        FakeOAuthToken.parsed_values = []
        FakeHTTPSConnection.instances = []
        FakeHTTPSConnection.response_bodies = ['{"ok": true}']
        FakeHTTPSConnection.response_statuses = []
        FakeHTTPResponse.instances = []
        FakeHTTPResponse.read_sizes = []
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
        fitbit.write_access_token_string(token_string)

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
        self.assertEqual(1, connection.close_calls)

    def test_protected_resource_path_is_trimmed(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        fitbit.write_access_token_string(token_string)

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
        fitbit.write_access_token_string(token_string)

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
            '/1/user/-/%2e%2e/profile.json',
            '/1/user/-/%2e/profile.json',
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

    def test_access_token_cache_rejects_symbolic_links(self):
        if not hasattr(os, 'symlink'):
            self.skipTest('symbolic links are unavailable')

        target = 'token-target.string'
        with open(target, 'w') as token_file:
            token_file.write('target-must-remain-unchanged')
        os.chmod(target, 0600)
        os.symlink(target, fitbit.ACCESS_TOKEN_STRING_FNAME)

        with self.assertRaises(ValueError):
            fitbit.read_access_token_string()
        with self.assertRaises(ValueError):
            fitbit.write_access_token_string('replacement-secret')

        with open(target) as token_file:
            self.assertEqual('target-must-remain-unchanged', token_file.read())

    def test_rejects_readable_access_token_cache_before_network(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(token_string)
        os.chmod(fitbit.ACCESS_TOKEN_STRING_FNAME, 0644)

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(ValueError):
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_request_token_flow_writes_owner_only_access_token_cache(self):
        request_secret = 'request-secret-must-not-be-logged'
        access_secret = 'access-secret-must-not-be-logged'
        request_token = 'oauth_token=request-key&oauth_token_secret=%s' % request_secret
        access_token = 'oauth_token=access-key&oauth_token_secret=%s' % access_secret
        FakeHTTPSConnection.response_bodies = [
            request_token,
            access_token,
            '{"profile": true}',
        ]

        original_stdout = sys.stdout
        try:
            output = StringIO.StringIO()
            sys.stdout = output
            data = fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertEqual('{"profile": true}', data)
        console_output = output.getvalue()
        self.assertNotIn(request_secret, console_output)
        self.assertNotIn(access_secret, console_output)
        self.assertNotIn(request_token, console_output)
        self.assertNotIn(access_token, console_output)
        self.assertIn('Authorization URL:', console_output)
        self.assertIn('oauth_token=request-key', console_output)
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
        self.assertEqual(1, connection.close_calls)

    def test_debug_output_omits_signed_url_and_response_body(self):
        signed_url_secret = 'signed-url-secret-must-not-be-logged'
        response_secret = 'response-secret-must-not-be-logged'
        oauth_request = FakeOAuthRequest(
            FakeOAuthConsumer('consumer', 'secret'),
            http_url='https://api.fitbit.com/oauth/request_token?oauth_signature=%s' %
            signed_url_secret,
        )
        FakeHTTPSConnection.response_bodies = [
            'oauth_token=request-key&oauth_token_secret=%s' % response_secret,
        ]
        connection = FakeHTTPSConnection(fitbit.SERVER)

        original_stdout = sys.stdout
        try:
            output = StringIO.StringIO()
            sys.stdout = output
            response = fitbit.fetch_response(oauth_request, connection, debug=True)
        finally:
            sys.stdout = original_stdout

        console_output = output.getvalue()
        self.assertIn('OAuth request method: GET', console_output)
        self.assertIn('OAuth response status: 200', console_output)
        self.assertIn('OAuth response bytes: %s' % len(response), console_output)
        self.assertNotIn(signed_url_secret, console_output)
        self.assertNotIn(response_secret, console_output)
        self.assertNotIn(oauth_request.http_url, console_output)
        self.assertNotIn(response, console_output)

    def test_debug_mode_does_not_enable_transport_trace_or_log_secrets(self):
        request_secret = 'debug-request-secret-must-not-be-logged'
        access_secret = 'debug-access-secret-must-not-be-logged'
        FakeHTTPSConnection.response_bodies = [
            'oauth_token=request-key&oauth_token_secret=%s' % request_secret,
            'oauth_token=access-key&oauth_token_secret=%s' % access_secret,
            '{"profile": true}',
        ]

        original_debug = fitbit.DEBUG
        original_stdout = sys.stdout
        try:
            fitbit.DEBUG = True
            output = StringIO.StringIO()
            sys.stdout = output
            data = fitbit.fitbit('/1/user/-/profile.json')
        finally:
            fitbit.DEBUG = original_debug
            sys.stdout = original_stdout

        console_output = output.getvalue()
        self.assertEqual('{"profile": true}', data)
        self.assertNotIn(request_secret, console_output)
        self.assertNotIn(access_secret, console_output)
        self.assertEqual(2, console_output.count('OAuth request method: GET'))
        self.assertEqual(2, console_output.count('OAuth response status: 200'))
        self.assertEqual([], FakeHTTPSConnection.instances[0].debug_levels)

    def test_rejects_failed_oauth_token_responses(self):
        FakeHTTPSConnection.response_bodies = ['temporarily unavailable']
        FakeHTTPSConnection.response_statuses = [503]

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(IOError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIn('OAuth request failed with HTTP status 503', str(raised.exception))
        self.assertFalse(os.path.exists(fitbit.ACCESS_TOKEN_STRING_FNAME))
        self.assertEqual([], FakeOAuthToken.parsed_values)
        self.assertEqual(1, FakeHTTPResponse.instances[0].close_calls)
        self.assertEqual(1, FakeHTTPSConnection.instances[0].close_calls)

    def test_rejects_failed_protected_resource_responses(self):
        fitbit.write_access_token_string('oauth_token=cached&oauth_token_secret=secret')
        FakeHTTPSConnection.response_bodies = ['not authorized']
        FakeHTTPSConnection.response_statuses = [401]

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(IOError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIn(
            'protected resource request failed with HTTP status 401',
            str(raised.exception),
        )
        self.assertNotIn('not authorized', str(raised.exception))
        self.assertEqual(1, FakeHTTPResponse.instances[0].close_calls)
        self.assertEqual(1, FakeHTTPSConnection.instances[0].close_calls)

    def test_rejects_oversized_oauth_token_responses(self):
        oversized = 'oauth_token=secret&' + ('x' * fitbit.MAX_RESPONSE_BODY_BYTES)
        FakeHTTPSConnection.response_bodies = [oversized]

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(IOError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIn('OAuth request response exceeds', str(raised.exception))
        self.assertNotIn('oauth_token=secret', str(raised.exception))
        self.assertEqual([fitbit.MAX_RESPONSE_BODY_BYTES + 1], FakeHTTPResponse.read_sizes)
        self.assertEqual([], FakeOAuthToken.parsed_values)
        self.assertFalse(os.path.exists(fitbit.ACCESS_TOKEN_STRING_FNAME))
        self.assertEqual(1, FakeHTTPResponse.instances[0].close_calls)

    def test_rejects_oversized_protected_resource_responses(self):
        fitbit.write_access_token_string('oauth_token=cached&oauth_token_secret=secret')
        oversized = 'private-health-data:' + ('x' * fitbit.MAX_RESPONSE_BODY_BYTES)
        FakeHTTPSConnection.response_bodies = [oversized]

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(IOError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIn('protected resource request response exceeds', str(raised.exception))
        self.assertNotIn('private-health-data', str(raised.exception))
        self.assertEqual([fitbit.MAX_RESPONSE_BODY_BYTES + 1], FakeHTTPResponse.read_sizes)
        self.assertEqual(1, FakeHTTPResponse.instances[0].close_calls)

    def test_accepts_response_at_size_limit(self):
        body = 'x' * fitbit.MAX_RESPONSE_BODY_BYTES
        response = FakeHTTPResponse(body)

        self.assertEqual(body, fitbit.read_success_response(response, 'boundary test'))
        self.assertEqual([fitbit.MAX_RESPONSE_BODY_BYTES + 1], FakeHTTPResponse.read_sizes)
        self.assertEqual(1, response.close_calls)

    def test_closes_response_when_read_fails(self):
        read_error = IOError('fixture read failure')
        response = FakeHTTPResponse('', read_error=read_error)

        with self.assertRaises(IOError) as raised:
            fitbit.read_success_response(response, 'read failure test')

        self.assertIs(read_error, raised.exception)
        self.assertEqual(1, response.close_calls)

    def test_oauth_endpoints_use_https(self):
        self.assertEqual('https://api.fitbit.com/oauth/request_token', fitbit.REQUEST_TOKEN_URL)
        self.assertEqual('https://api.fitbit.com/oauth/access_token', fitbit.ACCESS_TOKEN_URL)
        self.assertEqual('https://api.fitbit.com/oauth/authorize', fitbit.AUTHORIZATION_URL)


if __name__ == '__main__':
    unittest.main()
