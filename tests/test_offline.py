"""Unit tests that do not need Kafka or the metadata API."""

from src.parse import CreateAccountEvent, RateEvent, WatchEvent, parse_line
from src.evaluate import metrics_for_ranking, ndcg_at_k
from src.models.cold_start import heuristic_extract, llm_client_settings, score_catalog
import pandas as pd
import pytest


def test_parse_watch_rate_create() -> None:
    watch = parse_line(
        "2026-07-17T14:50:46,28083,GET /data/m/ace+ventura+pet+detective+1994/0.mpg"
    )
    assert isinstance(watch, WatchEvent)
    assert watch.user_id == 28083
    assert watch.movie_id == "ace+ventura+pet+detective+1994"
    assert watch.minute == 0

    rate = parse_line(
        "2026-07-17T16:19:12,28083,GET /rate/ace+ventura+pet+detective+1994=10"
    )
    assert isinstance(rate, RateEvent)
    assert rate.rating == 10

    create = parse_line("2026-09-01T00:00:00,99,GET /create_account")
    assert isinstance(create, CreateAccountEvent)
    assert create.user_id == 99

    assert parse_line("garbage") is None


def test_ranking_metrics() -> None:
    recs = ["a", "b", "c", "d"]
    relevant = {"b", "z"}
    m = metrics_for_ranking(recs, relevant, k=3)
    assert m["hit"] == 1.0
    assert m["precision"] == 1 / 3
    assert m["recall"] == 0.5
    assert ndcg_at_k(recs, relevant, 4) > 0


def test_heuristic_genre_extract_and_score() -> None:
    prefs = heuristic_extract(
        likes="I love action and science fiction, especially Star Wars",
        dislikes="I hate horror",
    )
    assert "Action" in prefs["liked_genres"]
    assert "Science Fiction" in prefs["liked_genres"]
    assert "Horror" in prefs["disliked_genres"]
    movies = pd.DataFrame(
        [
            {"id": "star+wars+1977", "title": "Star Wars", "genres": ["Adventure", "Science Fiction"]},
            {"id": "scream+1996", "title": "Scream", "genres": ["Horror"]},
            {"id": "fargo+1996", "title": "Fargo", "genres": ["Crime", "Drama"]},
        ]
    )
    ranked = score_catalog(prefs, movies, popularity={"star+wars+1977": 10, "scream+1996": 9, "fargo+1996": 8})
    assert ranked.iloc[0]["movie_id"] == "star+wars+1977"
    assert ranked.iloc[-1]["movie_id"] == "scream+1996"


def test_gemini_key_selects_google_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyDummyTestKey")
    kwargs, model = llm_client_settings()
    assert "generativelanguage.googleapis.com" in kwargs["base_url"]
    assert kwargs["api_key"] == "AIzaSyDummyTestKey"
    assert model.startswith("gemini")


def test_openai_key_keeps_default_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-gemini")
    kwargs, model = llm_client_settings()
    assert "base_url" not in kwargs
    assert kwargs["api_key"] == "sk-test-not-gemini"
    assert not model.startswith("gemini")
