"""Re-measures peak training memory to match the team's standardized
definition (proposed by Sarah, 2026-09-27): maximum resident set size (RSS)
for one full training process, including data loading + model fitting, but
excluding serialization/pickling.

Single-process version: a background thread samples RSS every 20ms while
data loads and the model fits. Simpler and more reliable than the
subprocess-polling approach, at the cost of not fully isolating collaborative's
memory from content's (both run in this process; the thread is reset between
the two so each model's *reported* peak still starts from that model's own
data-loading step).
"""
from __future__ import annotations

import gc
import json
import os
import sys
import threading
import time

import psutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from adapters import load_interactions, load_movies  # noqa: E402

PROC = psutil.Process(os.getpid())


class PeakSampler:
    def __init__(self, interval_s: float = 0.02) -> None:
        self.interval_s = interval_s
        self.peak = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        while not self._stop.is_set():
            self.peak = max(self.peak, PROC.memory_info().rss)
            time.sleep(self.interval_s)

    def start(self) -> None:
        self.peak = PROC.memory_info().rss
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.peak = max(self.peak, PROC.memory_info().rss)
        return self.peak / 1e6


def measure_collaborative() -> dict:
    from src.models.collaborative import CollaborativeItemCF

    sampler = PeakSampler()
    sampler.start()
    t0 = time.perf_counter()
    train = load_interactions("data/v2/train.csv")
    CollaborativeItemCF().fit(train)
    train_s = time.perf_counter() - t0
    peak_mb = sampler.stop()
    return {"model": "collaborative", "peak_training_rss_mb": peak_mb, "train_time_s": train_s}


def measure_content() -> dict:
    from src.models.content import ContentTfidfRecommender

    sampler = PeakSampler()
    sampler.start()
    t0 = time.perf_counter()
    train = load_interactions("data/v2/train.csv")
    movies = load_movies("data/movies.csv")
    ContentTfidfRecommender().fit(train, movies)
    train_s = time.perf_counter() - t0
    peak_mb = sampler.stop()
    return {"model": "content", "peak_training_rss_mb": peak_mb, "train_time_s": train_s}


if __name__ == "__main__":
    results = {}
    print("Measuring collaborative...", flush=True)
    results["collaborative"] = measure_collaborative()
    print(f"  peak {results['collaborative']['peak_training_rss_mb']:.1f} MB, "
          f"{results['collaborative']['train_time_s']:.1f}s", flush=True)

    gc.collect()  # reduce (not eliminate) contamination from collaborative's
                  # still-resident-but-freed objects before measuring content
    print("Measuring content...", flush=True)
    results["content"] = measure_content()
    print(f"  peak {results['content']['peak_training_rss_mb']:.1f} MB, "
          f"{results['content']['train_time_s']:.1f}s", flush=True)

    with open("results_peak_memory.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Wrote results_peak_memory.json", flush=True)
