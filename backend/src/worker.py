import logging,time
from pathlib import Path
import redis
from src.config.settings import REDIS_URL
from src.services.run import execute
from src.utils.repository import run_migrations
logging.basicConfig(level=logging.INFO)
def main():
    run_migrations(); client=redis.Redis.from_url(REDIS_URL)
    while True:
        Path("/tmp/worker-heartbeat").write_text(str(time.time()))
        try:
            item=client.blpop("coverage-map:jobs", timeout=3)
            if item: execute(item[1].decode())
        except Exception:
            logging.exception("worker failure");time.sleep(2)
if __name__=="__main__": main()
