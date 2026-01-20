from __future__ import annotations
from rq import Worker, Queue, Connection
import redis
from app.core.settings import settings

listen = ["default"]
redis_conn = redis.from_url(settings.REDIS_URL)

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work()
