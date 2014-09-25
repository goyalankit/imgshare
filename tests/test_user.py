import unittest
import json
import httplib
import urllib
import cookielib
import sys
from google.appengine.ext import db
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

globals = {
        "server" : "localhost",
        "port" : "8080",
        "cookie" : 'dev_appserver_login="tester_test@example.com:False:125112313150491131921"'

        }

class TestManage(unittest.TestCase):
    def setUp(self):
        self.conn = httplib.HTTPConnection(globals["server"])
        self.conn = httplib.HTTPConnection(globals["server"], globals["port"])
        self.testbed = testbed.Testbed();
        self.testbed.activate()
        self.testbed.init_user_stub()
        self.testbed.init_all_stubs()
        self.testbed.setup_env(
            USER_EMAIL = 'testeruser@example.com',
            USER_ID = '123',
            USER_IS_ADMIN = '1',
            AUTH_DOMAIN = 'testbed',
            overwrite = True)

    #def test_unauthorized_access(self):
        #url = "http://" + globals["server"] + ":" + globals["port"] + "/manage.json"
        #self.conn.request("GET", url)
        #resp = self.conn.getresponse()
        #self.assertTrue(resp.status == 401)

    def test_authorized_access(self):
        url = "http://" + globals["server"] + ":" + globals["port"] + "/manage.json"
        headers = {}
        #headers['Cookie'] = globals["cookie"]
        self.conn.request("GET", url, "", headers)
        import pdb; pdb.set_trace()
        resp = self.conn.getresponse()
        self.assertTrue(resp.status == 200)
        json_response = json.loads(resp.read())
        self.assertTrue(json_response["status"] == "OK")
        self.assertTrue(json_response["result"]["subscribed"] == [])
        self.assertTrue(json_response["result"]["owned"] == [])

#class TestCreateStream(unittest.TestCase):
    #def setUp(self):
        #self.conn = httplib.HTTPConnection(globals["server"])
        #self.conn = httplib.HTTPConnection(globals["server"], globals["port"])

    #def test_creation_of_stream(self):
        #url = "http://" + globals["server"] + ":" + globals["port"] + "/create"
        #headers = {}
        #params = urllib.urlencode({'name': 'mystream'})
        #headers['Cookie'] = globals["cookie"]
        #self.conn.request("POST", url, params, headers)
        #resp = self.conn.getresponse()
        #import pdb; pdb.set_trace()


if __name__ == '__main__':
    unittest.main()
