"""Tiny local server for Le's M1 candidate.

    python -m src.m1_server
    curl http://127.0.0.1:8082/recommend/9375

The team can later put this same handler on the course VM.
Needs a trained artifact: python -m src.train
"""

from __future__ import annotations

from flask import Flask, Response

from src.m1_recommend import recommend_line

app = Flask(__name__)


@app.get("/recommend/<int:user_id>")
def recommend_route(user_id: int) -> Response:
    body = recommend_line(user_id)
    return Response(body, mimetype="text/plain")


def main() -> None:
    # preload models so the first request is not the slow one
    recommend_line(0)
    app.run(host="0.0.0.0", port=8082, threaded=True)


if __name__ == "__main__":
    main()
