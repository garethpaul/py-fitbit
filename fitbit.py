"""
A Python library for accessing the FitBit API.
"""
from __future__ import print_function

import errno, os, re, stat, sys, tempfile
try:
   import httplib
except ImportError:
   import http.client as httplib
try:
   import urlparse
except ImportError:
   import urllib.parse as urlparse
from oauth import oauth 
import json
import settings

try:
   string_types = (basestring,)
except NameError:
   string_types = (str,)

try:
   read_input = raw_input
except NameError:
   read_input = input

CONSUMER_KEY    = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET
SERVER = 'api.fitbit.com'
REQUEST_TOKEN_URL = 'https://%s/oauth/request_token' % SERVER
ACCESS_TOKEN_URL = 'https://%s/oauth/access_token' % SERVER
AUTHORIZATION_URL = 'https://%s/oauth/authorize' % SERVER
ACCESS_TOKEN_STRING_FNAME = 'access_token.string'
DEBUG = False
MAX_RESPONSE_BODY_BYTES = 1 << 20
MAX_TOKEN_CACHE_BYTES = 1 << 14
MAX_OAUTH_VALUE_BYTES = 1 << 12
MAX_PERCENT_DECODE_LAYERS = 8
HTTPS_TIMEOUT_SECONDS = 30
CREDENTIAL_QUERY_PARAMETERS = set([
   'access_token',
   'client_secret',
   'consumer_secret',
   'oauth_signature',
   'oauth_token',
   'oauth_verifier',
])


def token_cache_flags(flags):
   if hasattr(os, 'O_NOFOLLOW'):
      flags |= os.O_NOFOLLOW
   if hasattr(os, 'O_NONBLOCK'):
      flags |= os.O_NONBLOCK
   return flags


def has_control_characters(value):
   return any(ord(char) < 32 or ord(char) == 127 for char in value)


def strict_percent_decode(value):
   if re.search(r'%(?![0-9A-Fa-f]{2})', value):
      raise ValueError('invalid percent encoding')
   return urlparse.unquote(value)


def decoded_layers(value):
   for _layer in range(MAX_PERCENT_DECODE_LAYERS):
      yield value
      decoded_value = strict_percent_decode(value)
      if decoded_value == value:
         return
      value = decoded_value
   raise ValueError('too many percent-encoding layers')


def token_cache_path_state(fname):
   try:
      path_stat = os.lstat(fname)
   except OSError as error:
      if error.errno == errno.ENOENT:
         return None
      raise
   if stat.S_ISLNK(path_stat.st_mode):
      raise ValueError('access token cache must not be a symbolic link')
   if not stat.S_ISREG(path_stat.st_mode):
      raise ValueError('access token cache must be a regular file')
   return path_stat


def reject_unsafe_token_cache_path(fname):
   return token_cache_path_state(fname)


def validate_token_cache_directory(fname):
   cache_directory = os.path.dirname(os.path.abspath(fname))
   directory_stat = os.lstat(cache_directory)
   if stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(directory_stat.st_mode):
      raise ValueError('access token cache directory must be a real directory')
   if stat.S_IMODE(directory_stat.st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
      raise ValueError('access token cache directory must not be shared-writable')
   if hasattr(os, 'getuid') and directory_stat.st_uid != os.getuid():
      raise ValueError('access token cache directory must be owned by the current user')
   return cache_directory


def token_cache_descriptor_mode(fd):
   mode = os.fstat(fd).st_mode
   if not stat.S_ISREG(mode):
      raise ValueError('access token cache must be a regular file')
   return stat.S_IMODE(mode)


def same_file_identity(path_stat, descriptor_stat):
   return (
      path_stat is not None and
      path_stat.st_dev == descriptor_stat.st_dev and
      path_stat.st_ino == descriptor_stat.st_ino
   )


def contains_dot_path_segment(path):
   for decoded_path in decoded_layers(path):
      normalized_path = decoded_path.replace('\\', '/')
      if normalized_path.startswith('//') or '://' in normalized_path:
         return True
      if any(segment in ('.', '..') for segment in normalized_path.split('/')):
         return True
   return False


def validate_oauth_value(value, label):
   if (not isinstance(value, string_types) or not value or
         len(value) > MAX_OAUTH_VALUE_BYTES or has_control_characters(value)):
      raise ValueError('invalid %s' % label)
   return value


def parse_oauth_token(token_string):
   if (not isinstance(token_string, string_types) or
         len(token_string) > MAX_TOKEN_CACHE_BYTES or
         has_control_characters(token_string)):
      raise ValueError('invalid OAuth token response')
   strict_percent_decode(token_string)
   try:
      pairs = urlparse.parse_qsl(
         token_string, keep_blank_values=True, strict_parsing=True)
   except ValueError:
      raise ValueError('invalid OAuth token response')
   values = {}
   for name, value in pairs:
      if name in values:
         raise ValueError('invalid OAuth token response')
      values[name] = value
   for required_name in ('oauth_token', 'oauth_token_secret'):
      if required_name not in values:
         raise ValueError('invalid OAuth token response')
      validate_oauth_value(values[required_name], 'OAuth token response')
   return oauth.OAuthToken.from_string(token_string)


def close_preserving_primary_error(resource):
   primary_error_active = sys.exc_info()[0] is not None
   try:
      resource.close()
   except Exception:
      if not primary_error_active:
         raise


def close_fd_preserving_primary_error(fd):
   primary_error_active = sys.exc_info()[0] is not None
   try:
      os.close(fd)
   except Exception:
      if not primary_error_active:
         raise


def validate_json_response(body):
   try:
      json.loads(body)
   except (TypeError, ValueError, RuntimeError):
      raise IOError('Fitbit protected resource returned invalid JSON')


def read_access_token_string(fname=ACCESS_TOKEN_STRING_FNAME):
   validate_token_cache_directory(fname)
   path_stat = reject_unsafe_token_cache_path(fname)
   try:
      fd = os.open(fname, token_cache_flags(os.O_RDONLY))
   except OSError:
      reject_unsafe_token_cache_path(fname)
      raise
   try:
      mode = token_cache_descriptor_mode(fd)
      descriptor_stat = os.fstat(fd)
      if not same_file_identity(path_stat, descriptor_stat):
         raise ValueError('access token cache changed before it could be opened')
      if mode & (stat.S_IRWXG | stat.S_IRWXO):
         raise ValueError('access token cache must be owner-only')
      if descriptor_stat.st_size > MAX_TOKEN_CACHE_BYTES:
         raise IOError('access token cache exceeds size limit')
      fobj = os.fdopen(fd)
      fd = None
      try:
         token_string = fobj.read(MAX_TOKEN_CACHE_BYTES + 1)
         if len(token_string) > MAX_TOKEN_CACHE_BYTES:
            raise IOError('access token cache exceeds size limit')
         return token_string
      finally:
         close_preserving_primary_error(fobj)
   finally:
      if fd is not None:
         close_fd_preserving_primary_error(fd)


def write_access_token_string(access_token_string, fname=ACCESS_TOKEN_STRING_FNAME):
   if (not isinstance(access_token_string, string_types) or
         len(access_token_string) > MAX_TOKEN_CACHE_BYTES):
      raise ValueError('access token cache value is invalid')
   original_path_stat = reject_unsafe_token_cache_path(fname)
   cache_directory = validate_token_cache_directory(fname)
   cache_prefix = '.%s.' % os.path.basename(fname)
   fd, staged_fname = tempfile.mkstemp(prefix=cache_prefix, dir=cache_directory)
   fobj = None
   try:
      token_cache_descriptor_mode(fd)
      if hasattr(os, 'fchmod'):
         os.fchmod(fd, 0o600)
      else:
         os.chmod(staged_fname, 0o600)
      fobj = os.fdopen(fd, 'w')
      fd = None
      try:
         fobj.write(access_token_string)
         fobj.flush()
         os.fsync(fobj.fileno())
      finally:
         try:
            fobj.close()
         finally:
            fobj = None

      current_path_stat = reject_unsafe_token_cache_path(fname)
      if original_path_stat is None:
         if current_path_stat is not None:
            raise ValueError('access token cache changed during publication')
      elif current_path_stat is None or not same_file_identity(
            original_path_stat, current_path_stat):
         raise ValueError('access token cache changed during publication')
      os.rename(staged_fname, fname)
      staged_fname = None
      if hasattr(os, 'O_DIRECTORY'):
         directory_fd = os.open(cache_directory, os.O_RDONLY | os.O_DIRECTORY)
         try:
            os.fsync(directory_fd)
         finally:
            os.close(directory_fd)
   finally:
      if fobj is not None:
         fobj.close()
      if fd is not None:
         os.close(fd)
      if staged_fname is not None:
         try:
            os.unlink(staged_fname)
         except OSError as error:
            if error.errno != errno.ENOENT:
               raise


def validate_api_call(api_call):
   if not isinstance(api_call, string_types):
      raise ValueError('api_call must be a Fitbit API path')

   api_call = api_call.strip()
   if (not api_call.startswith('/') or api_call.startswith('//') or
         '://' in api_call):
      raise ValueError('api_call must be a Fitbit API path')

   if any(char.isspace() for char in api_call) or has_control_characters(api_call):
      raise ValueError('api_call must not contain whitespace')

   if '#' in api_call:
      raise ValueError('api_call must not contain a fragment')

   split_call = urlparse.urlsplit(api_call)
   if contains_dot_path_segment(split_call.path):
      raise ValueError('api_call must not contain dot segments')

   for query_layer in decoded_layers(split_call.query):
      for name, _value in urlparse.parse_qsl(
            query_layer, keep_blank_values=True):
         for decoded_name in decoded_layers(name):
            if decoded_name.lower() in CREDENTIAL_QUERY_PARAMETERS:
               raise ValueError(
                  'api_call must not contain credential query parameters')

   return api_call


def fetch_response(oauth_request, connection, debug=DEBUG):
   url= oauth_request.to_url()
   connection.request(oauth_request.http_method,url)
   response = connection.getresponse()
   s=read_success_response(response, 'OAuth request')
   if debug:
      print('OAuth request method: %s' % oauth_request.http_method)
      print('OAuth response status: %s' % response.status)
      print('OAuth response bytes: %s' % len(s))
   return s


def read_success_response(response, operation):
   try:
      body = response.read(MAX_RESPONSE_BODY_BYTES + 1)
      status = getattr(response, 'status', None)
      if status is None or status < 200 or status >= 300:
         raise IOError('Fitbit %s failed with HTTP status %s' % (operation, status))
      if len(body) > MAX_RESPONSE_BODY_BYTES:
         raise IOError(
            'Fitbit %s response exceeds %s bytes' %
            (operation, MAX_RESPONSE_BODY_BYTES))
      return body
   finally:
      close_preserving_primary_error(response)


def fitbit(api_call):
   api_call = validate_api_call(api_call)
   consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
   signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
   connection = None
   try:
      # if local does not exist
      if not os.path.lexists(ACCESS_TOKEN_STRING_FNAME):
         connection = httplib.HTTPSConnection(SERVER, timeout=HTTPS_TIMEOUT_SECONDS)
         # obtain token to get request
         print('* Obtain a request token ...')
         oauth_request = oauth.OAuthRequest.from_consumer_and_token(
               consumer, http_url=REQUEST_TOKEN_URL)
         oauth_request.sign_request(signature_method, consumer, None)
         resp=fetch_response(oauth_request, connection, debug=DEBUG)
         auth_token=parse_oauth_token(resp)

         # authorize the request token
         print('* Authorize the request token ...')
         auth_url="%s?oauth_token=%s" % (
            AUTHORIZATION_URL, urlparse.quote(auth_token.key, safe=''))
         print('Authorization URL:\n%s' % auth_url)
         oauth_verifier = read_input(
            'Please go to the above URL and authorize the '+
            'app -- Type in the Verification code from the website, when done: ')
         validate_oauth_value(oauth_verifier, 'OAuth verifier')
         print('* Obtain an access token ...')
         # note that the token we're passing to the new
         # OAuthRequest is our current request token
         oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=auth_token, http_url=ACCESS_TOKEN_URL,
            parameters={'oauth_verifier': oauth_verifier})
         oauth_request.sign_request(signature_method, consumer, auth_token)

         # now the token we get back is an access token
         # parse the response into an OAuthToken object
         access_token=parse_oauth_token(
            fetch_response(oauth_request, connection, debug=DEBUG))

         # write the access token to file; next time we just read it from file
         if DEBUG:
            print('Writing file', ACCESS_TOKEN_STRING_FNAME)
         access_token_string = access_token.to_string()
         write_access_token_string(access_token_string)

      else:
         if DEBUG:
            print('Reading file', ACCESS_TOKEN_STRING_FNAME)
         access_token_string = read_access_token_string()

         access_token = parse_oauth_token(access_token_string)
         connection = httplib.HTTPSConnection(SERVER, timeout=HTTPS_TIMEOUT_SECONDS)

      # access protected resource
      print('* Access a protected resource ...')
      oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
         token=access_token, http_url=api_call)
      oauth_request.sign_request(signature_method, consumer, access_token)
      headers = oauth_request.to_header(realm='api.fitbit.com')
      connection.request('GET', api_call, headers=headers)
      resp = connection.getresponse()
      data = read_success_response(resp, 'protected resource request')
      if urlparse.urlsplit(api_call).path.lower().endswith('.json'):
         validate_json_response(data)
      return data
   finally:
      if connection is not None:
         close_preserving_primary_error(connection)

if __name__ == '__main__':
   print(json.loads(fitbit('/1/user/-/sleep/date/2013-08-31.json')))
