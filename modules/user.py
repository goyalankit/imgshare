import jinja2
import webapp2
import urllib
import datetime
import cgi
import models
import json
from google.appengine.api import users
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
        greeting = Photo(title="yah")

        if users.get_current_user():
            greeting.author = users.get_current_user().nickname()
        avatar = self.request.get('img')
        greeting.full_size_image = db.Blob(avatar)
        output = greeting.put()
        self.response.out.write("Image upload success %s" % output)

class Thumbnailer(webapp2.RequestHandler):
    def get(self):
        if self.request.get("id"):
            photo = Photo.get_by_id(int(self.request.get("id")))

            if photo:
                img = images.Image(photo.full_size_image)
                img.resize(width=80, height=100)
                img.im_feeling_lucky()
                thumbnail = img.execute_transforms(output_encoding=images.JPEG)

                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(thumbnail)
                return

        # Either "id" wasn't provided, or there was no image with that ID
        # in the datastore.
        self.error(404)

class Create(webapp2.RequestHandler):
    def get(self, is_json):
        if not users.get_current_user():
            self.redirect("/")
        else:
            url = users.create_logout_url(self.request.uri)
            template = JINJA_ENVIRONMENT.get_template('templates/create.html')
            template_values = {'user' : users.get_current_user(), 'url' : url}
            self.response.write(template.render(template_values))

    def post(self, is_json):
        import pdb; pdb.set_trace()
        if not users.get_current_user():
            self.redirect("/")
        else:
            google_user = users.get_current_user()
            user = models.User.gql("WHERE google_id = :1", google_user.user_id()).get()
            if not user:
                user = models.User(name="jon", email=google_user.email()).put()

            if self.request.get("name"):
                stream, result = models.Stream.create_stream(self.request.get("name"),
                                            user,
                                            "",
                                            "#cool")

            if stream and is_json:
                self.response.out.write(json.dumps({"status" : "OK"}))
            elif stream:
                self.redirect("./manage")
            else:
                self.response.out.write(json.dumps({"status" : "ERROR", "result" : result}))

class View(webapp2.RequestHandler):
    def get(self, is_json):
        pass


class ViewAll(webapp2.RequestHandler):
    def get(self):
        import pdb; pdb.set_trace()
