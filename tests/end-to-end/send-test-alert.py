#!/usr/bin/python3

# Based on https://gist.github.com/carinadigital/fd2960fdccd77dbdabc849656c43a070

import json
import logging
import os
import random
import time

from datetime import datetime, timezone

import requests


def get_random_int():
    return random.randint(0,10000)


def get_current_time():
    local_time = datetime.now(timezone.utc).astimezone()
    return local_time.isoformat()


def generate_post_data(name, status, startsAt="", endsAt=""):
    template = {
        "status": status,
        "labels": {
            "alertname": name,
            "service": "my-service",
            "severity":"warning",
            "instance": f"{name}.example.net",
            "namespace": "foo-bar",
            "label_costcentre": "FOO"
        },
        "annotations": {
            "summary": "High latency is high!"
        },
        "generatorURL": f"http://local-example-alert/{name}"
    }
    if startsAt:
        template["startsAt"] = startsAt
    if endsAt:
        template["endsAt"] = endsAt
    return [template]

if __name__ == "__main__":
    ALERTMANAGER_HOST = os.getenv("ALERTMANAGER_HOST", "localhost")
    ALERTMANAGER_PORT = os.getenv("ALERTMANAGER_PORT", "9093")
    logging.basicConfig(
        format='%(asctime)s %(message)s',
        level=logging.INFO,
        datefmt='%m-%d-%Y %H:%M:%S%z'
    )

    name = f"dummy-alert-{get_random_int()}"
    url = f"http://{ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}/api/v1/alerts"

    logging.info(f"Firing alert {name}")
    start_time = get_current_time()
    post_data = generate_post_data(name, status="firing", startsAt=start_time)
    r = requests.post(url=url, data=json.dumps(post_data))
    print(r.status_code == 200)

    time.sleep(10)

    logging.info(f"Sending resolved {name}")
    post_data = generate_post_data(name, status="firing", startsAt=start_time, endsAt=get_current_time())
    r = requests.post(url=url, data=json.dumps(post_data))
    assert r.status_code == 200
