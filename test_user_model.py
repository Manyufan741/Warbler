"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        user1 = User.signup("u1", "u1@aaa.com", "u1pswd", None)
        user2 = User.signup("u2", "u2@aaa.com", "u2pswd", None)

        user1.id = 1111
        user2.id = 2222

        db.session.commit()

        self.user1 = user1
        self.user2 = user2

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_is_followed_by(self):
        self.user1.followers.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_followed_by(self.user2))

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))

    def test_signup(self):
        user3 = User.signup("u3", "u3@aaa.com", "u3pswd", None)
        user3.id = 3333
        db.session.commit()
        self.assertEqual(user3.username, "u3")
        self.assertEqual(user3.email, "u3@aaa.com")
        self.assertNotEqual(user3.password, "u3pswd")
        self.assertTrue(user3.password.startswith("$2b$"))

    def test_failed_signup_due_to_username(self):
        user3 = User.signup(None, "u3@aaa.com", "u3pswd", None)
        user3.id = 3333
        self.assertRaises(exc.IntegrityError, db.session.commit)

    def test_failed_signup_due_to_email(self):
        user3 = User.signup("u3", None, "u3pswd", None)
        user3.id = 3333
        self.assertRaises(exc.IntegrityError, db.session.commit)

    def test_failed_signup_due_to_password(self):
        with self.assertRaises(ValueError):
            User.signup("u3", "u3@aaa.com", None, None)
        with self.assertRaises(ValueError):
            User.signup("u3", "u3@aaa.com", "", None)

    def test_user_authentication(self):
        user = User.authenticate("u1", "u1pswd")
        self.assertTrue(user)
        self.assertEqual(user.id, self.user1.id)
