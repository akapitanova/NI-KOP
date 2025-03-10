import random


# -----------------------------------------
def gen_weights(n):
    new_weights = []
    for i in range(0, n):
        new_weights.append(random.randint(0, 100))
    return new_weights


class Sat:
    def __init__(self, id, n, clauses, weights=None):
        self.id = id
        self.n = n
        self.nc = len(clauses)
        self.clauses = clauses

        if weights is None or len(weights) == 0:
            self.weights = gen_weights(n)
        else:
            self.weights = weights

    def __str__(self):
        return "%s %s %s %s %s" % (self.id, self.n, self.nc, self.clauses, self.weights)

    __repr__ = __str__


# -----------------------------------------
class SatSolution:
    def __init__(self, best, count):
        self.best = best
        self.count = count

    def __str__(self):
        return "%s %s" % (self.best.is_satisfied(), self.best)

    __repr__ = __str__


# -----------------------------------------
def evaluate_clause(clause, binary):
    for i in clause:
        position = abs(i) - 1;
        sign = i > 0
        if sign == binary[position]:
            return True
    return False


class SatState:
    def __init__(self, sat, binary=None):
        self.sat = sat
        if binary is None:
            self.binary = [0] * sat.n
            self.unsatisfied_variables = [i + 1 for i in range(0, self.sat.n)]
            self.price = 0
            self.satisfied_nc = 0
        else:
            self.binary = binary
            self.unsatisfied_variables = []
            self.price = self.get_price()
            self.satisfied_nc = self.get_satisfied_nc()

    def __str__(self):
        return "%s %s %s 0" % (self.sat.id[1:], self.price, str(self.get_variables()).strip('[]').replace(',', ''))

    __repr__ = __str__

    def is_satisfied(self):
        return self.satisfied_nc == self.sat.nc

    def get_variables(self):
        variables = []
        for i in range(0, self.sat.n):
            variables.append(i + 1)
            if self.binary[i] == 0:
                variables[i] = -variables[i]
        return variables

    def get_price(self):
        sum_price = 0
        for i in range(0, self.sat.n):
            sum_price += self.binary[i] * self.sat.weights[i]
        return sum_price

    def get_satisfied_nc(self):
        count = 0
        variables = []
        for clause in self.sat.clauses:
            if evaluate_clause(clause, self.binary):
                count += 1
            else:
                variables.extend(clause)
        self.unsatisfied_variables = list(set(variables))
        return count
