from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.api import search
from google.appengine.api import mail
from settings import JINJA_ENVIRONMENT
import datetime
import json
import operator

class User(db.Model):
    subscriptions = db.ListProperty(db.Key)
    email = db.EmailProperty()
    google_id = db.StringProperty()

    @staticmethod
    def create_new_user(email, google_id):
        user = User.gql("WHERE google_id = :1", google_id).get()
        if user:
            return user, False # no new user is created.
        else:
            user = User(email=db.Email(email), google_id=google_id).put()
            return user, True # new  user created

    @staticmethod
    def get_user(google_id):
        return User.gql("WHERE google_id = :1", google_id).get()

    def subscribe(self, stream):
        self.subscriptions.append(stream.key())
        self.put()

    def unsubscribe(self, stream):
        if stream.key() in self.subscriptions:
            self.subscriptions.remove(stream.key())
        self.put()

class Stream(db.Model):
    owner = db.ReferenceProperty(User,
                                 required=True,
                                 collection_name="owned")
    name = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    cover_image = db.StringProperty()
    tags = db.StringListProperty()
    view_count = db.IntegerProperty(default=0)

    def __dict__(self):
        return {
                "id" : self.key().id(),
                "name" : self.name,
                "created_at"  : self.created_at.strftime("%d/%m/%y"),
                "updated_at" : self.updated_at.strftime("%d/%m/%y"),
                "cover_image" : self.cover_image,
                "tags" : self.tags,
                "view_count" : str(self.view_count),
                "count" : self.images.count()
                }

    # cursor can be used: https://developers.google.com/appengine/docs/python/datastore/queries#Python_Limitations_of_cursors
    def get_images(self, limit=None, useCursor=False, user=None, resetCursor=False):
        # override use cursor flag if resetCursor flag is set
        useCursor = useCursor and (not resetCursor)

        if resetCursor:
            memcache.delete("stream_images:cursor:%s")

        stream_photos_query  = self.images
        if useCursor:
            cursor = memcache.get("stream_images:cursor:%s" % user.google_id)


        if useCursor and cursor:
            stream_photos_query.with_cursor(start_cursor=cursor)

        stream_photos = stream_photos_query.fetch(limit=limit)

        cursor = stream_photos_query.cursor()
        memcache.set("stream_images:cursor:%s" % user.google_id, cursor)

        return stream_photos

    def to_json(self):
        return json.dumps(self.__dict__())

    def update_view_count(self):
        self.view_count = int(self.view_count) + 1
        self.put()
        View(stream=self).put()
        return self.view_count

    @staticmethod
    def create_user_stream(name, user, cover_image, tags):
        stream = Stream.gql("WHERE name = '%s'" % name).get()
        if not stream:
            stream = Stream(owner=user,
                        name = name,
                        cover_image = cover_image,
                        tags = tags.split(','), view_count=0)
            stream.put()
        else:
            return None, "Stream already present"
        return stream, "New Stream Created"

    def add_photo(self, img, title, comments):
        photo = Photo(full_size_image=img,
                    title=title,
                    comments=comments,
                    stream=self)
        photo.put()
        return photo

    @staticmethod
    def get_all_owned_streams(user):
        owned_streams = user.owned.fetch(limit=None)
        user_streams = []
        for stream in owned_streams:
            user_streams.append(stream.__dict__())

        return user_streams

    @staticmethod
    def get_all_subscribed_streams(user):
        streams = user.subscriptions
        subscribed_streams = []
        for stream in streams:
            stream_obj = db.get(stream)
            if stream_obj:
                subscribed_streams.append(db.get(stream).__dict__())

        return subscribed_streams

class Search():
    @staticmethod
    def find_by_keyword(keyword):
        all_stream = Stream.all()
        results = []
        for stream in all_stream:
            if (keyword in stream.name) or (keyword in stream.tags):
                results.append(stream.__dict__())
        return results
"""
PHOTO
"""
class Photo(db.Model):
    comments = db.StringProperty("comments")
    title = db.StringProperty("title")
    stream = db.ReferenceProperty(Stream, collection_name="images")
    blob_key = blobstore.BlobReferenceProperty()

    def __dict__(self, resize=None):
        if resize:
            url = images.get_serving_url(self.blob_key) + ('=s%s' % resize)
        return {
                "id" : self.key().id(),
                "url" : images.get_serving_url(self.blob_key),
                "comments" : self.comments,
                "stream_id" : self.stream.key().id()
                }



class View(db.Model):
    stream = db.ReferenceProperty(Stream, collection_name="views")
    created_at = db.DateTimeProperty(auto_now_add=True)

    @staticmethod
    def seconds_ago(time_s):
        return datetime.datetime.now() - datetime.timedelta(seconds=time_s)

    @staticmethod
    def getTop():
        stream_count = {}
        views = View.all().filter('created_at >', View.seconds_ago(2*60*60))
        for view in views:
            if view.stream.key().id() in stream_count:
                stream_count[view.stream.key().id()] += 1
            else:
                stream_count[view.stream.key().id()] = 1
        return sorted(stream_count.items(), key=operator.itemgetter(1), reverse=True)[0:3]

class TrendSetter(db.Model):

    @staticmethod
    def topTrending():
        TrendSetter.setTrend()
        result = {}
        stream_dict = dict(memcache.get("top_trending"))
        i = 0
        for streamid in stream_dict:
            stream = Stream.get_by_id(streamid)
            if stream:
                result[i]= { "stream" : stream.__dict__(), "one_hour_view_count" : stream_dict[streamid] }
                i += 1
        return result


    @staticmethod
    def setTrend():
        if len(View.getTop()) > 0:
            memcache.set("top_trending", View.getTop())



class CronHandler(db.Model):

    @staticmethod
    def initialize():
        pass

    @staticmethod
    def runJob():
        pass

    @staticmethod
    def hourlyJobs():
        TrendSetter.setTrend()


class Mailer():
    @staticmethod
    def sendMail(ids, mailType):
        message = mail.EmailMessage(sender="ankit3goyal@gmail.com",
                            subject="Your account has been approved")
        template = JINJA_ENVIRONMENT.get_template('templates/newsletter.html')
        template_values = {}
        for email in ids:
            message.to = email
            message.html = template.render(template_values)
            message.send()
        return


