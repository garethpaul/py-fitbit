"""
A Python library for accessing the FitBit API.
"""
import errno, os, httplib, stat, tempfile
import urlparse
from oauth import oauth 
import json
import settings

CONSUMER_KEY    = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET
SERVER = 'api.fitbit.com'
REQUEST_TOKEN_URL = 'https://%s/oauth/request_token' % SERVER
ACCESS_TOKEN_URL = 'https://%s/oauth/access_token' % SERVER
AUTHORIZATION_URL = 'https://%s/oauth/authorize' % SERVER
ACCESS_TOKEN_STRING_FNAME = 'access_token.string'
DEBUG = False
MAX_RESPONSE_BODY_BYTES = 1 << 20
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


def reject_unsafe_token_cache_path(fname):
   try:
      mode = os.lstat(fname).st_mode
      if stat.S_ISLNK(mode):
         raise ValueError('access token cache must not be a symbolic link')
      if not stat.S_ISREG(mode):
         raise ValueError('access token cache must be a regular file')
   except OSError as error:
      if error.errno != errno.ENOENT:
         raise


def token_cache_descriptor_mode(fd):
   mode = os.fstat(fd).st_mode
   if not stat.S_ISREG(mode):
      raise ValueError('access token cache must be a regular file')
   return stat.S_IMODE(mode)


def read_access_token_string(fname=ACCESS_TOKEN_STRING_FNAME):
   reject_unsafe_token_cache_path(fname)
   try:
      fd = os.open(fname, token_cache_flags(os.O_RDONLY))
   except OSError:
      reject_unsafe_token_cache_path(fname)
      raise
   try:
      mode = token_cache_descriptor_mode(fd)
      if mode & (stat.S_IRWXG | stat.S_IRWXO):
         raise ValueError('access token cache must be owner-only')
      fobj = os.fdopen(fd)
      fd = None
      try:
         return fobj.read()
      finally:
         fobj.close()
   finally:
      if fd is not None:
         os.close(fd)


def write_access_token_string(access_token_string, fname=ACCESS_TOKEN_STRING_FNAME):
   reject_unsafe_token_cache_path(fname)
   cache_directory = os.path.dirname(os.path.abspath(fname))
   cache_prefix = '.%s.' % os.path.basename(fname)
   fd, staged_fname = tempfile.mkstemp(prefix=cache_prefix, dir=cache_directory)
   fobj = None
   try:
      token_cache_descriptor_mode(fd)
      if hasattr(os, 'fchmod'):
         os.fchmod(fd, 0600)
      else:
         os.chmod(staged_fname, 0600)
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

      reject_unsafe_token_cache_path(fname)
      os.rename(staged_fname, fname)
      staged_fname = None
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
   if not isinstance(api_call, basestring):
      raise ValueError('api_call must be a Fitbit API path')

   api_call = api_call.strip()
   if (not api_call.startswith('/') or api_call.startswith('//') or
         '://' in api_call):
      raise ValueError('api_call must be a Fitbit API path')

   if any(char.isspace() for char in api_call):
      raise ValueError('api_call must not contain whitespace')

   if '#' in api_call:
      raise ValueError('api_call must not contain a fragment')

   path_segments = urlparse.urlsplit(api_call).path.split('/')
   if any(urlparse.unquote(segment) in ('.', '..') for segment in path_segments):
      raise ValueError('api_call must not contain dot segments')

   for name, _value in urlparse.parse_qsl(
         urlparse.urlsplit(api_call).query, keep_blank_values=True):
      if name.lower() in CREDENTIAL_QUERY_PARAMETERS:
         raise ValueError('api_call must not contain credential query parameters')

   return api_call


def fetch_response(oauth_request, connection, debug=DEBUG):
   url= oauth_request.to_url()
   connection.request(oauth_request.http_method,url)
   response = connection.getresponse()
   s=read_success_response(response, 'OAuth request')
   if debug:
      print 'OAuth request method: %s' % oauth_request.http_method
      print 'OAuth response status: %s' % response.status
      print 'OAuth response bytes: %s' % len(s)
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
      response.close()


def fitbit(api_call):
   api_call = validate_api_call(api_call)
   consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
   signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
   connection = None
   try:
      # if local does not exist
      if not os.path.lexists(ACCESS_TOKEN_STRING_FNAME):
         connection = httplib.HTTPSConnection(SERVER)
         # obtain token to get request
         print '* Obtain a request token ...'
         oauth_request = oauth.OAuthRequest.from_consumer_and_token(
               consumer, http_url=REQUEST_TOKEN_URL)
         oauth_request.sign_request(signature_method, consumer, None)
         resp=fetch_response(oauth_request, connection, debug=DEBUG)
         auth_token=oauth.OAuthToken.from_string(resp)

         # authorize the request token
         print '* Authorize the request token ...'
         auth_url="%s?oauth_token=%s" % (AUTHORIZATION_URL, auth_token.key)
         print 'Authorization URL:\n%s' % auth_url
         oauth_verifier = raw_input(
            'Please go to the above URL and authorize the '+
            'app -- Type in the Verification code from the website, when done: ')
         print '* Obtain an access token ...'
         # note that the token we're passing to the new
         # OAuthRequest is our current request token
         oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=auth_token, http_url=ACCESS_TOKEN_URL,
            parameters={'oauth_verifier': oauth_verifier})
         oauth_request.sign_request(signature_method, consumer, auth_token)

         # now the token we get back is an access token
         # parse the response into an OAuthToken object
         access_token=oauth.OAuthToken.from_string(
            fetch_response(oauth_request, connection, debug=DEBUG))

         # write the access token to file; next time we just read it from file
         if DEBUG:
            print 'Writing file', ACCESS_TOKEN_STRING_FNAME
         access_token_string = access_token.to_string()
         write_access_token_string(access_token_string)

      else:
         if DEBUG:
            print 'Reading file', ACCESS_TOKEN_STRING_FNAME
         access_token_string = read_access_token_string()

         access_token = oauth.OAuthToken.from_string(access_token_string)
         connection = httplib.HTTPSConnection(SERVER)

      # access protected resource
      print '* Access a protected resource ...'
      oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
         token=access_token, http_url=api_call)
      oauth_request.sign_request(signature_method, consumer, access_token)
      headers = oauth_request.to_header(realm='api.fitbit.com')
      connection.request('GET', api_call, headers=headers)
      resp = connection.getresponse()
      data = read_success_response(resp, 'protected resource request')
      return data
   finally:
      if connection is not None:
         connection.close()

if __name__ == '__main__':
   print json.loads(fitbit('/1/user/-/sleep/date/2013-08-31.json'))
