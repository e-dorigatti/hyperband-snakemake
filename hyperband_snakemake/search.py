import math


class HbStage:
    def __init__(self, n, r, bracket, search):
        self.n, self.r = n, r
        self.bracket, self.search = bracket, search

    def cost(self):
        return self.search.unit_time * self.n * (self.r + self.search.guaranteed_budget)

    def pprint(self, idx):
        print('    Stage {} - {} configurations each with budget {} (cost: {:.2f})'.format(
            idx, self.n, self.search.guaranteed_budget + self.r, self.cost()
        ))


class HbBracket:
    def __init__(self, eta, s, n, r, search):
        self.s, self.n, self.r, self.eta = s, n, r, eta
        self.search = search
        self.stages = [
            HbStage(
                n=math.floor(n / eta**i),
                r=r * eta**i,
                bracket=self,
                search=search,
            )
            for i in range(0, s + 1)
        ]

    def cost(self):
        return sum(s.cost() for s in self.stages)

    def pprint(self, idx):
        print(f'  Bracket {idx} (cost: {self.cost():.2f})')
        for i, each in enumerate(self.stages):
            each.pprint(i)


class HbSearch:
    def __init__(self, smax, eta, unit_time, folds, repetitions, guaranteed_budget):
        R = eta**smax
        B = R * (smax + 1)

        self.smax, self.eta, self.R, self.B = smax, eta, R, B
        self.unit_time, self.folds, self.repetitions = unit_time, folds, repetitions
        self.guaranteed_budget = guaranteed_budget

        self.brackets = [
            HbBracket(
                eta=eta,
                s=s,
                n=math.ceil(B * eta**s / (R * (s + 1))),
                r=R / eta**s,
                search=self,
            )
            for s in range(smax, -1, -1)
        ]

    def cost(self):
        return sum(b.cost() for b in self.brackets)

    def pprint(self):
        print(f'Hyperband Search (cost: {self.cost():.2f})')
        for i, each in enumerate(self.brackets):
            each.pprint(i)
