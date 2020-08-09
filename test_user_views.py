"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
# from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 9999
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("user1", "test1@test.com", "password", None)
        self.u1_id = 1111
        self.u1.id = self.u1_id
        self.u2 = User.signup("user2", "test2@test.com", "password", None)
        self.u2_id = 2222
        self.u2.id = self.u2_id
        self.u3 = User.signup("user3", "test3@test.com", "password", None)
        self.u3_id = 3333
        self.u3.id = self.u3_id
        self.u4 = User.signup("user4", "test4@test.com", "password", None)
        self.u4_id = 4444
        self.u4.id = self.u4_id

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_not_logged_in_view(self):
        with self.client as client:
            resp = client.get('/')
            html = resp.get_data(as_text=True)
            self.assertIn("What's Happening?", html)

    def test_user_list(self):
        with self.client as client:
            resp = client.get('/users')
            html = resp.get_data(as_text=True)
            self.assertIn("@user1", html)
            self.assertIn("@user2", html)
            self.assertIn("@user3", html)
            self.assertIn("@user4", html)

    def test_user_query(self):
        with self.client as client:
            resp = client.get('/users?q=user')
            html = resp.get_data(as_text=True)
            self.assertIn("@testuser", html)
            self.assertIn("@user1", html)
            self.assertIn("@user2", html)
            self.assertIn("@user3", html)
            self.assertIn("@user4", html)

    def test_is_followed_view(self):
        self.u1.followers.append(self.u3)
        self.u1.followers.append(self.u4)
        db.session.commit()
        self.assertTrue(self.u1.is_followed_by(self.u3))
        self.assertTrue(self.u1.is_followed_by(self.u4))
        with self.client as client:
            resp = client.get(f"/users/{self.u1_id}")
            html = resp.get_data(as_text=True)
            self.assertIn('<a href="/users/1111/followers">2</a>', html)

    def test_is_following_view(self):
        self.u1.following.append(self.u3)
        self.u1.following.append(self.u4)
        db.session.commit()
        self.assertTrue(self.u1.is_following(self.u3))
        self.assertTrue(self.u1.is_following(self.u4))
        with self.client as client:
            resp = client.get(f"/users/{self.u1_id}")
            html = resp.get_data(as_text=True)
            self.assertIn('<a href="/users/1111/following">2</a>', html)

    def test_user_likes(self):
        msg = Message(id=123, text="likelike", user_id=self.u1_id)
        l = Likes(user_id=self.testuser_id, message_id=msg.id)
        db.session.add_all([msg, l])
        db.session.commit()
        self.assertEqual(self.testuser.likes[0].text, "likelike")
        self.assertEqual(self.testuser.likes[0].user_id, self.u1_id)
        with self.client as client:
            res = client.get(f"/users/{self.testuser_id}")
            html = res.get_data(as_text=True)
            self.assertIn('<a href="/users/9999/likes">1</a>', html)

    def test_unauthenticated_like(self):

        msg = Message(id=123, text="likelike", user_id=self.u1_id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            res = c.post(f"/messages/{msg.id}/like", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            self.assertIn("Access unauthorized", html)
