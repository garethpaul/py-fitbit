#!/usr/bin/env python2
"""Mocked tests for the legacy Fitbit OAuth request path."""

import os
import shutil
try:
    import StringIO
except ImportError:
    import io as StringIO
import stat
import sys
import tempfile
import types
import unittest
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


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

    def __init__(self, body, status=200, read_error=None, close_error=None):
        self.body = body
        self.status = status
        self.read_error = read_error
        self.close_error = close_error
        self.close_calls = 0
        self.__class__.instances.append(self)

    def read(self, size=None):
        self.__class__.read_sizes.append(size)
        if self.read_error is not None:
            raise self.read_error
        return self.body if size is None else self.body[:size]

    def close(self):
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


class FakeHTTPSConnection(object):
    instances = []
    response_bodies = []
    response_statuses = []
    request_error = None
    close_error = None

    def __init__(self, server, *args, **kwargs):
        self.server = server
        self.args = args
        self.kwargs = kwargs
        self.requests = []
        self.debug_levels = []
        self.close_calls = 0
        FakeHTTPSConnection.instances.append(self)

    def set_debuglevel(self, level):
        self.debug_levels.append(level)

    def request(self, method, url, body=None, headers=None):
        if self.__class__.request_error is not None:
            raise self.__class__.request_error
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
        if self.__class__.close_error is not None:
            raise self.__class__.close_error


class FitbitOAuthRequestTest(unittest.TestCase):
    def setUp(self):
        FakeOAuthRequest.created = []
        FakeOAuthToken.parsed_values = []
        FakeHTTPSConnection.instances = []
        FakeHTTPSConnection.response_bodies = ['{"ok": true}']
        FakeHTTPSConnection.response_statuses = []
        FakeHTTPSConnection.request_error = None
        FakeHTTPSConnection.close_error = None
        FakeHTTPResponse.instances = []
        FakeHTTPResponse.read_sizes = []
        self.original_connection = fitbit.httplib.HTTPSConnection
        self.original_read_input = fitbit.read_input
        self.original_cwd = os.getcwd()
        self.tempdir = tempfile.mkdtemp()
        fitbit.httplib.HTTPSConnection = FakeHTTPSConnection
        fitbit.read_input = lambda prompt: 'verifier-code'
        os.chdir(self.tempdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        fitbit.httplib.HTTPSConnection = self.original_connection
        fitbit.read_input = self.original_read_input
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

    def test_protected_resource_path_preserves_valid_encoded_filename(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        fitbit.write_access_token_string(token_string)
        api_call = '/1/user/-/profile%252ejson'

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            data = fitbit.fitbit(api_call)
        finally:
            sys.stdout = original_stdout

        self.assertEqual('{"ok": true}', data)
        self.assertEqual(api_call, FakeOAuthRequest.created[0].http_url)
        self.assertEqual(
            [('GET', api_call, {'Authorization': 'OAuth realm=api.fitbit.com'})],
            FakeHTTPSConnection.instances[0].requests,
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
            '/1/user/-/%252e%252e/profile.json',
            '/1/user/-/%252e/profile.json',
            '/1/user/-/%2e%2e%2fprofile.json',
            '/1/user/-/%252e%252e%252fprofile.json',
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
        self.assertEqual(0o600, mode)
        self.assertEqual(
            'oauth_token=cached&oauth_token_secret=secret',
            fitbit.read_access_token_string(),
        )

    def test_failed_token_cache_write_preserves_last_good_value(self):
        last_good = 'oauth_token=last-good&oauth_token_secret=preserved'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(last_good)
        os.chmod(fitbit.ACCESS_TOKEN_STRING_FNAME, 0o600)

        original_fdopen = fitbit.os.fdopen

        class FailingWriter(object):
            def __init__(self, fd):
                self.fd = fd

            def write(self, _value):
                raise IOError('simulated token-cache write failure')

            def close(self):
                os.close(self.fd)

        try:
            fitbit.os.fdopen = lambda fd, _mode: FailingWriter(fd)
            with self.assertRaises(IOError):
                fitbit.write_access_token_string('replacement-secret')
        finally:
            fitbit.os.fdopen = original_fdopen

        with open(fitbit.ACCESS_TOKEN_STRING_FNAME) as token_file:
            self.assertEqual(last_good, token_file.read())
        self.assertEqual([fitbit.ACCESS_TOKEN_STRING_FNAME], os.listdir('.'))

    def test_token_cache_write_replaces_hard_link_without_modifying_target(self):
        if not hasattr(os, 'link'):
            self.skipTest('hard links are unavailable')

        target = 'linked-token-target.string'
        last_good = 'oauth_token=linked&oauth_token_secret=preserved'
        replacement = 'oauth_token=new&oauth_token_secret=new'
        with open(target, 'w') as token_file:
            token_file.write(last_good)
        os.chmod(target, 0o600)
        os.link(target, fitbit.ACCESS_TOKEN_STRING_FNAME)

        fitbit.write_access_token_string(replacement)

        with open(target) as token_file:
            self.assertEqual(last_good, token_file.read())
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME) as token_file:
            self.assertEqual(replacement, token_file.read())
        self.assertNotEqual(
            os.stat(target).st_ino,
            os.stat(fitbit.ACCESS_TOKEN_STRING_FNAME).st_ino,
        )

    def test_access_token_cache_rejects_symbolic_links(self):
        if not hasattr(os, 'symlink'):
            self.skipTest('symbolic links are unavailable')

        target = 'token-target.string'
        with open(target, 'w') as token_file:
            token_file.write('target-must-remain-unchanged')
        os.chmod(target, 0o600)
        os.symlink(target, fitbit.ACCESS_TOKEN_STRING_FNAME)

        with self.assertRaises(ValueError):
            fitbit.read_access_token_string()
        with self.assertRaises(ValueError):
            fitbit.write_access_token_string('replacement-secret')

        with open(target) as token_file:
            self.assertEqual('target-must-remain-unchanged', token_file.read())

    def test_access_token_cache_rejects_non_regular_files(self):
        if not hasattr(os, 'mkfifo'):
            self.skipTest('FIFOs are unavailable')

        os.mkfifo(fitbit.ACCESS_TOKEN_STRING_FNAME, 0o600)

        for operation in [
            lambda: fitbit.read_access_token_string(),
            lambda: fitbit.write_access_token_string('replacement-secret'),
        ]:
            with self.assertRaises(ValueError) as raised:
                operation()
            self.assertEqual(
                'access token cache must be a regular file',
                str(raised.exception),
            )

    def test_rejects_fifo_access_token_cache_before_network(self):
        if not hasattr(os, 'mkfifo'):
            self.skipTest('FIFOs are unavailable')

        os.mkfifo(fitbit.ACCESS_TOKEN_STRING_FNAME, 0o600)

        with self.assertRaises(ValueError) as raised:
            fitbit.fitbit('/1/user/-/profile.json')

        self.assertEqual(
            'access token cache must be a regular file',
            str(raised.exception),
        )
        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_dangling_access_token_cache_symlink_before_network(self):
        if not hasattr(os, 'symlink'):
            self.skipTest('symbolic links are unavailable')

        os.symlink('missing-token-target.string', fitbit.ACCESS_TOKEN_STRING_FNAME)

        with self.assertRaises(ValueError):
            fitbit.fitbit('/1/user/-/profile.json')

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_readable_access_token_cache_before_network(self):
        token_string = 'oauth_token=cached&oauth_token_secret=secret'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(token_string)
        os.chmod(fitbit.ACCESS_TOKEN_STRING_FNAME, 0o644)

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
        self.assertEqual(0o600, mode)
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

    def test_rejects_malformed_json_without_exposing_body(self):
        fitbit.write_access_token_string(
            'oauth_token=cached&oauth_token_secret=secret'
        )
        FakeHTTPSConnection.response_bodies = ['{"private-health-data":']

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(IOError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIn('invalid JSON', str(raised.exception))
        self.assertNotIn('private-health-data', str(raised.exception))
        self.assertEqual(1, FakeHTTPResponse.instances[0].close_calls)
        self.assertEqual(1, FakeHTTPSConnection.instances[0].close_calls)

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

    def test_rejects_recursively_encoded_credential_query_names(self):
        with self.assertRaises(ValueError):
            fitbit.fitbit('/1/user/-/profile.json?%256fauth_token=secret')

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_encoded_query_delimiters_that_reveal_credentials(self):
        with self.assertRaises(ValueError):
            fitbit.fitbit(
                '/1/user/-/profile.json?safe=x%26oauth_token%3Dsecret'
            )

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_recursively_encoded_backslash_dot_segments(self):
        with self.assertRaises(ValueError):
            fitbit.fitbit('/1/user/%255c..%255cprofile.json')

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_recursively_encoded_authority_like_paths(self):
        with self.assertRaises(ValueError):
            fitbit.fitbit('/%252f%252fevil.example/profile.json')

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_malformed_percent_encoding(self):
        with self.assertRaises(ValueError):
            fitbit.fitbit('/1/user/%2/profile.json')

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_percent_encodes_request_token_in_authorization_url(self):
        request_key = 'request-key&redirect_uri=https://evil.example/'
        request_token = (
            'oauth_token=%s&oauth_token_secret=request-secret' %
            fitbit.quote(request_key, safe='')
        )
        FakeHTTPSConnection.response_bodies = [
            request_token,
            'oauth_token=access-key&oauth_token_secret=access-secret',
            '{"profile": true}',
        ]

        original_stdout = sys.stdout
        try:
            output = StringIO.StringIO()
            sys.stdout = output
            fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        authorization_output = output.getvalue()
        self.assertNotIn('&redirect_uri=https://evil.example/', authorization_output)
        self.assertIn(
            'oauth_token=request-key%26redirect_uri%3Dhttps%3A%2F%2Fevil.example%2F',
            authorization_output,
        )

    def test_response_close_error_does_not_mask_read_failure(self):
        read_error = IOError('primary read failure')
        close_error = IOError('secondary close failure')
        response = FakeHTTPResponse(
            '', read_error=read_error, close_error=close_error
        )

        with self.assertRaises(IOError) as raised:
            fitbit.read_success_response(response, 'read failure test')

        self.assertIs(read_error, raised.exception)
        self.assertEqual(1, response.close_calls)

    def test_connection_close_error_does_not_mask_request_failure(self):
        fitbit.write_access_token_string(
            'oauth_token=cached&oauth_token_secret=secret'
        )
        request_error = IOError('primary request failure')
        FakeHTTPSConnection.request_error = request_error
        FakeHTTPSConnection.close_error = IOError('secondary close failure')

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(IOError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIs(request_error, raised.exception)
        self.assertEqual(1, FakeHTTPSConnection.instances[0].close_calls)

    def test_rejects_oversized_token_cache_before_network_access(self):
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write('x' * (fitbit.MAX_TOKEN_CACHE_BYTES + 1))
        os.chmod(fitbit.ACCESS_TOKEN_STRING_FNAME, 0o600)

        original_fdopen = fitbit.os.fdopen
        fitbit.os.fdopen = lambda _fd, *args: self.fail(
            'oversized token cache must be rejected before reading'
        )
        try:
            with self.assertRaises(IOError):
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            fitbit.os.fdopen = original_fdopen

        self.assertEqual([], FakeOAuthRequest.created)
        self.assertEqual([], FakeHTTPSConnection.instances)

    def test_rejects_token_cache_replaced_between_lstat_and_open(self):
        original_token = 'oauth_token=original&oauth_token_secret=original-secret'
        replacement_token = 'oauth_token=replaced&oauth_token_secret=replaced-secret'
        with open(fitbit.ACCESS_TOKEN_STRING_FNAME, 'w') as token_file:
            token_file.write(original_token)
        os.chmod(fitbit.ACCESS_TOKEN_STRING_FNAME, 0o600)

        original_open = fitbit.os.open
        swapped = [False]

        def swapping_open(path, flags, *args):
            if path == fitbit.ACCESS_TOKEN_STRING_FNAME and not swapped[0]:
                swapped[0] = True
                os.rename(path, path + '.original')
                with open(path, 'w') as token_file:
                    token_file.write(replacement_token)
                os.chmod(path, 0o600)
            return original_open(path, flags, *args)

        fitbit.os.open = swapping_open
        try:
            with self.assertRaises(ValueError):
                fitbit.read_access_token_string()
        finally:
            fitbit.os.open = original_open

    def test_rejects_token_cache_in_shared_writable_directory(self):
        shared_directory = os.path.join(self.tempdir, 'shared')
        os.mkdir(shared_directory)
        os.chmod(shared_directory, 0o777)
        token_path = os.path.join(shared_directory, 'access_token.string')

        with self.assertRaises(ValueError):
            fitbit.write_access_token_string(
                'oauth_token=cached&oauth_token_secret=secret', token_path
            )

        self.assertFalse(os.path.lexists(token_path))

    def test_rejects_malformed_oauth_token_response(self):
        FakeHTTPSConnection.response_bodies = ['oauth_token=request-key']

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(ValueError) as raised:
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertIn('invalid OAuth token response', str(raised.exception))
        self.assertNotIn('request-key', str(raised.exception))
        self.assertEqual([], FakeOAuthToken.parsed_values)

    def test_rejects_control_characters_in_oauth_verifier(self):
        FakeHTTPSConnection.response_bodies = [
            'oauth_token=request-key&oauth_token_secret=request-secret'
        ]
        fitbit.read_input = lambda prompt: 'bad\nverifier'

        original_stdout = sys.stdout
        try:
            sys.stdout = StringIO.StringIO()
            with self.assertRaises(ValueError):
                fitbit.fitbit('/1/user/-/profile.json')
        finally:
            sys.stdout = original_stdout

        self.assertEqual(1, len(FakeOAuthRequest.created))
        self.assertFalse(os.path.exists(fitbit.ACCESS_TOKEN_STRING_FNAME))


if __name__ == '__main__':
    unittest.main()
