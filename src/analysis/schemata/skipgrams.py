import heapq
import itertools
import math
from typing import Callable, Generic, Iterator, Optional, Tuple, TypeVar

import numpy as np
from pydantic import BaseModel



# Ggeneric type variable for musical events (e.g., Note objects)
T = TypeVar('T')

class Skipgram (BaseModel, Generic[T]):
    cost: float
    contents: list[T]

class PathNode(Generic[T]):
    __slots__ = ['event', 'parent', 'length', 'cost']
    
    def __init__(self, event: T, parent: Optional['PathNode'], cost: float):
        self.event = event
        self.parent = parent
        self.length = (parent.length + 1) if parent else 1
        self.cost = cost

    def to_list(self) -> list[T]:
        """Reconstructs the path only when needed (O(N))."""
        res = [self.event]
        curr = self.parent
        while curr:
            res.append(curr.event)
            curr = curr.parent
        return res[::-1]
    
    def get_contents_iterator(self) -> Iterator[T]:
        """ Traverses the linked list without allocating a new list """
        curr = self
        stack = []
        while curr:
            stack.append(curr.event)
            curr = curr.parent
        return reversed(stack)



def skipgram (input: Iterator[T], k: float, n: int, c: Callable[[T, T], float], p: Callable[[PathNode], bool] | None = None) -> Iterator[Skipgram]:
    """General skipgram implementation after Finkensiep, Neuwirth, Rohrmeier 2018.

    Args:
        input: input stream
        k: upper bound on the allowed skip
        n: length of the generated skipgrams
        c: cost function (should always return positive costs)
        p: predicate functions. applied to all prefixes. if they dont apply, they are thrown out.

    Returns:
     Stream of found skipgrams
    """


    counter = itertools.count()
    pfxs: list[Tuple[int, int, PathNode]] = []
    output: list[Tuple[int, int, Skipgram]] = []

    for event_id, event in enumerate(input):
        # filter out impossible skipgrams
        pfxs = [ (id, tb, node) for id, tb, node in pfxs if node.cost + c(node.event, event) <= k]

        # return completed - oldest element has to be first in pfxs, since they are added in order of input
        while len(pfxs) > 0 and len(output) > 0 and output[0][0] < pfxs[0][0]: 
            yield heapq.heappop(output)[2]

        # get new possible skipgrams (combinations, plus just the new element (added here for edgecase of n==1))
        ext = [ (id, next(counter), PathNode(event, node, node.cost + c(node.event, event))) for id, tb, node in pfxs ]
        ext.append((event_id, next(counter), PathNode(event, None, 0.0)))

        # add new skipgrams / add them to output if complete
        for event_id, tb, node in ext:
            if p and not p(node): continue

            if node.length == n:
                sg = Skipgram(cost=node.cost, contents=node.to_list())
                heapq.heappush(output, (event_id, tb, sg))
            else:
                pfxs.append((event_id, tb, node))

    # returns last outputs in order
    while len(output) > 0:
        yield heapq.heappop(output)[2] 

        

