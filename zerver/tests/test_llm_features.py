import os
from unittest import mock

import orjson
from django.test import SimpleTestCase
from typing_extensions import override

# Avoid LiteLLM network during import of production modules in these tests.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from zerver.actions.message_flags import do_mark_all_as_read
from zerver.lib.llm_client import default_model_for_key, parse_json_object
from zerver.lib.test_classes import ZulipTestCase
from zerver.lib.topic_title_improver import (
    _suggestion_cache,
    should_call_llm,
    title_token_overlap,
)
from zerver.models import UserMessage


def _fake_llm_response(content: str) -> dict[str, object]:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 40, "completion_tokens": 20, "total_tokens": 60},
    }


class LLMHelperUnitTest(SimpleTestCase):
    def test_parse_json_object_plain_and_fenced(self) -> None:
        self.assertEqual(parse_json_object('{"a": 1}'), {"a": 1})
        self.assertEqual(
            parse_json_object('Sure.\n```json\n{"drifted": true}\n```\n'),
            {"drifted": True},
        )

    def test_title_overlap_and_llm_gate(self) -> None:
        self.assertLess(
            title_token_overlap("Weekend plans", ["drain the postgres replicas"]),
            0.5,
        )
        self.assertGreater(
            title_token_overlap("Weekend plans", ["weekend brunch plans still on?"]),
            0.5,
        )
        self.assertFalse(should_call_llm("Weekend plans", 1, ["hello"]))
        self.assertTrue(
            should_call_llm(
                "Weekend plans",
                3,
                [
                    "Postgres failover window?",
                    "Drain replicas before the schema migration.",
                    "Lock the migration behind a feature flag.",
                ],
            )
        )
        self.assertTrue(should_call_llm("hi", 3, ["hello there", "still around?", "ping"]))

    def test_default_model_for_key_prefix(self) -> None:
        self.assertEqual(default_model_for_key("AQ.example"), "gemini/gemini-2.0-flash")
        self.assertEqual(default_model_for_key("AIzaSyExample"), "gemini/gemini-2.0-flash")
        self.assertEqual(default_model_for_key("sk-example"), "gpt-4o-mini")


class LLMFeaturesTestCase(ZulipTestCase):
    @override
    def setUp(self) -> None:
        super().setUp()
        _suggestion_cache.clear()
        self.reader = self.example_user("hamlet")
        self.writer = self.example_user("iago")
        self.channel_name = "Denmark"
        self.subscribe(self.reader, self.channel_name)
        self.subscribe(self.writer, self.channel_name)
        do_mark_all_as_read(self.reader)

    def _llm_settings(self):
        return self.settings(
            TOPIC_SUMMARIZATION_MODEL="gpt-4o-mini",
            TOPIC_SUMMARIZATION_API_KEY="test-key-not-real",
            TOPIC_SUMMARIZATION_PARAMETERS={},
        )

    def test_recap_requires_login(self) -> None:
        result = self.client_get("/json/messages/recap")
        self.assert_json_error(
            result, "Not logged in: API authentication or user session required", 401
        )

    def test_recap_requires_llm_configuration(self) -> None:
        self.login_user(self.reader)
        with self.settings(TOPIC_SUMMARIZATION_MODEL=None, TOPIC_SUMMARIZATION_API_KEY=None):
            result = self.client_get("/json/messages/recap")
        self.assert_json_error_contains(result, "LLM is not configured")

    def test_recap_empty_inbox(self) -> None:
        self.login_user(self.reader)
        with (
            self._llm_settings(),
            mock.patch("zerver.lib.llm_client.litellm.completion") as mocked_create,
        ):
            result = self.client_get("/json/messages/recap")
        self.assert_json_success(result)
        data = orjson.loads(result.content)
        self.assertEqual(data["unread_count"], 0)
        self.assertEqual(data["sections"], [])
        mocked_create.assert_not_called()

    def test_recap_summarizes_unread_and_includes_permalinks(self) -> None:
        msg_id = self.send_stream_message(
            self.writer,
            self.channel_name,
            content="The launch date slipped to Friday.",
            topic_name="Release plan",
        )
        self.send_stream_message(
            self.writer,
            self.channel_name,
            content="Please update the announcement draft.",
            topic_name="Release plan",
        )
        self.assertTrue(
            UserMessage.objects.filter(user_profile=self.reader, message_id=msg_id)
            .extra(where=[UserMessage.where_unread()])  # noqa: S610
            .exists()
        )

        recap_json = orjson.dumps(
            {
                "overview": "Iago pushed the launch and asked for an announcement update.",
                "sections": [
                    {
                        "title": "#Denmark > Release plan",
                        "summary": "Launch moved to Friday; announcement still needs a rewrite.",
                        "message_ids": [msg_id],
                    }
                ],
            }
        ).decode()

        self.login_user(self.reader)
        with (
            self._llm_settings(),
            mock.patch(
                "zerver.lib.llm_client.litellm.completion",
                return_value=_fake_llm_response(recap_json),
            ),
        ):
            result = self.client_get("/json/messages/recap")

        self.assert_json_success(result)
        data = orjson.loads(result.content)
        self.assertGreaterEqual(data["unread_count"], 2)
        self.assertIn("launch", data["overview"].lower())
        self.assertIn("Friday", data["sections"][0]["summary"])
        section = data["sections"][0]
        self.assertEqual(section["references"][0]["message_id"], msg_id)
        permalink = section["references"][0]["permalink"]
        self.assertIn("#narrow/channel/", permalink)
        self.assertIn("/near/" + str(msg_id), permalink)
        self.assertIn("/topic/", permalink)

    def test_topic_title_suggest_rejects_empty_topic(self) -> None:
        stream_id = self.get_stream_id(self.channel_name)
        self.login_user(self.reader)
        with self._llm_settings():
            result = self.client_post(
                "/json/messages/topic_title_suggest",
                {"stream_id": orjson.dumps(stream_id).decode(), "topic": "   "},
            )
        self.assert_json_error_contains(result, "Topic cannot be empty")

    def test_topic_title_suggest_skips_llm_for_short_threads(self) -> None:
        self.send_stream_message(
            self.writer,
            self.channel_name,
            content="Are we still on for Saturday?",
            topic_name="Weekend plans",
        )
        stream_id = self.get_stream_id(self.channel_name)
        self.login_user(self.reader)
        with (
            self._llm_settings(),
            mock.patch("zerver.lib.llm_client.litellm.completion") as mocked_create,
        ):
            result = self.client_post(
                "/json/messages/topic_title_suggest",
                {"stream_id": orjson.dumps(stream_id).decode(), "topic": "Weekend plans"},
            )
        self.assert_json_success(result)
        data = orjson.loads(result.content)
        self.assertFalse(data["drifted"])
        self.assertTrue(data["skipped_llm"])
        mocked_create.assert_not_called()

    def test_topic_title_suggest_detects_drift(self) -> None:
        topic = "Weekend plans"
        self.send_stream_message(
            self.writer, self.channel_name, content="Postgres failover window?", topic_name=topic
        )
        self.send_stream_message(
            self.writer,
            self.channel_name,
            content="We should drain replicas before the schema migration.",
            topic_name=topic,
        )
        self.send_stream_message(
            self.writer,
            self.channel_name,
            content="Lock the migration behind a feature flag.",
            topic_name=topic,
        )
        stream_id = self.get_stream_id(self.channel_name)
        suggestion = orjson.dumps(
            {
                "drifted": True,
                "suggested_title": "Database migration failover",
                "reason": "The thread is about a schema migration, not weekend plans.",
            }
        ).decode()

        self.login_user(self.reader)
        with (
            self._llm_settings(),
            mock.patch(
                "zerver.lib.llm_client.litellm.completion",
                return_value=_fake_llm_response(suggestion),
            ),
        ):
            result = self.client_post(
                "/json/messages/topic_title_suggest",
                {"stream_id": orjson.dumps(stream_id).decode(), "topic": topic},
            )
        self.assert_json_success(result)
        data = orjson.loads(result.content)
        self.assertTrue(data["drifted"])
        self.assertEqual(data["suggested_title"], "Database migration failover")
        self.assertFalse(data["skipped_llm"])
        self.assertGreaterEqual(data["message_count"], 3)
