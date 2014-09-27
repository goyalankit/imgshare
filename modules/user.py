from google.appengine.ext import db
import jinja2
import webapp2
import urllib
import datetime
import cgi
import models
import json
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import mail
import random

from settings import JINJA_ENVIRONMENT

DEFAULT_IMAGES = [
        "https://docs.google.com/file/d/0ByjZS11ljx0gUmpmSUJvRUJRV0E/preview",
        "https://docs.google.com/file/d/0ByjZS11ljx0gUmpmSUJvRUJRV0E/preview"
        ]

# /manage
class Manage(webapp2.RequestHandler):
    def get(self, format):
        if not users.get_current_user():
            if format.find('json') > 0:
                self.error(401)
            else:
                self.redirect("/")
                return
        else:
            url = users.create_logout_url(self.request.uri)
            template_values = {'user' : users.get_current_user(), 'url' : url}

            user = models.User.get_user(users.get_current_user().user_id())
            streams = {}
            streams["owned"] = models.Stream.get_all_owned_streams(user)
            streams["subscribed"] = models.Stream.get_all_subscribed_streams(user)

            if format.find('json') > 0:
                self.response.headers.add_header("Content-Type", "application/json")
                self.response.write(json.dumps({"status" : "OK", "result" : streams}))
            else:
                template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
                template_values["streams"] = streams
                #self.respose.set_status(200);
                self.response.write(template.render(template_values))


class DeleteStream(webapp2.RequestHandler):
    def post(self):
        if not users.get_current_user():
            self.redirect("/")
            return
        else:
            if (self.request.get('stream_ids')):
                streams = [int(stream) for stream in self.request.get('stream_ids').split(',')]

                list_of_streams = models.Stream.get_by_id(streams);

                for stream in list_of_streams:
                    db.delete(models.View.all(keys_only=True).filter("stream =", stream).fetch(1000))
                    db.delete(stream.key())

                self.response.out.write(json.dumps({"status" : "OK", "result" : "delete successful"}))

            self.response.out.write(json.dumps({"status": "ERROR", "reason" : "Streams not found"}))


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return

        if self.request.get('stream_id'):
            stream = models.Stream.get_by_id(int(self.request.get('stream_id')))

        if not stream:
            self.response.out.write(json.dumps({"status" : "ERROR", "reason" : "No stream found"}))
            return

        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form

        if not upload_files:
            self.response.out.write(json.dumps({"status" : "ERROR", "reason" : "No image found"}))
            return

        blob_info = upload_files[0]

        photo = models.Photo(title=self.request.get("title","untitled image"), blob_key = blob_info)
        photo.stream = stream
        photo.comments = self.request.get("comments","")
        photo.put()
        if 'json' in format:
            self.response.out.write(json.dumps({"status" : "OK", "result" : "image upload success"}))
        else:
            self.redirect('./stream/view?id=' + self.request.get('stream_id') + '&upload=successful')



class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)

class Uploader(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload.html')
        self.response.out.write('<html><body>')
        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write("""Upload File: <input type="file" name="file"><br> <input "type"="text" name="stream_id"><br/>
        <input type="submit"
        name="submit" value="Submit"></form></body></html>""")

        def post(self):
            if not users.get_current_user():
                self.redirect("/")
                return

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
                #img = images.get_serving_url(photo.full_size_image)
                self.response.headers['Content-Type'] = 'image/png'
                self.response.out.write(photo.full_size_image)
                return

        # Either "id" wasn't provided, or there was no image with that ID
        # in the datastore.
        self.error(404)

class Create(webapp2.RequestHandler):
    def get(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        else:
            url = users.create_logout_url(self.request.uri)
            template = JINJA_ENVIRONMENT.get_template('templates/create.html')
            template_values = {'user' : users.get_current_user(), 'url' : url}
            self.response.write(template.render(template_values))

    def post(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        else:
            google_user = users.get_current_user()
            user = models.User.gql("WHERE google_id = :1", google_user.user_id()).get()
            if not user:
                user = models.User(name="jon", email=google_user.email()).put()

            if self.request.get("name"):
                stream, result = models.Stream.create_user_stream(self.request.get("name"),
                        user,
                        self.request.get("cover_image", DEFAULT_IMAGES[0]),
                        self.request.get("tags", ""))

                if stream:
                    if self.request.get('addsub'):
                        email_ids = self.request.get('addsub').split(',')
                        models.Mailer.sendMail(email_ids, "subscribe")

                    if 'json' in format:
                        self.response.out.write(json.dumps({"status" : "OK"}))
                        return
                    else:
                        self.redirect('/manage?refresh=true&message=success')
                        return
                else:
                    if 'json' in format:
                        self.response.out.write(json.dumps({"status" : "ERROR", "result" : result}))
                        return
                    else:
                        self.redirect('/manage?refresh=true&message=fail')
                        return

class View(webapp2.RequestHandler):
    def get(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        else:
            stream_id = self.request.get("id")
            if stream_id:
                stream = models.Stream.get_by_id(long(stream_id))
                if not stream:
                    self.response.out.write(json.dumps({"status" : "ERROR", "reason" : "No Stream Found" }))

                get_more = self.request.get("get_more");


                user = models.User.get_user(users.get_current_user().user_id())

                if get_more:
                    stream_photos = stream.get_images(limit=3, useCursor=True, user=user)
                else:
                    stream_photos = stream.get_images(limit=3, useCursor=True, user=user, resetCursor=True)
                photos = []
                for photo in stream_photos:
                    photos.append(photo.__dict__())
                url = users.create_logout_url(self.request.uri)
                stream.update_view_count()

                template_values = {'user' : users.get_current_user(), 'url' : url}
                template_values['photos'] = photos
                template_values['stream'] = stream
                template_values['upload_url'] = blobstore.create_upload_url('/upload')
                template_values['owner'] = stream.owner.google_id == user.google_id
                template_values['subscribed'] = [True for st in models.Stream.get_all_subscribed_streams(user) if stream.key().id() == st['id']] != []
                template_values['upload'] = self.request.get("upload",'')

                if format.find('json') > 0:
                    self.response.headers.add_header("Content-Type", "application/json")
                    self.response.out.write(json.dumps({"status" : "OK", "result" : photos }))
                else:
                    template = JINJA_ENVIRONMENT.get_template('templates/view_stream.html')
                    self.response.write(template.render(template_values))
            else:
                self.response.out.write(json.dumps({"status" : "ERROR", "reason" : "No Stream Found" }))

class ViewAll(webapp2.RequestHandler):
    def get(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        else:
            user = models.User.get_user(users.get_current_user().user_id())
            user_streams = {}
            user_streams["owned"] = models.Stream.get_all_owned_streams(user)
            user_streams["subscribed"] = models.Stream.get_all_subscribed_streams(user)
            url = users.create_logout_url(self.request.uri)
            template_values = {'user' : users.get_current_user(), 'url' : url}
            template_values['user_streams'] = user_streams
            r = lambda: random.randint(0,255)
            #["83BAE8", "E3DB18", "057351", "8F354D", "941F23", "1C6D76"]
            template_values['random_colors'] =  [('%02X%02XF0' % (r(),r())) for i in xrange(0,30)]

            if format.find('json') > 0:
                self.response.headers.add_header("Content-Type", "application/json")
                return self.response.out.write(json.dumps({"status" : "OK", "result" : user_streams}))
            else:
                template = JINJA_ENVIRONMENT.get_template('templates/view.html')
                self.response.write(template.render(template_values))


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


class Ping(webapp2.RequestHandler):
    def get(self, format):
        if not users.get_current_user():
            self.redirect("/")

        stream = models.Stream.get_by_id(int(self.request.get("stream_id")))
        images = stream.get_images()


class Subscribe(webapp2.RequestHandler):
    def post(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        user = models.User.get_user(users.get_current_user().user_id())

        if not (self.request.get('stream_id')):
            return self.response.write(json.dumps({"status" : "ERROR", "reason" : "Stream not found"}))

        stream = models.Stream.get_by_id(int(self.request.get('stream_id')))

        if not stream:
            return self.response.write(json.dumps({"status" : "ERROR", "reason" : "Stream not found"}))

        user.subscribe(stream)
        return self.response.write(json.dumps({"status" : "OK", "result" : "Subscribed to Stream"}))

class UnSubscribe(webapp2.RequestHandler):
    def post(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        user = models.User.get_user(users.get_current_user().user_id())

        if not (self.request.get('stream_ids')):
            return self.response.write(json.dumps({"status" : "ERROR", "reason" : "Stream not found"}))

        streams = [int(stream) for stream in self.request.get('stream_ids').split(',')]

        stream_obj_list = models.Stream.get_by_id(streams)

        if not stream_obj_list:
            return self.response.write(json.dumps({"status" : "ERROR", "reason" : "Stream not found"}))

        for stream in stream_obj_list:
            user.unsubscribe(stream)

        return self.response.write(json.dumps({"status" : "OK", "result" : "UnSubscribed Successfully"}))

class Search(webapp2.RequestHandler):
    def get(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        user = models.User.get_user(users.get_current_user().user_id())
        url = users.create_logout_url(self.request.uri)
        template_values = {'user' : users.get_current_user(), 'url' : url}

        if not self.request.get('name'):
            if format.find('json') > 0:
                self.response.headers.add_header("Content-Type", "application/json")
                # may be send latest
                self.response.out.write(json.dumps({"status" : "OK", "result" : [] }))
                return
            else:
                template = JINJA_ENVIRONMENT.get_template('templates/search.html')
                self.response.write(template.render(template_values))
                return

        # if q is present
        streams = models.Search.find_by_keyword(self.request.get('name'));

        self.response.write(json.dumps({"status" : "OK", "result" : streams}))

class Social(webapp2.RequestHandler):
    def get(self, format):
        user = models.User.get_user(users.get_current_user().user_id())
        url = users.create_logout_url(self.request.uri)
        template_values = {'user' : users.get_current_user(), 'url' : url}

        if format.find('json') > 0:
            self.response.headers.add_header("Content-Type", "application/json")
            # may be send latest
            self.response.out.write(json.dumps({"status" : "OK", "result" : ['stream1', 'stream2'] }))
            return
        else:
            template = JINJA_ENVIRONMENT.get_template('templates/social.html')
            self.response.write(template.render(template_values))

class Trending(webapp2.RequestHandler):
    def get(self, format):
        current_user = users.get_current_user();

        if not current_user:
            self.redirect("/")
            return

        user = models.User.get_user(current_user.user_id())
        url = users.create_logout_url(self.request.uri)
        template_values = {'user' : users.get_current_user(), 'url' : url}
        streams = models.TrendSetter.topTrending()
        template_values['user_streams'] = streams
        r = lambda: random.randint(0,255)
        # ["83BAE8", "E3DB18", "057351", "8F354D", "941F23", "1C6D76"]
        template_values['random_colors'] =  [('%02X%02XF0' % (r(),r())) for i in xrange(0,30)]
        job = models.Jobs.gql("WHERE user = :1 and job_type = :2", user, 'trends').get()
        if job:
            template_values['checked_options'] = {job.duration : 'checked'}
        else:
            template_values['checked_options'] = {'noreport' : 'checked'}

        if format.find('json') > 0:
            self.response.headers.add_header("Content-Type", "application/json")
            # may be send latest
            self.response.out.write(json.dumps({"status" : "OK", "result" : streams }))
            return
        else:
            template = JINJA_ENVIRONMENT.get_template('templates/trending.html')
            self.response.write(template.render(template_values))


class UpdateNotificationRate(webapp2.RequestHandler):
    def post(self, format):
        if not users.get_current_user():
            self.redirect("/")
            return
        user = models.User.get_user(users.get_current_user().user_id())
        if self.request.get('optionsRadios'):
            models.Jobs.createOrUpdate("trends", self.request.get('optionsRadios'), user)

        if 'json' in format:
            self.response.headers.add_header("Content-Type", "application/json")
            # may be send latest
            self.response.out.write(json.dumps({"status" : "OK", "result" : "Job updated" }))
        else:
            self.redirect('./trending?refresh=true&job-update=success')

class TaskExecutor(webapp2.RequestHandler):
    def get(self):
        if not (self.request.get('time')):
            return
        duration = self.request.get('time')
        models.CronHandler.runJob(duration)
        return


"""
class Mailer(webapp2.RequestHandler):
    def get(self, format):
        message = mail.EmailMessage(sender="ankit3goyal@gmail.com",
                            subject="Your account has been approved")

        message.to = "me@goyalankit.com"
        template = JINJA_ENVIRONMENT.get_template('templates/newsletter.html')
        template_values = {}
        message.html = template.render(template_values)

        message.send()
"""

