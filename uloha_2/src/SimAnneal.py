import random
import math

from Sat import SatState, SatSolution
from Data import relative_error


# -----------------------------------------
class SimAnneal:
    def __init__(self, instance, cooling_coef, min_temp, init_temp, inner_loop):
        self.instance = instance
        self.cooling_coef = cooling_coef
        self.min_temp = min_temp
        self.init_temp = init_temp
        self.init_temp = self.gen_init_temp()
        # print(self.init_temp)
        self.inner_loop = inner_loop

    def solve(self, ref, init_state=None):
        # init_state = self.gen_random_state()
        state = SatState(init_state.sat, init_state.binary)
        best = SatState(init_state.sat, init_state.binary)
        temp = self.init_temp
        solution_count = 0
        step = 0
        attempt = 1
        max_attempts = 4
        values = []
        values2 = []

        while max_attempts > attempt and self.bounds(best):
            while self.frozen(temp):
                values.append((step, self.cost(best), self.cost(state), ref, relative_error(ref, self.cost(best)),
                               relative_error(ref, self.cost(state))))
                values2.append((step, best.satisfied_nc, state.satisfied_nc, state.sat.nc,
                                relative_error(ref, self.cost(best)), relative_error(ref, self.cost(state))))

                for i in range(0, self.inner_loop):
                    new = self.random_neighbour(state)
                    if not self.bounds(new):
                        solution_count += 1
                    state = self.try_state(state, new, temp)
                    if self.better(state, best):
                        best = SatState(state.sat, state.binary)
                temp = self.cool(temp)
                step += 1
            attempt += 1
            temp = self.init_temp
        return self.solution(best, solution_count), values, values2

    def frozen(self, temp):
        return temp > self.min_temp

    def cool(self, temp):
        return temp * self.cooling_coef

    def try_state(self, state, new, temp):
        if self.better(new, state):
            return new
        q = self.cost_difference(state, new)
        if random.uniform(0, 1) < math.exp(-q / temp):
            return new
        return state

    def gen_random_state(self):
        return SatState(self.instance, [random.randint(0, 1) for i in range(0, self.instance.n)])

    def gen_init_temp(self, s=100):
        S = []

        for i in range(0, s):
            state = self.gen_random_state()
            neighbour = self.random_neighbour(state)

            if (self.better(state, neighbour)):
                S.append(self.cost_difference(state, neighbour))
            else:
                S.append(self.cost_difference(neighbour, state))

        tn = -(sum(S) / len(S)) / math.log(0.9)
        return int(tn)

    def solution(self, state, solution_count):
        return SatSolution(state, solution_count)

    def cost(self, state):
        return state.price

    def random_neighbour(self, state):
        if len(state.unsatisfied_variables) > 0:
            random_var = random.choice(state.unsatisfied_variables)
            i = abs(random_var) - 1
        else:
            i = random.randint(0, state.sat.n - 1)
        new = list(state.binary)
        new[i] = 1 - new[i]
        return SatState(state.sat, new)

    def better(self, x, y):
        return self.cost_difference(x, y) > 0

    def cost_difference(self, x, y):
        if x.satisfied_nc == y.satisfied_nc:
            return self.cost(x) - self.cost(y)
        return x.satisfied_nc - y.satisfied_nc
        # converted = self.convert(x.satisfied_nc, 0, x.sat.n, 0, sum(x.sat.weights)) - self.convert(y.satisfied_nc, 0, y.sat.n, 0, sum(y.sat.weights))
        # return converted

    def bounds(self, state):
        return not state.is_satisfied()

    def convert(self, old, old_min, old_max, new_min, new_max):
        new = (((old - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min
        return new