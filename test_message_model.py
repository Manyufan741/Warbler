"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        user1 = User.signup("u1", "u1@aaa.com", "u1pswd", None)

        user1.id = 1111

        db.session.commit()

        self.user1 = user1

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_of_user(self):
        msg = Message(text="test message", user_id=self.user1.id)
        db.session.add(msg)
        db.session.commit()
        self.assertEqual(self.user1.messages[0].text, "test message")

    def test_like_message(self):
        msg = Message(text="liked message", user_id=self.user1.id)
        msg.id = 9999
        user2 = User.signup("u2", "u2@aaa.com", "u2pswd", None)
        user2.id = 2222
        user2.likes.append(msg)
        db.session.add_all([msg, user2])
        db.session.commit()

        self.assertEqual(len(user2.likes), 1)
        self.assertEqual(user2.likes[0].text, "liked message")

        like = Likes.query.filter(Likes.user_id == user2.id).all()
        self.assertEqual(like[0].user_id, 2222)
        self.assertEqual(like[0].message_id, 9999)
