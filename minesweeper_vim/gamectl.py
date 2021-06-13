from dataclasses import dataclass, field
from time import sleep, time
from typing import Callable, List


def time_ms() -> int:
    return int(time() * 1000)


@dataclass
class Timer:
    callback: Callable[..., None]
    interval: int
    deadline_ms: int = 0

    def __post_init__(self) -> None:
        self.deadline_ms = time_ms() + self.interval


@dataclass
class GameCtl:
    timers: List[Timer] = field(default_factory=list)

    def register_callback(
        self, callback: Callable[..., None], interval: int = 100
    ) -> None:
        self.timers.append(Timer(callback, interval))

    def ioloop(self) -> None:
        while True:
            sleep(0.1)
            for timer in self.timers:
                if time_ms() > timer.deadline_ms:
                    timer.callback()
                    timer.deadline_ms += timer.interval
