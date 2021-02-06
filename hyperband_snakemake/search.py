import math
from typing import List, Optional


class HbSearch:
    def __init__(
            self, smax: int, eta: int, unit_time: float, folds: Optional[int],
            repetitions: Optional[int], guaranteed_budget: int,
            allowed_brackets: List[int], last_stage: Optional[int]) -> None:
        R = eta**smax
        B = R * (smax + 1)

        self.smax, self.eta, self.R, self.B = smax, eta, R, B
        self.unit_time, self.folds, self.repetitions = unit_time, folds, repetitions
        self.guaranteed_budget = guaranteed_budget
        self.last_stage = last_stage

        self.brackets = [
            HbBracket(
                eta=eta,
                s=s,
                n=math.ceil(B * eta**s / (R * (s + 1))),
                r=R / eta**s,
                last_stage=last_stage,
                search=self,
            )
            for s in range(smax, -1, -1)
            if not allowed_brackets or smax - s in allowed_brackets
        ]

    def cost(self) -> float:
        return sum(b.cost() for b in self.brackets)

    def pprint(self) -> None:
        print('Hyperband Search - η: {} S: {} R: {} B: {}  (cost: {:.2f})'.format(
            self.eta, self.smax, self.R, self.B, self.cost()
        ))
        for i, each in enumerate(self.brackets):
            each.pprint(i)


class HbBracket:
    def __init__(self, eta: int, s: int, n: int, r: int,
                 last_stage: Optional[int], search: HbSearch):
        self.s, self.n, self.r, self.eta = s, n, r, eta

        if last_stage is None:
            last_stage = s

        self.search = search
        self.stages = [
            HbStage(
                n=math.floor(n / eta**i),
                r=r * eta**i,
                bracket=self,
                search=search,
            )
            for i in range(0, last_stage + 1)
        ]

    def cost(self) -> float:
        return sum(s.cost() for s in self.stages)

    def pprint(self, idx: int) -> None:
        print(f'  Bracket {idx} (cost: {self.cost():.2f})')
        for i, each in enumerate(self.stages):
            each.pprint(i)


class HbStage:
    def __init__(self, n: int, r: int, bracket: HbBracket, search: HbSearch):
        self.n, self.r = n, r
        self.bracket, self.search = bracket, search

    def cost(self) -> float:
        return self.search.unit_time * self.n * (self.r + self.search.guaranteed_budget)

    def pprint(self, idx: int) -> None:
        print('    Stage {} - {} configurations each with budget {} (cost: {:.2f})'.format(
            idx, self.n, self.search.guaranteed_budget + self.r, self.cost()
        ))
