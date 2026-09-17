from zerver.views.llm_features import get_unread_message_recap, topic_title_suggest_backend
from zerver.views.message_summary import get_messages_summary

    rest_path(
        "messages/recap",
        GET=(get_unread_message_recap, {"intentionally_undocumented"}),
    ),
    rest_path(
        "messages/topic_title_suggest",
        POST=(topic_title_suggest_backend, {"intentionally_undocumented"}),
    ),
