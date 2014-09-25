from modules import user
import unittest
import json
import httplib
import urllib
import cookielib
import sys

sys.path.insert('../modules')

COOKIE = "tester_test@example.com:False:125112313150491131921"
globals = {
        "server" : "localhost",
        "port" : "8080",
        }
class TestManage(self):
    def setUp(self):
        conn = httplib.HTTPConnection(globals["server"])
        conn = httplib.HTTPConnection(globals["server"],globals["port"]) 

    def test_unauthorized_access(self):
        url = "http://" + globals["server"] + ":" + port + "/manage.json"
        response = conn.request("GET", url)
        import pdb; pdb.set_trace()
