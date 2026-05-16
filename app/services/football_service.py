import time
import random
from typing import Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cachetools import TTLCache
from threading import Lock

from app.config import Config
from app.utils.logger import logger

class FootballService:
    BASE_URL = "https://api.football-data.org/v4/"
    
    _state_lock      = Lock()
    _last_call_time  = 0.0
    _block_until     = 0.0
    _fail_count      = 0
    _requests_left   = 10      # free tier limit per minute
    MIN_INTERVAL     = 6.5
    FAIL_THRESHOLD   = 3
    COOLDOWN_429     = 900
    COOLDOWN_FAIL    = 300

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = TTLCache(maxsize=100, ttl=3600)
        self.lock = Lock()

        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=10))
        session.headers.update({
            "X-Auth-Token": api_key,
            "User-Agent": "FootballBot/1.0 (LINE chatbot; EPL alerts)",
        })
        self.session = session

    def _wait_for_rate_limit(self):
        with self._state_lock:
            now    = time.time()
            jitter = random.uniform(0.5, 2.5)
            gap    = (self.MIN_INTERVAL + jitter) - (now - self._last_call_time)
            if gap > 0:
                time.sleep(gap)
            self._last_call_time = time.time()

    def _is_blocked(self) -> bool:
        with self._state_lock:
            return time.time() < self._block_until

    def _record_429(self):
        with self._state_lock:
            self._block_until = time.time() + self.COOLDOWN_429
            self._fail_count  = 0
            logger.warning(f"⛔ 429 received — pausing {self.COOLDOWN_429}s")

    def _record_failure(self):
        with self._state_lock:
            self._fail_count += 1
            if self._fail_count >= self.FAIL_THRESHOLD:
                self._block_until = time.time() + self.COOLDOWN_FAIL
                self._fail_count  = 0
                logger.warning(f"⛔ {self.FAIL_THRESHOLD} failures — pausing {self.COOLDOWN_FAIL}s")

    def _record_success(self, response: requests.Response):
        with self._state_lock:
            self._fail_count = 0
            remaining = response.headers.get("X-Requests-Available-Minute")
            if remaining is not None:
                self._requests_left = int(remaining)
                if self._requests_left <= 2:
                    self._last_call_time = time.time() + 30 

    def fetch(self, endpoint: str, ttl: int = 60) -> Optional[Any]:
        cache_key = endpoint
        with self.lock:
            if cache_key in self.cache:
                return self.cache[cache_key]

        if self._is_blocked():
            logger.info("⏳ Rate-limit block active")
            return None

        self._wait_for_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        try:
            res = self.session.get(url, timeout=(5, 15))

            if res.status_code == 429:
                self._record_429()
                return None

            if not res.ok:
                logger.warning(f"API {res.status_code}: {endpoint}")
                self._record_failure()
                return None

            self._record_success(res)
            data = res.json()

            if ttl > 0:
                with self.lock:
                    self.cache.__setitem__(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Fetch error [{endpoint}]: {e}")
            self._record_failure()
            return None

svc = FootballService(Config.FOOTBALL_API_KEY)
