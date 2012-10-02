import webapp2

class SiteHandler(webapp2.RequestHandler):
  def get(self):
    self.redirect("/public/index.html?" + self.request.query_string)
