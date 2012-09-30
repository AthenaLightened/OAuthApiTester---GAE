from . import OAuthApi

class SinaWBApi(OAuthApi.OAuthApi, OAuthApi.RequestListener):
  def __init__(self, client_id='', client_secret='', **kwargs):
    super(SinaWBApi, self).__init__(client_id, client_secret, **kwargs)

    # force the defaults
    self.uid = ''
    self.request_listener = self
    self.authorization_endpoint = "https://api.weibo.com/oauth2/authorize"
    self.token_endpoint = "https://api.weibo.com/oauth2/access_token"
    self.api_endpoint = "https://api.weibo.com/2"


  def onReceiveAccessTokenResponse(self, response):
    self.uid = response.uid
