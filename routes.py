from webapp2_extras.routes import RedirectRoute
from modules import user

_routes = [
        RedirectRoute('/', user.MainPage, name='login', strict_slash=True),
        RedirectRoute('/manage<format:(.*)>', user.Manage, name='logout', strict_slash=True),
        RedirectRoute('/stream/image/get', user.Thumbnailer, name='get image', strict_slash=True),
        RedirectRoute('/stream/image/upload', user.Uploader, name='image upload', strict_slash=True),
        RedirectRoute('/upload', user.UploadHandler, name='image upload', strict_slash=True),
        RedirectRoute('/stream/view<format:(.*)>', user.View, name='view stream', strict_slash=True),
        RedirectRoute('/view<format:(.*)>', user.ViewAll , name='view all streams', strict_slash=True),
        RedirectRoute('/create', user.Create , name='create-stream', strict_slash=True),
        RedirectRoute('/ping<format:(.*)>', user.Ping , name='create-stream', strict_slash=True),
        RedirectRoute('/serve/<resource:(.*)>', user.ServeHandler , name='create-stream', strict_slash=True),
        RedirectRoute('/subscribe<format:\.(.*)>', user.Subscribe , name='subscribe a stream', strict_slash=True)

]

def get_routes():
    return _routes

def add_routes(app):
    for r in _routes:
        app.router.add(r)
