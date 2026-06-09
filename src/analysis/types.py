from typing import TypeAlias

from corpus.models import BaseModel

ChordDistribution: TypeAlias = dict[str, dict[str, int]]


class ChordStat(BaseModel):
    chord: str
    count: int
    total: int
    percentage: float
