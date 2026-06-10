import importlib
import os
import unittest


class TestFirebaseHelpers(unittest.TestCase):
    def setUp(self):
        self.prev_db_url = os.environ.get("FIREBASE_DB_URL")
        self.prev_auth_token = os.environ.get("FIREBASE_AUTH_TOKEN")
        os.environ["FIREBASE_DB_URL"] = "https://example.firebaseio.com"
        os.environ["FIREBASE_AUTH_TOKEN"] = "test-token"
        import system.firebase as firebase_module
        importlib.reload(firebase_module)
        self.firebase = firebase_module

    def tearDown(self):
        if self.prev_db_url is None:
            os.environ.pop("FIREBASE_DB_URL", None)
        else:
            os.environ["FIREBASE_DB_URL"] = self.prev_db_url

        if self.prev_auth_token is None:
            os.environ.pop("FIREBASE_AUTH_TOKEN", None)
        else:
            os.environ["FIREBASE_AUTH_TOKEN"] = self.prev_auth_token

    def test_firebase_url_builds_correctly(self):
        url = self.firebase.firebase_url("users/test-user")
        self.assertTrue(url.startswith("https://example.firebaseio.com/users/test-user.json"))
        self.assertIn("auth=", url)

    def test_load_firebase_user_returns_empty_when_no_user(self):
        user = self.firebase.load_user("")
        self.assertEqual(user, {})

    def test_save_firebase_user_raises_for_missing_user_id(self):
        with self.assertRaises(ValueError):
            self.firebase.update_user("", {"key": "value"})
