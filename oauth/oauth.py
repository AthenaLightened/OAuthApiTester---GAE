import os,urllib,urllib2,urlparse,mimetools,mimetypes

class OAuth(object):
  '''
  A simple OAuthApi Class
  '''

  SUPPORTED_HTTP_METHODS = ['GET', 'POST']

  def __init__(self, client_id='', client_secret='', **kwargs):
    ''' '''
    if not client_id or not client_secret:
      raise ValueError("client_id and client_secret required")

    self.client_id = client_id
    self.client_secret = client_secret

    for url in ['redirect_uri', 'authorization_endpoint', 'token_endpoint', 'api_endpoint']:
      if url in kwargs:
        setattr(self, url, kwargs[url])

  def getAuthorizationUri(self, state=None, scope=None, redirect_uri=None):
    redirect_uri = self.redirect_uri if redirect_uri is None else redirect_uri
    
    params = {}
    params['client_id'] = self.client_id
    params['response_type'] = 'code'
    params['redirect_uri'] = redirect_uri

    if state:
      params['state'] = state

    if scope:
      params['scope'] = scope

    return "{host}?{query}".format(host=self.authorization_endpoint, query=urllib.urlencode(params))

  def getAccessToken(self, code=None, redirect_uri=None):
    if code is not None:
      
      if not self.token_endpoint:
        raise ValueError("Token endpoint required")

      params = {}
      params['client_id'] = self.client_id
      params['client_secret'] = self.client_secret
      params['redirect_uri'] = self.redirect_uri if redirect_uri is None else redirect_uri
      params['grant_type'] = 'authorization_code'
      params['code'] = code

      response = self.sendRequest('POST', self.token_endpoint, params)
      self._processAccessTokenResponse(response)

    return self.access_token;

  def setAccessToken(self, access_token):
    self.access_token = access_token

  def sendRequest(self, uri, params=None, method='GET', headers=None):
    if not uri:
      raise ValueError("uri required")

    method = method.upper()
    if method not in OAuth.SUPPORTED_HTTP_METHODS:
      raise NotImplementedError("http method({method}) not implemented".format(method=method))

    data = None
    headers = {} if headers is None else headers
    headers['User-Agent'] = 'OAuthApi - lixu'

    # append query string for GET
    if method == 'GET' and params is not None and len(params) > 0:
      query = urllib.urlencode(params)
      if '?' in uri:
        uri = "{uri}&{query}".format(uri=uri, query=query)
      else:
        uri = "{uri}?{query}".format(uri=uri, query=query)

    if method == 'POST' and params is not None and len(params) > 0:
      has_file = False
      for name, value in params:
        if value[0:1] == '@':
          has_file = True
          break

      if has_file:
        # use multipart
        boundary = mimetools.choose_boundary()

        body = []
        part_boundary = '--' + boundary
        for name, value in params:
          if value[0:1] == '@':
            path = value[1:]
            file_name = os.path.basename(path)
            mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'

            print "{}, {}, {}".format(path, file_name, mime_type)

            try:
              with open(path) as f:
                value = f.read()

              body.extend([part_boundary,
                           'Content-Disposition: file; name="{}"; filename="{}"'.format(name, file_name),
                           'Content-Type: {}'.format(mime_type),
                           '',
                           value])
            except IOError:
              pass
          else:
            body.extend([part_boundary,
                         'Content-Disposition: form-data; name="{}"'.format(name),
                         '',
                         value])
        body.extend([part_boundary + '--', ''])
        data = '\r\n'.join(body)

        headers['Content-type'] = 'multipart/form-data; boundary={boundary}'.format(boundary=boundary)
        headers['Content-length'] = len(data)
      else:
        data = urllib.urlencode(params)

    request = urllib2.Request(uri, data, headers)
    print "{}, {}, {}".format(request.get_method(), request.get_full_url(), request.get_selector())
    response = urllib2.urlopen(request).read()

    return response


  def _processAccessTokenResponse(self, response):
    pass

if __name__ == '__main__':
  o = OAuth(client_id='801245460', 
            client_secret='d12b828fc77692f9440bb09e77a455fe', 
            redirect_uri="http://oauth-api-tester.appspot.com/",
            authorization_endpoint="https://open.t.qq.com/cgi-bin/oauth2/authorize")
  print o.sendRequest('http://localhost/test.php', [('a', '@oauth.py'), ('b', 'this is b')], 'POST')
  #print o.getAuthorizationUri()
