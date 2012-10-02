import os
import urllib,urllib2,urlparse
import mimetools,mimetypes
import json
import pprint

class OAuthApi(object):
  '''A simple OAuthApi Class

  How to use: 
  # initialize 
  o = OAuthApi(client_id='801245460', 
               client_secret='d12b828fc77692f9440bb09e77a455fe', 
               redirect_uri="http://oauth-api-tester.appspot.com/",
               authorization_endpoint="https://open.t.qq.com/cgi-bin/oauth2/authorize",
               token_endpoint="https://open.t.qq.com/cgi-bin/oauth2/access_token",
               api_endpoint="http://open.t.qq.com/api")

  # get the authorization uri
  print o.getAuthorizationUri()

  # exchange for the access_token
  print o.getAccessToken(code='223a51a78fceebc6adb9ad5202452d90')

  # call the api
  o.access_token = '22e060247791b8095f92158e2eb923d2'
  o.api('user/info')
  '''

  def __init__(self, client_id, client_secret, **kwargs):
    ''' Constructor

    keyword arguments:
    client_id -- OAuth client_id
    client_secret -- OAuth client_secret
    request_sender -- A HTTP Wrapper for sending requests(default: RequestSender)
    kwargs -- Some optional urls, e.g. redirect_uri, authorization_endpoint, etc.
    '''
    if not client_id or not client_secret:
      raise ValueError("client_id and client_secret required")

    self.client_id = client_id
    self.client_secret = client_secret

    # set optional attributes
    if 'request_sender' in kwargs and kwargs['request_sender'] is not None:
      self.request_sender = kwargs['request_sender']
    else:
      self.request_sender = RequestSender()

    if 'request_listener' in kwargs and kwargs['request_listener'] is not None:
      self.request_listener = kwargs['request_listener']

    for attr in ['redirect_uri', 'authorization_endpoint', 'token_endpoint', 'api_endpoint']:
      if attr in kwargs:
        setattr(self, attr, kwargs[attr].lstrip("/"))

  def getAuthorizationUri(self, state=None, scope=None, redirect_uri=None):
    '''Return the constructed authorization uri'''
    redirect_uri = self.redirect_uri if redirect_uri is None else redirect_uri
    
    params = [('client_id', self.client_id),
              ('response_type', 'code'),
              ('redirect_uri', redirect_uri)]
    if state:
      params.append(('state', state))

    if scope:
      params.append(('scope', scope))

    return self.authorization_endpoint + '?' + urllib.urlencode(params)

  def getAccessToken(self, code=None, redirect_uri=None):
    '''Exchange the authoriazation_code for the access_token, and return it'''
    if code is not None:
      
      if not self.token_endpoint:
        raise ValueError("Token endpoint required")

      redirect_uri = self.redirect_uri if redirect_uri is None else redirect_uri
      params = [('client_id', self.client_id),
                ('client_secret', self.client_secret),
                ('redirect_uri', redirect_uri),
                ('grant_type', 'authorization_code'),
                ('code', code)]

      if self.request_listener:
        params = self.request_listener.onSendAccessTokenRequest(params)
        
      response = self.sendOAuthRequest(self.token_endpoint, params, 'POST')

      if self.request_listener:
        self.request_listener.onReceiveAccessTokenResponse(self.token_endpoint, response)

      self.access_token = response['access_token']

    return self.access_token;

  def api(self, api, params=None, method='GET', headers=None):
    '''Call the api
    
    keyword arguments:
    api -- The api you want to call
    params -- a dict or a list of 2-tuples, 
              files should be prefixed with '@', e.g. {'image': '@logo.png'}
              access_token will be automatically appended
    method -- 'GET' or 'POST'
    headers -- a dict for extra HTTP headers
    '''
    if not self.api_endpoint:
      raise ValueError("Api endpoint required")

    if not self.access_token:
      raise ValueError("Access Token required")
      
    if params is None:
      params = {'access_token': self.access_token}
    else:
      params = dict(params)
      params['access_token'] = self.access_token

    if self.request_listener:
      api, params, method, headers = self.request_listener.onSendApiRequest(api, params, method, headers)

    url = self.api_endpoint + '/' + api.lstrip('/')
    response = self.sendOAuthRequest(url, params, method, headers)

    if self.request_listener:
      self.request_listener.onReceiveApiResponse(url, response)

    return response

  def sendOAuthRequest(self, uri, params=None, method='GET', headers=None):
    '''Send an OAuth Request use self.request_sender, raise error if detectd, return the result
    
    keyword arguments:
    api -- The api you want to call
    params -- a dict or a list of 2-tuples, 
              files should be prefixed with '@', e.g. {'image': '@logo.png'}
    method -- 'GET' or 'POST'
    headers -- a dict for extra HTTP headers
    '''
    code, response = self.request_sender.sendRequest(uri, params, method, headers)

    if code != 200:
      if code in (403, 405):
        reason = 'Forbidden'
      elif code == 400:
        reason = 'Parameters error'
      else:
        reason = 'HTTP Error: ' + str(code)
      raise OAuthApiError(uri, '', reason)

    # try decode as json
    try:
      decoded = json.loads(response, 'utf_8')
    except ValueError:
      # try treat it as query string
      decoded = urlparse.parse_qs(response)

      if len(decoded) == 0:
        decoded = response
      else:
        # {"name": ["value"]} => {"name": "value"}
        decoded = dict((k, decoded[k][0]) for k in decoded)

    # check error
    if isinstance(decoded, dict) and 'error' in decoded:
      if 'error_description' in decoded:
        raise OAuthApiError(uri, response, decoded['error_description'])
      else:
        raise OAuthApiError(uri, response, decoded['error'])
    elif isinstance(decoded, (str, unicode)): 
      raise OAuthApiError(uri, response, decoded)

    return decoded


class OAuthApiError(Exception):
  
  def __init__(self, request, response, reason):
    self.request = request
    self.response = response
    self.reason = reason

  def __str__(self):
    return "[{}], [{}], [{}]".format(self.request, self.response, self.reason)


class RequestSender(object):
  '''
  A simple RequestSender Class
  '''

  SUPPORTED_HTTP_METHODS = ['GET', 'POST']

  def sendRequest(self, uri, params=None, method='GET', headers=None):
    '''
    Send the request
    return (http_status_code, http_response_body)
    '''
    if not uri:
      raise ValueError("uri required")

    method = method.upper()
    if method not in RequestSender.SUPPORTED_HTTP_METHODS:
      raise NotImplementedError("http method({method}) not implemented".format(method=method))

    data = None
    headers = {} if headers is None else headers
    headers['User-Agent'] = 'OAuthApi - Python'

    # append query string for GET
    if method == 'GET' and params is not None and len(params) > 0:
      query = urllib.urlencode(params)
      uri = uri + '&' + query if '?' in uri else uri + '?' + query

    if method == 'POST' and params is not None and len(params) > 0:
      params = dict(params)
      files = []
      fields = []
      for name in params:
        value = params[name]
        # cast to string
        if isinstance(value, (int,long,float)):
          value = str(value)

        if value[0:1] == '@': # it's a file
          path = value[1:]
          # try to get the file content
          try:
            with open(path) as f:
              value = f.read()
            file_name = os.path.basename(path)
            mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'

            files.append((name, file_name, mime_type, value))
          except IOError:
            # it's just a normal field
            fields.append((name, value))
        else: # it's a normal field
          fields.append((name, value))
          
      if len(files) > 0:
        # use multipart
        boundary = mimetools.choose_boundary()

        body = []
        part_boundary = '--' + boundary
        # add files
        for name, file_name, mime_type, value in files:
          body.extend([part_boundary,
                       'Content-Disposition: file; name="{}"; filename="{}"'.format(name, file_name),
                       'Content-Type: {}'.format(mime_type),
                       '',
                       value])

        # add other fields
        for name, value in fields:
          body.extend([part_boundary,
                       'Content-Disposition: form-data; name="{}"'.format(name),
                       '',
                       value])


        body.extend([part_boundary + '--', ''])
        data = '\r\n'.join(body)

        headers['Content-type'] = 'multipart/form-data; boundary={boundary}'.format(boundary=boundary)
        headers['Content-length'] = len(data)
      else:
        data = urllib.urlencode(fields)

    request = urllib2.Request(uri, data, headers)
    try:
      response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
      return e.code, None

    return response.getcode(), response.read()


class RequestListener(object):
  
  def onSendAccessTokenRequest(self, params):
    return params
    
  def onReceiveAccessTokenResponse(self, request, response):
    pass

  def onSendApiRequest(self, api, params, method, headers):
    return api, params, method, headers

  def onReceiveApiResponse(self, request, response):
    pass



if __name__ == '__main__':
  pass
  # test request sender
#  sender = RequestSender()
#  print sender.sendRequest("http://localhost/test.php", {'a': 1}, 'GET')
#  print sender.sendRequest("http://localhost/test.php", [('a', 1)], 'GET')
#  print sender.sendRequest("http://localhost/test.php", [('a', 1)], 'POST')
#  print sender.sendRequest("http://localhost/test.php", [('a', 1), ('file', '@' + os.path.abspath(__file__))], 'POST')

#  o = OAuthApi(client_id='801245460', 
#            client_secret='d12b828fc77692f9440bb09e77a455fe', 
#            redirect_uri="http://oauth-api-tester.appspot.com/",
#            authorization_endpoint="https://open.t.qq.com/cgi-bin/oauth2/authorize",
#            token_endpoint="https://open.t.qq.com/cgi-bin/oauth2/access_token",
#            api_endpoint="http://open.t.qq.com/api")
#  #print o.getAuthorizationUri()
#  #print o.getAccessToken(code='223a51a78fceebc6adb9ad5202452d90')
#  o.access_token = '22e060247791b8095f92158e2eb923d2'
#  pprint.pprint(o.api('user/info'))
