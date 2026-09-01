from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _
from pydantic import Json

from zerver.lib.exceptions import JsonableError
from zerver.lib.llm_client import llm_is_configured
from zerver.lib.message_recap import generate_unread_recap
from zerver.lib.response import json_success
from zerver.lib.topic_title_improver import suggest_topic_title
from zerver.lib.typed_endpoint import typed_endpoint, typed_endpoint_without_parameters
from zerver.models import UserProfile


def _require_llm() -> None:
    if not llm_is_configured():
        raise JsonableError(
            _("LLM is not configured. Add an API key to api.key or set LLM_API_KEY.")
        )


@typed_endpoint_without_parameters
def get_unread_message_recap(
    request: HttpRequest,
    user_profile: UserProfile,
) -> HttpResponse:
    """GET /api/v1/messages/recap — summarize the caller's unread messages."""
    _require_llm()
    recap = generate_unread_recap(user_profile)
    return json_success(request, data=recap)


@typed_endpoint
def topic_title_suggest_backend(
    request: HttpRequest,
    user_profile: UserProfile,
    *,
    stream_id: Json[int],
    topic: str,
) -> HttpResponse:
    """POST /api/v1/messages/topic_title_suggest — detect drift and suggest a title."""
    _require_llm()
    if not topic.strip():
        raise JsonableError(_("Topic cannot be empty."))
    suggestion = suggest_topic_title(user_profile, stream_id=stream_id, topic_name=topic)
    return json_success(request, data=suggestion)
