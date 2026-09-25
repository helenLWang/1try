"""Adapt the shared v2 snapshot (movielog-v2/) into the column names the I2
models (ported from ../1try_repo/src/models/) expect.

Column mapping, per DATA_GUIDE.md section 4:
  data/v2/train.csv   user_id,movie_id,timestamp,minutes_watched
                       -> interactions: user_id(int), movie_id(str),
                          rating(float, = minutes_watched), timestamp
  data/movies.csv      movie_id,title,genres,release_date,runtime,overview,tagline
                       -> movies: id(str), genres(list[str]), tagline, overview
                          (genres is '|'-separated in the CSV, not JSON)
  data/users.csv       user_id,age,occupation,gender,likes,dislikes
                       -> users: user_id(int), self_description_likes,
                          self_description_dislikes (cold_start.py's expected names)
"""
from __future__ import annotations

import pandas as pd


def load_interactions(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["user_id"] = df["user_id"].astype(int)
    df["movie_id"] = df["movie_id"].astype(str)
    # Engagement weight, per DATA_GUIDE.md: "train.minutes_watched to weight
    # by engagement" (the alternative, np.ones for binary, is not used here).
    df["rating"] = df["minutes_watched"].astype(float)
    return df


def load_movies(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"movie_id": "id"})
    df["id"] = df["id"].astype(str)
    df["genres"] = df["genres"].fillna("").apply(
        lambda s: [g for g in str(s).split("|") if g]
    )
    df["overview"] = df["overview"].fillna("")
    df["tagline"] = df["tagline"].fillna("")
    return df


def load_users(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["user_id"] = df["user_id"].astype(int)
    df = df.rename(
        columns={"likes": "self_description_likes", "dislikes": "self_description_dislikes"}
    )
    return df
