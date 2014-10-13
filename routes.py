from webapp2_extras.routes import RedirectRoute
from modules import user

_routes = [
        RedirectRoute('/', user.MainPage, name='login', strict_slash=True),
        RedirectRoute('/manage<format:(.*)>', user.Manage, name='logout', strict_slash=True),
        RedirectRoute('/stream/image/get', user.Thumbnailer, name='get image', strict_slash=True),
        RedirectRoute('/stream/image/upload', user.Uploader, name='image upload', strict_slash=True),
        RedirectRoute('/upload/', user.UploadHandler, name='image upload', strict_slash=True),
        RedirectRoute('/stream/view<format:(.*)>', user.View, name='view stream', strict_slash=True),
        RedirectRoute('/view<format:(.*)>', user.ViewAll , name='view all streams', strict_slash=True),
        RedirectRoute('/create<format:(.*)>', user.Create , name='create-stream', strict_slash=True),
        RedirectRoute('/ping<format:(.*)>', user.Ping , name='create-stream', strict_slash=True),
        RedirectRoute('/serve/<resource:(.*)>', user.ServeHandler , name='create-stream', strict_slash=True),
        RedirectRoute('/stream/subscribe<format:\.(.*)>', user.Subscribe , name='subscribe a stream', strict_slash=True),
        RedirectRoute('/stream/unsubscribe<format:\.(.*)>', user.UnSubscribe , name='subscribe a stream', strict_slash=True),
        RedirectRoute('/search<format:(.*)>', user.Search , name='search stream', strict_slash=True),
        #RedirectRoute('/sendmail<format:(.*)>', user.Mailer , name='search stream', strict_slash=True),
        RedirectRoute('/social<format:(.*)>', user.Social , name='search stream', strict_slash=True),
        RedirectRoute('/trending<format:(.*)>', user.Trending , name='trending stream', strict_slash=True),
        RedirectRoute('/update-rate<format:(.*)>', user.UpdateNotificationRate , name='trending stream', strict_slash=True),
        RedirectRoute('/stream/delete', user.DeleteStream , name='search stream', strict_slash=True),
        RedirectRoute('/autocomplete<format:(.*)>', user.AutoCompleteHandler , name='autocomplete suggessions', strict_slash=True),
        RedirectRoute('/tasks', user.TaskExecutor , name='search stream', strict_slash=True),
        RedirectRoute('/stream/geoview<format:(.*)>', user.GeoHandler , name='search stream', strict_slash=True)

]

def get_routes():
    return _routes

def add_routes(app):
    for r in _routes:
        app.router.add(r)
