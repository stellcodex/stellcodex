from redis import Redis
from rq import Queue

from .config import settings


redis_conn = Redis.from_url(settings.redis_url)


def get_queue(name: str) -> Queue:
    return Queue(name, connection=redis_conn)
