"""
drp.ai — worker/celery_app.py
Celery application configuration using Upstash Redis as broker and backend.
"""

from celery import Celery
import os

import ssl

REDIS_URL = os.getenv(
    "REDIS_URL",
    "rediss://default:gQAAAAAAAXNqAAIgcDI1ODdmNzBjYTA3Yjc0ZWE5ODJhMjBiZjcwN2I1YjMyMg@real-cricket-95082.upstash.io:6379"
)

celery_app = Celery(
    "drp_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Results expire after 1 hour — enough for polling
    result_expires=3600,

    # Upstash requires SSL
    broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
    redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},

    # Don't prefetch too many tasks — keeps memory low
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # Timezone
    timezone="Asia/Kolkata",
    enable_utc=True,
)