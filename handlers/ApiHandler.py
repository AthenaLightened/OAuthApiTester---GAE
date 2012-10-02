import webapp2,json
from oauth.SinaWBApi import SinaWBApi
from oauth.TencentWBApi import TencentWBApi 

configs = {'sina': {'client_id': '51885333',
                    'client_secret': 'c1b238a2f5ed43c177014fd6bcc76ee4',
                    'redirect_uri': 'http://oauth-api-tester.appspot.com/'},
           'tencent': {'client_id': '801245460',
                       'client_secret': 'd12b828fc77692f9440bb09e77a455fe',
                       'redirect_uri': 'http://oauth-api-tester.appspot.com/'}}

class ApiHandler(webapp2.RequestHandler):
  def get(self, action):
    method = getattr(self, 'api' + action[0].upper() + action[1:])
    if (callable(method)):
      method()
    else:
      self.response.write('404')

  def apiTest(self):
    self.response.write(dict(self.request.GET.items()))

  def apiGetAuthorizationUrl(self):
    platform = self.request.get('platform', default_value='sina')
    self.sendJSONResponse(self.getApi().getAuthorizationUri(state=platform))

  def apiGetAccessToken(self):
    code = self.request.get('code')
    self.sendJSONResponse(self.getApi().getAccessToken(code))

  def apiApi(self):
    api = self.getApi()

    try:
      api_to_call = self.request.get('api')
      params = dict((k, v) for k, v in self.request.GET.items() 
                           if k not in ['access_token', 'platform', 'api'])
      result = api.api(api_to_call, params)
      self.sendJSONResponse(result)
    except Exception as e:
      self.sendJSONResponse(False, str(e))
  

  def sendJSONResponse(self, result, error_message='', error_code=0):
    self.response.content_type = "application/json"
      
    if error_message == '':
      result = {'code': 0, 'message': '', 'data': result}
    else:
      result = {'code': error_code, 'message': error_message, 'data': result}

    self.response.write(json.dumps(result, sort_keys=True, indent=2))
    
    
  def getApi(self):
    platform = self.request.get('platform', default_value='sina')
    access_token = self.request.get('access_token', '')

    api = None
    if platform == 'sina':
      api = SinaWBApi(**configs['sina'])
    elif platform == 'tencent':
      api = TencentWBApi(**configs['tencent'])
      api.open_id = self.request.get('open_id')
      api.open_secret = self.request.get('open_secret')
    else:
      raise NotImplemented(platform)

    api.access_token = access_token
    return api
