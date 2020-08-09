"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser.id = 9999

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_unauthorized_add(self):
        with self.client as client:
            res = client.post("/messages/new",
                              data={"text": "Hello"}, follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_existing_message(self):
        testmsg = Message(text="test message", user_id=self.testuser.id)
        db.session.add(testmsg)
        db.session.commit()
        msg = Message.query.filter(Message.user_id == self.testuser.id).all()
        self.assertEqual(msg[0].text, "test message")

    def test_message_like(self):

        msg = Message(id=123, text="likelike", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = client.post("/messages/123/like", follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            likes = Likes.query.filter(Likes.message_id == 123).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser.id)

    def test_unauthenticated_like(self):

        msg = Message(id=123, text="likelike", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            res = client.post(
                f"/messages/{msg.id}/like", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            self.assertIn("Access unauthorized", html)

    def test_delete_message(self):
        msg = Message(id=123, text="to be deleted", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            res = client.post("/messages/123/delete", follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            deleted_message = Message.query.get(123)

            self.assertIsNone(deleted_message)

    def test_unauthorized_delete_message(self):
        msg = Message(id=123, text="to be deleted", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as client:
            res = client.post(
                f"/messages/{msg.id}/delete", follow_redirects=True)
            html = res.get_data(as_text=True)

            self.assertIn("Access unauthorized", html)
