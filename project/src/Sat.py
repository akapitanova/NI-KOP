import random


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Clause:
    def __init__(self, x, y, z):
        self.variables = (x, y, z)

    def is_sat(self, x):
        for i in self.variables:
            satis = x[i-1] if i > 0 else not x[-i-1]
            if satis:
                return True
        return False


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def cool(curr_temp, cooling_factor):
    return curr_temp * cooling_factor


def random_permutation(size):
    perm = []

    for i in range(0, size):
        perm[i] = i

    random.shuffle(perm)
    return perm


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SAT:

    def __init__(self, var_n, clauses_n):
        self.eq_bound = 50
        self.clauses = set()
        self.clauses_n = clauses_n
        self.var_n = var_n
        self.weights = []
        self.weights_sum = 0

    def get_weights_sum(self):
        return self.weights_sum

    def equilibrium(self, n):
        return n > self.eq_bound

    def add_clause(self, x, y, z):
        self.clauses.add(Clause(x, y, z))

    def is_sat(self, x):
        for clause in self.clauses:
            if not clause.is_sat(x):
                return False
            return True

    def set_weights(self, w):
        self.weights = w

    def set_weights_sum(self, weights_sum):
        self.weights_sum = weights_sum

    def get_size(self):
        return self.var_n

    def get_clauses_n(self):
        return self.clauses_n

    def get_var_n(self):
        return self.var_n

    def set_eq_bound(self, eq_bound):
        self.eq_bound = eq_bound

    def get_weight(self, n):
        if n > len(self.weights) - 1:
            print('out of range')
        return self.weights[n]

    def get_clauses(self):
        return self.clauses
