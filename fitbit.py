"""
A Python library for accessing the FitBit API.
"""
import os, httplib 
from oauth import oauth 
import json
import settings

CONSUMER_KEY    = settings.CONSUMER_KEY
CONSUMER_SECRET = settings.CONSUMER_SECRET
SERVER = 'api.fitbit.com'
REQUEST_TOKEN_URL = 'http://%s/oauth/request_token' % SERVER
ACCESS_TOKEN_URL = 'http://%s/oauth/access_token' % SERVER
AUTHORIZATION_URL = 'http://%s/oauth/authorize' % SERVER
ACCESS_TOKEN_STRING_FNAME = 'access_token.string'
DEBUG = True


def fetch_response(oauth_request, connection, debug=DEBUG):
   url= oauth_request.to_url()
   connection.request(oauth_request.http_method,url)
   response = connection.getresponse()
   s=response.read()
   if debug:
      print 'requested URL: %s' % url
      print 'server response: %s' % s
   return s


def fitbit(api_call):
   connection = httplib.HTTPSConnection(SERVER)
   consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
   signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()

   # if local does not exist
   if not os.path.exists(ACCESS_TOKEN_STRING_FNAME):
      # obtain token to get request
      print '* Obtain a request token ...'
      oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, http_url=REQUEST_TOKEN_URL)
      if DEBUG:
         connection.set_debuglevel(10)
      oauth_request.sign_request(signature_method, consumer, None)
      resp=fetch_response(oauth_request, connection)
      auth_token=oauth.OAuthToken.from_string(resp)
      print 'Auth key: %s' % str(auth_token.key)
      print 'Auth secret: %s' % str(auth_token.secret)
      print '-'*75,'\n\n'

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
         fetch_response(oauth_request,connection))
      print 'Access key: %s' % str(access_token.key)
      print 'Access secret: %s' % str(access_token.secret)
      print '-'*75,'\n\n'


      # write the access token to file; next time we just read it from file
      if DEBUG:
         print 'Writing file', ACCESS_TOKEN_STRING_FNAME
      fobj = open(ACCESS_TOKEN_STRING_FNAME, 'w')
      access_token_string = access_token.to_string()
      fobj.write(access_token_string)
      fobj.close()

   else:
      if DEBUG:
         print 'Reading file', ACCESS_TOKEN_STRING_FNAME
      fobj = open(ACCESS_TOKEN_STRING_FNAME)
      access_token_string = fobj.read()
      fobj.close()

      access_token = oauth.OAuthToken.from_string(access_token_string)

   # access protected resource
   print '* Access a protected resource ...'
   oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
      token=access_token, http_url=api_call)
   oauth_request.sign_request(signature_method, consumer, access_token)
   headers = oauth_request.to_header(realm='api.fitbit.com')
   connection.request('GET', api_call, headers=headers)
   resp = connection.getresponse()
   data = resp.read()
   return data

if __name__ == '__main__':
   print json.loads(fitbit('/1/user/-/sleep/date/2013-08-31.json'))

