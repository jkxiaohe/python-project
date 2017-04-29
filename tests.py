# _*_ encoding=utf-8 _*_

import unittest
from nowstagram import app

class NowstagramTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING']=True
        self.app=app.test_client()
        print 'setUp'

    def testDown(self):
        print 'testDown'
        pass

    def register(self,username,password):
        return self.app.post('/reg/' , data={"username" : username , "password" : password} , follow_redirects=True)

    def login(self,username,password):
        return self.app.post('/login/' , data={"username" : username , "password" : password} , follow_redirects=True)

    def logout(self):
        return self.app.get('/logout/')

    def test_reg_logout_login(self):
        assert self.register("hello" , "world").status_code == 200
        # assert '1' in self.app.open('/profile').data
        # self.logout()
        # assert '1' not in self.app.open('/').data
        # self.login("hello","world")
        # assert '1' in self.app.open('/').data

    def test_profile(self):
        r = self.app.open('/profile/3/' , follow_redirects=True)
        assert r.status_code == 200
        assert "password" in r.data
        self.register("hello2","world")
        assert "hello2" in self.app.open('/profile/1/' , follow_redirects=True).data
