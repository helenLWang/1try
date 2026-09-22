"""Collect Kafka events + metadata API records into CSV/JSONL files.

Example:

    python -m src.collect --max-events 5000000 --windows 12
    python -m src.collect --max-events 20000 --recent   # smoke test
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from kafka import KafkaConsumer, TopicPartition
from tqdm import tqdm

from src.config import (
    COLLECTION_META_PATH,
    DATA_DIR,
    DEFAULT_MAX_EVENTS,
    KAFKA_BOOTSTRAP,
    KAFKA_TOPIC,
    MAX_RATING,
    METADATA_API,
    MIN_RATING,
    MOVIES_PATH,
    RATINGS_PATH,
    SAMPLE_DIR,
    USERS_PATH,
    WATCHES_PATH,
)
from src.parse import CreateAccountEvent, RateEvent, WatchEvent, parse_line
from src.api import fetch_movies, fetch_users


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def _decode(raw: bytes | None) -> str:
    if not raw:
        return ""
    return raw.decode("utf-8", errors="replace")


def _ingest_event(
    event: WatchEvent | RateEvent | CreateAccountEvent | None,
    ratings: list[dict],
    watches: dict[tuple[int, str], dict],
    user_ids: set[int],
    movie_ids: set[str],
    counters: dict[str, int],
) -> None:
    if event is None:
        counters["other"] += 1
        return
    if isinstance(event, WatchEvent):
        counters["watch"] += 1
        user_ids.add(event.user_id)
        movie_ids.add(event.movie_id)
        key = (event.user_id, event.movie_id)
        row = watches.get(key)
        if row is None:
            watches[key] = {
                "user_id": event.user_id,
                "movie_id": event.movie_id,
                "max_minute": event.minute,
                "n_events": 1,
                "first_ts": event.timestamp,
                "last_ts": event.timestamp,
            }
        else:
            row["n_events"] += 1
            if event.minute > row["max_minute"]:
                row["max_minute"] = event.minute
            if event.timestamp < row["first_ts"]:
                row["first_ts"] = event.timestamp
            if event.timestamp > row["last_ts"]:
                row["last_ts"] = event.timestamp
        return
    if isinstance(event, RateEvent):
        counters["rate"] += 1
        if event.rating < MIN_RATING or event.rating > MAX_RATING:
            counters["bad_rating"] += 1
            return
        user_ids.add(event.user_id)
        movie_ids.add(event.movie_id)
        ratings.append(
            {
                "user_id": event.user_id,
                "movie_id": event.movie_id,
                "rating": event.rating,
                "timestamp": event.timestamp,
            }
        )
        return
    if isinstance(event, CreateAccountEvent):
        counters["create"] += 1
        user_ids.add(event.user_id)


def consume_events(
    max_events: int,
    recent: bool,
    topic: str,
    bootstrap: str,
    windows: int = 1,
) -> tuple[list[dict], dict[tuple[int, str], dict], set[int], set[str], dict]:
    """Consume up to `max_events` Kafka messages.

    `windows` > 1 reads several slices spaced across the retained log so the
    same users can accumulate history (a single tail slice is only a few hours
    of traffic and almost every user has one movie).
    """
    consumer = KafkaConsumer(
        bootstrap_servers=bootstrap,
        enable_auto_commit=False,
        max_poll_records=5000,
        fetch_max_bytes=10 * 1024 * 1024,
        consumer_timeout_ms=15000,
        request_timeout_ms=30000,
    )
    partitions = consumer.partitions_for_topic(topic)
    if not partitions:
        consumer.close()
        raise RuntimeError(
            f"Topic {topic!r} not found at {bootstrap}. "
            "Is the SSH tunnel running? See README.md."
        )

    tps = [TopicPartition(topic, p) for p in sorted(partitions)]
    consumer.assign(tps)
    begin = consumer.beginning_offsets(tps)
    end = consumer.end_offsets(tps)
    total_available = sum(end[tp] - begin[tp] for tp in tps)

    n_windows = max(1, windows)
    if recent and n_windows == 1:
        starts = [
            {tp: max(begin[tp], end[tp] - (max_events // max(len(tps), 1) + 1)) for tp in tps}
        ]
    elif not recent and n_windows == 1:
        starts = [{tp: begin[tp] for tp in tps}]
    else:
        # Evenly spaced slices, including a tail slice.
        starts = []
        for w in range(n_windows):
            frac = w / max(n_windows - 1, 1)
            starts.append(
                {
                    tp: begin[tp]
                    + int((end[tp] - begin[tp] - 1) * frac)
                    for tp in tps
                }
            )

    ratings: list[dict] = []
    watches: dict[tuple[int, str], dict] = {}
    user_ids: set[int] = set()
    movie_ids: set[str] = set()
    counters = {"watch": 0, "rate": 0, "create": 0, "other": 0, "bad_rating": 0}

    per_window = max(1, max_events // n_windows)
    pbar = tqdm(total=max_events, desc="kafka", unit="evt")
    n = 0
    t0 = time.time()
    try:
        for window_idx, origin in enumerate(starts):
            for tp, offset in origin.items():
                lo, hi = begin[tp], end[tp]
                consumer.seek(tp, min(max(offset, lo), max(hi - 1, lo)))
            taken = 0
            idle = 0
            window_t0 = time.time()
            window_budget_s = float(os.environ.get("I2_WINDOW_SECONDS", "45"))
            while n < max_events and taken < per_window:
                if time.time() - window_t0 > window_budget_s:
                    break
                batch = consumer.poll(timeout_ms=4000)
                batch = consumer.poll(timeout_ms=4000)
                if not batch:
                    idle += 1
                    if idle >= 2:
                        break
                    continue
                idle = 0
                for _tp, messages in batch.items():
                    for msg in messages:
                        if n >= max_events or taken >= per_window:
                            break
                        n += 1
                        taken += 1
                        pbar.update(1)
                        _ingest_event(
                            parse_line(_decode(msg.value)),
                            ratings,
                            watches,
                            user_ids,
                            movie_ids,
                            counters,
                        )
            pbar.set_postfix(window=f"{window_idx + 1}/{n_windows}")
    finally:
        pbar.close()
        consumer.close()

    stats = {
        "events_scanned": n,
        "watch_events": counters["watch"],
        "rate_events": counters["rate"],
        "create_account_events": counters["create"],
        "other_events": counters["other"],
        "ratings_out_of_range": counters["bad_rating"],
        "unique_users_in_stream": len(user_ids),
        "unique_movies_in_stream": len(movie_ids),
        "unique_watch_pairs": len(watches),
        "elapsed_s": round(time.time() - t0, 2),
        "topic": topic,
        "bootstrap": bootstrap,
        "recent": recent,
        "windows": n_windows,
        "available_topic_messages": total_available,
        "begin_offsets": {str(tp.partition): begin[tp] for tp in tps},
        "end_offsets": {str(tp.partition): end[tp] for tp in tps},
    }
    return ratings, watches, user_ids, movie_ids, stats


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_sample(ratings: list[dict], movies: list[dict], users: list[dict]) -> None:
    """Tiny fixtures so parsers/tests can run without Kafka."""
    _write_csv(
        SAMPLE_DIR / "ratings.csv",
        ratings[:80],
        ["user_id", "movie_id", "rating", "timestamp"],
    )
    _write_jsonl(SAMPLE_DIR / "movies.jsonl", movies[:30])
    described = [u for u in users if u.get("self_description_likes")][:10]
    _write_jsonl(SAMPLE_DIR / "users.jsonl", described or users[:10])


def collect(max_events: int, recent: bool, skip_metadata: bool, windows: int = 1) -> None:
    _ensure_data_dir()
    print(
        f"Collecting up to {max_events} events from {KAFKA_TOPIC} "
        f"at {KAFKA_BOOTSTRAP} (recent={recent}, windows={windows})"
    )
    ratings, watches, user_ids, movie_ids, stats = consume_events(
        max_events=max_events,
        recent=recent,
        topic=KAFKA_TOPIC,
        bootstrap=KAFKA_BOOTSTRAP,
        windows=windows,
    )

    rating_rows = ratings
    watch_rows = list(watches.values())
    _write_csv(
        RATINGS_PATH,
        rating_rows,
        ["user_id", "movie_id", "rating", "timestamp"],
    )
    _write_csv(
        WATCHES_PATH,
        watch_rows,
        ["user_id", "movie_id", "max_minute", "n_events", "first_ts", "last_ts"],
    )

    movies: list[dict] = []
    users: list[dict] = []
    if not skip_metadata:
        print(f"Fetching metadata for {len(movie_ids)} movies and {len(user_ids)} users")
        movies = fetch_movies(sorted(movie_ids))
        users = fetch_users(sorted(user_ids))
        # Keep a compact movie record; drop bulky nested TMDB blobs we do not use.
        compact_movies = []
        for movie in movies:
            genres = movie.get("genres") or []
            genre_names = [
                g.get("name") for g in genres if isinstance(g, dict) and g.get("name")
            ]
            compact_movies.append(
                {
                    "id": movie.get("id"),
                    "title": movie.get("title") or movie.get("original_title"),
                    "original_title": movie.get("original_title"),
                    "overview": movie.get("overview") or "",
                    "tagline": movie.get("tagline") or "",
                    "genres": genre_names,
                    "runtime": movie.get("runtime"),
                    "release_date": movie.get("release_date"),
                    "original_language": movie.get("original_language"),
                    "imdb_id": movie.get("imdb_id"),
                    "tmdb_numeric_id": movie.get("id")
                    if isinstance(movie.get("id"), int)
                    else None,
                }
            )
        movies = [m for m in compact_movies if m.get("id")]
        _write_jsonl(MOVIES_PATH, movies)
        _write_jsonl(USERS_PATH, users)
    else:
        print("Skipping metadata API (--skip-metadata)")

    stats.update(
        {
            "n_ratings_written": len(rating_rows),
            "n_watches_written": len(watch_rows),
            "n_movies_fetched": len(movies),
            "n_users_fetched": len(users),
            "n_users_with_likes": sum(
                1 for u in users if u.get("self_description_likes")
            ),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "metadata_api": METADATA_API,
        }
    )
    COLLECTION_META_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    _write_sample(rating_rows, movies, users)
    print(json.dumps(stats, indent=2))
    print(f"Wrote {RATINGS_PATH}, {WATCHES_PATH}, {MOVIES_PATH}, {USERS_PATH}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect I2 Kafka + API data")
    parser.add_argument(
        "--max-events",
        type=int,
        default=DEFAULT_MAX_EVENTS,
        help="Stop after this many Kafka messages (default: %(default)s)",
    )
    parser.add_argument(
        "--recent",
        action="store_true",
        default=True,
        help="Read from the tail of the log (default)",
    )
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        help="Read from the earliest retained offset instead of the tail",
    )
    parser.add_argument(
        "--windows",
        type=int,
        default=12,
        help="Read this many slices spaced across the retained log "
        "(default: 12). Use 1 to read only the tail/head.",
    )
    parser.add_argument(
        "--skip-metadata",
        action="store_true",
        help="Only parse Kafka; do not call the metadata API",
    )
    args = parser.parse_args(argv)
    recent = not args.from_beginning
    try:
        collect(
            max_events=args.max_events,
            recent=recent,
            skip_metadata=args.skip_metadata,
            windows=args.windows,
        )
    except Exception as exc:  # noqa: BLE001 — surface a hint for the common failure
        print(f"Collection failed: {exc}", file=sys.stderr)
        print(
            "If this is a Kafka connection error, start the SSH tunnel:\n"
            "  ./scripts/start_kafka_tunnel.sh",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
