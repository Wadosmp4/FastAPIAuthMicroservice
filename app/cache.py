from aioredis import Redis
from app.config import settings

redis_conn = Redis(host=settings.REDIS_HOST,
                   port=settings.REDIS_PORT,
                   decode_responses=True,
                   password=settings.REDIS_PASSWORD)
