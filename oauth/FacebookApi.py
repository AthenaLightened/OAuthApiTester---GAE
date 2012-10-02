from . import OAuthApi

class FacebookApi(OAuthApi.OAuthApi, OAuthApi.RequestListener):
  def __init__(self, client_id='', client_secret='', **kwargs):
    super(FacebookApi, self).__init__(client_id, client_secret, **kwargs)

    # force the defaults
    self.uid = ''
    self.request_listener = self
    self.authorization_endpoint = "https://www.facebook.com/dialog/oauth"
    self.token_endpoint = "https://graph.facebook.com/oauth/access_token"
    self.api_endpoint = "https://graph.facebook.com"
