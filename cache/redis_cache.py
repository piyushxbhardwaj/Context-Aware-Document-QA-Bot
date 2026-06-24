import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Interface for query/response caching.
    Tries to import the redis library and connect to a Redis instance.
    If Redis is unavailable or the library is not installed, it falls back
    gracefully to an in-memory dictionary to keep the application functional.
    """
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, ttl: int = 3600):
        self.host = host
        self.port = port
        self.db = db
        self.ttl = ttl
        self.redis_client = None
        self._memory_cache = {}

        try:
            import redis
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_timeout=1.0,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis cache at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(
                f"Redis unavailable or not installed. "
                f"Falling back to In-Memory dictionary cache. Details: {e}"
            )
            self.redis_client = None

    def get(self, key: str) -> Optional[str]:
        """Retrieves a value from the cache. Returns None on cache miss."""
        if self.redis_client:
            try:
                return self.redis_client.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Falling back to memory cache.")
                
        return self._memory_cache.get(key)

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Stores a value in the cache with a time-to-live (TTL) in seconds."""
        expire_ttl = ttl or self.ttl
        if self.redis_client:
            try:
                self.redis_client.setex(key, expire_ttl, value)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}. Falling back to memory cache.")

        self._memory_cache[key] = value
        return True

    def clear(self) -> bool:
        """Flushes all stored entries from the cache."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                return True
            except Exception as e:
                logger.warning(f"Redis flush failed: {e}. Clearing memory cache.")

        self._memory_cache.clear()
        return True
