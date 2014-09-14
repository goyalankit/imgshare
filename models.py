from google.appengine.ext import db
import json

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

class Stream(db.Model):
    owner = db.ReferenceProperty(User,
                                 required=True,
                                 collection_name="owned")
    name = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    cover_image = db.StringProperty()
    tags = db.StringListProperty()

    def __dict__(self):
        return {
                "id" : self.key().id(),
                "name" : self.name,
                "created_at"  : self.created_at.strftime("%d/%m/%y"),
                "updated_at" : self.updated_at.strftime("%d/%m/%y"),
                "cover_image" : self.cover_image,
                "tags" : self.tags
                }

    # cursor can be used: https://developers.google.com/appengine/docs/python/datastore/queries#Python_Limitations_of_cursors
    def get_images(self, limit, use_cursor=False, user=None):
        if use_cursor:
            cursor = memcache.get("stream_images:cursor:%s" % user.google_id)
        if use_cursor and cursor:
            self.images.with_cursor(start_cursor=cursor)

        stream_photos = self.images.fetch(limit=limit)

        if use_cursor:
            cursor = self.images.cursor()
            memcache.set("stream_images:cursor:%s" % user.google_id, cursor)

        return stream_photos

    def to_json(self):
        return json.dumps(self.__dict__())

    @staticmethod
    def create_user_stream(name, user, cover_image, tags):
        stream = Stream.gql("WHERE name = '%s'" % name).get()
        if not stream:
            stream = Stream(owner=user,
                        name = name,
                        cover_image = cover_image,
                        tags = tags.split(','))
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
        return user.owned.get()
"""
PHOTO
"""
class Photo(db.Model):
    comments = db.StringProperty("comments")
    title = db.StringProperty("title")
    stream = db.ReferenceProperty(Stream, collection_name="images")
    full_size_image = db.BlobProperty()

    def __dict__(self):
        return {
                "id" : self.key().id(),
                "url" : "./stream/image/get?id=%s" % self.key().id(),
                "comments" : self.comments,
                "stream_id" : self.stream.key().id()
                }

