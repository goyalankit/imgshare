from google.appengine.ext import db

class User(db.Model):
    name = db.StringProperty("name")
    subscriptions = db.ListProperty(db.Key)
    email = db.StringProperty("email")
    google_id = db.StringProperty("google_id")

class Stream(db.Model):
    owner = db.ReferenceProperty(User,
                                 required=True,
                                 collection_name="owned")
    name = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now=True)
    created_at = db.DateTimeProperty(auto_now_add=True)
    cover_image = db.StringProperty()
    tags = db.StringListProperty()

    @staticmethod
    def create_stream(name, user, cover_image, tags):
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

"""
PHOTO
"""
class Photo(db.Model):
    comments = db.StringProperty("comments")
    title = db.StringProperty("title")
    stream = db.ReferenceProperty(Stream, collection_name="images")
    full_size_image = db.BlobProperty()

