import httplib,urllib

class OAuth(object):
  '''
  A simple OAuthApi Class
  '''

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
    

  def getAccessToken(self):
    pass

  def setAccessToken(self, access_token):
    pass

  def sendRequest(self, request):
    pass

if __name__ == '__main__':
  o = OAuth(client_id='801245460', 
            client_secret='d12b828fc77692f9440bb09e77a455fe', 
            redirect_uri="http://oauth-api-tester.appspot.com/",
            authorization_endpoint="https://open.t.qq.com/cgi-bin/oauth2/authorize")
  print o.getAuthorizationUri()
