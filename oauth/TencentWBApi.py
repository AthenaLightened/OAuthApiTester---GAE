from . import OAuthApi

class TencentWBApi(OAuthApi.OAuthApi, OAuthApi.RequestListener):
  def __init__(self, client_id='', client_secret='', **kwargs):
    super(TencentWBApi, self).__init__(client_id, client_secret, **kwargs)

    # force the defaults
    self.uid = ''
    self.name = ''
    self.open_id = ''
    self.open_secret = ''
    self.request_listener = self
    self.authorization_endpoint = "https://open.t.qq.com/cgi-bin/oauth2/authorize"
    self.token_endpoint = "https://open.t.qq.com/cgi-bin/oauth2/access_token"
    self.api_endpoint = "http://open.t.qq.com/api"


  def onSendApiRequest(self, api, params, method, headers):
    if not self.open_id:
      raise ValueError("openid is required.")

    params['openid'] = self.open_id
    params['format'] = 'json'
    params['oauth_consumer_key'] = self.client_id
    params['oauth_version'] = '2.a'
    params['scope'] = 'all'

    return api, params, method, headers

  def onReceiveApiResponse(self, request, response):
    if 'errcode' in response and str(response['errcode']) != '0':
      raise OAuthApi.OAuthApiError(request, response, response['msg'])


  def onReceiveAccessTokenResponse(self, request, response):
    self.uid = response['name']
    self.name = response['nick']
