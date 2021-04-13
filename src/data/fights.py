from dataclasses import dataclass


@dataclass
class Fight:
    name: str
    difficulty: int
    startTime: int
    endTime: int
    encounterID: int
