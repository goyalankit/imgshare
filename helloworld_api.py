import urllib

from google.appengine.api import users

import webapp2
from settings import JINJA_ENVIRONMENT

package = 'Hello'


from modules import user

class MainPage(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        else:
            url = users.create_login_url(self.request.uri)

            url_linktext = 'Login'
            template = JINJA_ENVIRONMENT.get_template('templates/login.html')

        template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'user' : users.get_current_user()
        }

        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/manage', user.Manage),
    ('/stream/image/get', user.Thumbnailer),
    ('/stream/image/upload', user.Uploader),
    ('/view(.json)*', user.View),
    ('/stream/view', user.View),
    ('/create(.json)*', user.Create)
], debug=True)
