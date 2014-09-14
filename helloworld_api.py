import routes
import webapp2
import config

application = webapp2.WSGIApplication(config=config.webapp2_config)
routes.add_routes(application)
