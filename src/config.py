"""Shared paths and hyperparameters.

All knobs used for training and evaluation live here so the run is
reproducible: change a value, re-run `python -m src.train`, and the
artifacts and logs will record the new setting.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Paths (repo root = parent of this package)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("I2_DATA_DIR", ROOT / "data"))
ARTIFACT_DIR = Path(os.environ.get("I2_ARTIFACT_DIR", ROOT / "artifacts"))
SAMPLE_DIR = DATA_DIR / "sample"
MODEL_DIR = ARTIFACT_DIR / "models"

RATINGS_PATH = DATA_DIR / "ratings.csv"
WATCHES_PATH = DATA_DIR / "watches.csv"
USERS_PATH = DATA_DIR / "users.jsonl"
MOVIES_PATH = DATA_DIR / "movies.jsonl"
COLLECTION_META_PATH = DATA_DIR / "collection_meta.json"
INTERACTIONS_PATH = DATA_DIR / "interactions.csv"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"
TRAIN_LOG_PATH = ARTIFACT_DIR / "train_log.json"

API_KEY_FILE = ROOT / "api.key"

# ---------------------------------------------------------------------------
# Kafka / metadata API
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "movielog1")
METADATA_API = os.environ.get(
    "METADATA_API", "http://128.2.220.123:8080"
).rstrip("/")
KAFKA_SERVER_IP = os.environ.get("KAFKA_SERVER_IP", "128.2.220.123")
SSH_TUNNEL_USER = os.environ.get("SSH_TUNNEL_USER", "tunnel")

# Default collection budget. 5e6 events is a few minutes of consume time and
# typically yields tens of thousands of ratings without writing a huge dump.
DEFAULT_MAX_EVENTS = int(os.environ.get("I2_MAX_EVENTS", "5000000"))
API_BATCH_SIZE = 200  # hard limit of the course API
API_SLEEP_S = float(os.environ.get("I2_API_SLEEP", "0.08"))
API_MAX_RETRIES = 4

# ---------------------------------------------------------------------------
# Interaction construction
# ---------------------------------------------------------------------------
# Drop watch-only events shorter than this; they are usually "clicked and left".
MIN_WATCH_MINUTES = 3
# Implicit rating when the user watched but never rated.
IMPLICIT_BASE = 5.0
IMPLICIT_SCALE = 4.0  # added as progress -> 1.0, so implicit is in ~5-9
MIN_RATING = 1
MAX_RATING = 10

# ---------------------------------------------------------------------------
# Train / eval split
# ---------------------------------------------------------------------------
TEST_HOLD_FRACTION = 0.2
MIN_INTERACTIONS_FOR_SPLIT = 2
TOP_K = 20

# ---------------------------------------------------------------------------
# Collaborative filtering (Truncated SVD on biased residuals)
# ---------------------------------------------------------------------------
CF_N_COMPONENTS = 50
CF_MIN_USER_INTERACTIONS = 2
CF_MIN_MOVIE_INTERACTIONS = 2

# ---------------------------------------------------------------------------
# Content-based filtering
# ---------------------------------------------------------------------------
TFIDF_MAX_FEATURES = 4000
TFIDF_NGRAM = (1, 2)
TFIDF_MIN_DF = 2

# ---------------------------------------------------------------------------
# Cold-start / LLM
# ---------------------------------------------------------------------------
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")  # optional, e.g. OpenRouter
LLM_TEMPERATURE = 0.2
LLM_MAX_CANDIDATES = 80
COLD_START_TOP_K = 20
