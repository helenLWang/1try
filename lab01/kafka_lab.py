"""Lab 1: Kafka producer, consumer, and seek demo.

Run after the SSH tunnel is up:
    ssh -L 9092:localhost:9092 tunnel@128.2.220.123 -NT

Then:
    python kafka_lab.py
"""

from __future__ import annotations

import os
from datetime import datetime
from json import dumps, loads
from random import randint
from time import sleep
from typing import Any, Dict, List

from kafka import KafkaConsumer, KafkaProducer, TopicPartition

# Unique topic so we do not collide with other students.
ANDREW_ID = "helenlwang"
TOPIC = f"lab01-{ANDREW_ID}"
BOOTSTRAP = ["localhost:9092"]
NUM_MESSAGES = 20


def make_city_data(city: str, temperature_f: int) -> Dict[str, Any]:
    return {
        "city": city,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature_f": temperature_f,
    }


def run_producer() -> List[int]:
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda m: dumps(m).encode("utf-8"),
    )
    cities = [
        ("Pittsburgh", 64),
        ("Shanghai", 82),
        ("San Francisco", 68),
    ]
    print("Writing to Kafka Broker")
    assigned_offsets: List[int] = []
    for _ in range(NUM_MESSAGES):
        city, temperature_f = cities[randint(0, len(cities) - 1)]
        data = make_city_data(city, temperature_f)
        future = producer.send(topic=TOPIC, value=data)
        assigned_offsets.append(future.get(timeout=10).offset)
        sleep(0.5)
    producer.flush()
    producer.close()
    print(f"Data written to topic: {TOPIC}")
    print(f"Offsets assigned in this run: {assigned_offsets[0]} .. {assigned_offsets[-1]}")
    return assigned_offsets


def run_consumer(max_messages: int = NUM_MESSAGES) -> None:
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kafka_log.csv")
    if os.path.exists(log_path):
        os.remove(log_path)

    # New group_id each run so auto_offset_reset='earliest' actually rewinds.
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        auto_commit_interval_ms=1000,
        consumer_timeout_ms=5000,
        group_id=f"{TOPIC}-consumer-{datetime.now().strftime('%H%M%S')}",
    )
    print("Reading Kafka Broker")
    count = 0
    with open(log_path, "a", encoding="utf-8") as log_file:
        for message in consumer:
            message_str = message.value.decode("utf-8")
            message_dict = loads(message_str)
            print(f"offset {message.offset}: {message_dict}")
            log_file.write(message_str + "\n")
            count += 1
            if count >= max_messages:
                break
    consumer.close()
    print(f"Wrote {count} rows to {log_path}")


def run_seek_demo() -> None:
    explorer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP,
        enable_auto_commit=False,
        group_id=None,
    )
    tp = TopicPartition(TOPIC, 0)
    explorer.assign([tp])

    first_offset = explorer.beginning_offsets([tp])[tp]
    next_offset = explorer.end_offsets([tp])[tp]
    print(f"readable offsets: {first_offset} .. {next_offset - 1}\n")

    def read_from(offset: int, n: int = 2) -> None:
        explorer.seek(tp, offset)
        seen = 0
        while seen < n:
            batch = explorer.poll(timeout_ms=2000, max_records=n - seen)
            if not batch:
                break
            for record in batch[tp]:
                print(f"  offset {record.offset}: {loads(record.value.decode('utf-8'))}")
                seen += 1

    start_offsets = [
        first_offset,
        (first_offset + next_offset) // 2,
        max(first_offset, next_offset - 2),
    ]
    for start in start_offsets:
        print(f"--- seek to offset {start} ---")
        read_from(start, 2)

    explorer.close()
    print(
        "\nTA note: auto_offset_reset can reach the first offset ('earliest') "
        "and the high watermark ('latest'). The midpoint needs seek()."
    )


if __name__ == "__main__":
    print(f"Topic: {TOPIC}")
    print("\n========== 1. PRODUCER ==========")
    run_producer()
    print("\n========== 2. CONSUMER ==========")
    run_consumer()
    print("\n========== 3. SEEK DEMO ==========")
    run_seek_demo()
