import urllib
import routes
import webapp2
import models
import config
from google.appengine.api import users
from settings import JINJA_ENVIRONMENT
from modules import user

package = 'Hello'


#application = webapp2.WSGIApplication([
    #('/', MainPage),
    #('/manage', user.Manage),
    #('/stream/image/get', user.Thumbnailer),
    #('/stream/image/upload', user.Uploader),
    #('/view', user.ViewAll),
    #('/stream/view', user.View),
    #('/create', user.Create)
#], debug=True)
application = webapp2.WSGIApplication(config=config.webapp2_config)
routes.add_routes(application)
