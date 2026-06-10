import json
import os
import tempfile
import unittest

from system.storage import append_chat_exchange, load_conversation, store_ai_evaluation, store_user_input, store_ai_input


class TestStorage(unittest.TestCase):
    def test_append_chat_exchange_creates_conversation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "conversation.json")
            entry = append_chat_exchange("hello", "hi there", filename=filename)

            self.assertEqual(entry["user"], "hello")
            self.assertEqual(entry["ai"], "hi there")

            conversations = load_conversation(filename=filename)
            self.assertEqual(len(conversations), 1)
            self.assertEqual(conversations[0]["user"], "hello")
            self.assertEqual(conversations[0]["ai"], "hi there")

    def test_store_user_and_ai_input_append_to_same_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "conversation.json")
            store_user_input("user message", filename=filename)
            store_ai_input("ai response", filename=filename)

            conversations = load_conversation(filename=filename)
            self.assertEqual(len(conversations), 1)
            self.assertEqual(conversations[0]["user"], "user message")
            self.assertEqual(conversations[0]["ai"], "ai response")

    def test_store_ai_evaluation_appends_evaluation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "evaluation.json")
            evaluation = {"confidence_score": 2, "notes": "Test"}
            store_ai_evaluation(evaluation, filename=filename)
            store_ai_evaluation({"confidence_score": 1}, filename=filename)

            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["confidence_score"], 2)
            self.assertEqual(data[1]["confidence_score"], 1)
