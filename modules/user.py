from google.appengine.ext import db
import jinja2
import webapp2
import urllib
import datetime
import cgi
import models
import json
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import memcache
from settings import JINJA_ENVIRONMENT

# /manage
class Manage(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect("/")
        else:
            url = users.create_logout_url(self.request.uri)
            template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
            template_values = {'user' : users.get_current_user(), 'url' : url}
            self.response.write(template.render(template_values))


class Uploader(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("""
          <form action="/stream/image/upload?%s" enctype="multipart/form-data" method="post">
          <div><input type="file" name="img"/></div>
          <div><input type="text" name="stream_id"/></div>
          <div><input type="text" name="comments"/></div>
          <div><label>Avatar:</label></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
          <hr>
          <form>Guestbook name: <input value="%s" name="guestbook_name">
          <input type="submit" value="switch"></form>
        </body>
      </html>""" % (urllib.urlencode({'guestbook_name': "cool"}),
                    cgi.escape("cool")))

    def post(self):
        if not users.get_current_user():
            self.redirect("/")

        if self.request.get('stream_id'):
            stream = models.Stream.get_by_id(int(self.request.get('stream_id')))

        if not stream:
            self.response.out.write(json.dumps({"status" : "ERROR", "reason" : "No stream found"}))


        photo = models.Photo(title=self.request.get("title","untitled image"))
        image = self.request.get('img')
        photo.full_size_image = db.Blob(image)
        photo.stream = stream
        photo.comments = self.request.get("comments","")
        output = photo.put()
        self.response.out.write(json.dumps({ "status" : "OK", "result" : "Image upload success %s" % output}))

class Thumbnailer(webapp2.RequestHandler):
    def get(self):
        if self.request.get("id"):
            photo = models.Photo.get_by_id(int(self.request.get("id")))

            if photo:
                #import pdb; pdb.set_trace()
                #img = images.get_serving_url(photo.full_size_image)
                self.response.headers['Content-Type'] = 'image/png'
                self.response.out.write(photo.full_size_image)
                return

        # Either "id" wasn't provided, or there was no image with that ID
        # in the datastore.
        self.error(404)

class Create(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect("/")
        else:
            url = users.create_logout_url(self.request.uri)
            template = JINJA_ENVIRONMENT.get_template('templates/create.html')
            template_values = {'user' : users.get_current_user(), 'url' : url}
            self.response.write(template.render(template_values))

    def post(self):
        if not users.get_current_user():
            self.redirect("/")
        else:
            google_user = users.get_current_user()
            user = models.User.gql("WHERE google_id = :1", google_user.user_id()).get()
            if not user:
                user = models.User(name="jon", email=google_user.email()).put()

            if self.request.get("name"):
                stream, result = models.Stream.create_user_stream(self.request.get("name"),
                                            user,
                                            "",
                                            "#cool")

            if stream:
                self.response.out.write(json.dumps({"status" : "OK"}))
            else:
                self.response.out.write(json.dumps({"status" : "ERROR", "result" : result}))

class View(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect("/")
        else:
            stream_id = self.request.get("id")
            if stream_id:
                stream = models.Stream.get_by_id(long(stream_id))
                stream_photos = stream.get_images(limit=3)
                photos = []
                for photo in stream_photos:
                    photos.append(photo.__dict__())
                self.response.out.write(json.dumps({"status" : "OK", "result" : photos }))
            else:
                self.response.out.write(json.dumps({"status" : "ERROR", "reason" : "No Stream Found" }))


class ViewAll(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect("/")
        else:
            user = models.User.get_user(users.get_current_user().user_id())
            owned_streams = user.owned.fetch(limit=None)
            user_streams = {}

            user_streams["owned"] = []
            for stream in owned_streams:
                user_streams["owned"].append(stream.__dict__())

            return self.response.out.write(json.dumps({"status" : "OK", "result" : user_streams}))

class MainPage(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            # create new user if it doens't exist
            models.User.create_new_user(users.get_current_user().email(),
                    users.get_current_user().user_id())
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

