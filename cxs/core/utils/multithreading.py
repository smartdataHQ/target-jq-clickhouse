import os

import dotenv

dotenv.load_dotenv()

INITIAL_CONCURRENT_TASKS = os.getenv("INITIAL_CONCURRENT_TASKS", 15)
MAX_CONCURRENT_TASKS = os.getenv("MAX_CONCURRENT_TASKS", 25)
MIN_CONCURRENT_TASKS = os.getenv("MIN_CONCURRENT_TASKS", 10)


class AdaptiveConcurrency:
    def __init__(
        self,
        initial: int = INITIAL_CONCURRENT_TASKS,
        maximum: int = MAX_CONCURRENT_TASKS,
        minimum: int = MIN_CONCURRENT_TASKS,
    ):
        self.current = initial
        self.max = maximum
        self.min = minimum

    def increase(self):
        self.current = min(self.current * 2, self.max)

    def decrease(self):
        self.current = max(self.current // 2, self.min)
