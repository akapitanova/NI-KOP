import copy
import math
import random
import Sat


class Solution:
    def __init__(self, problem):
        self.problem = problem
        self.evaluation = None
        self.weights_sum = None
        self.fitness = None
        self.is_sat = None
        self.is_sat_clauses = None

        self.init_solution()

    def init_solution(self):
        self.evaluation = []
        self.weights_sum = 0

        for i in range(self.problem.get_var_n()):
            self.evaluation.append(random.randint(0, 1))
            self.weights_sum += self.evaluation[i] * self.problem.get_weight(i)

        self.check_satis()
        self.count_fitness()

    def count_weights_sum(self):
        self.weights_sum = 0
        for i in range(self.problem.get_var_n()):
            self.weights_sum += self.evaluation[i] * self.problem.get_weight(i)

    def count_fitness(self):
        self.fitness = self.weights_sum * self.is_sat_clauses / self.problem.get_clauses_n()

    def change_eval(self, new_eval):
        self.evaluation = new_eval
        self.count_weights_sum()
        self.check_satis()
        self.count_fitness()

    def check_satis(self):
        self.is_sat_clauses = self.count_sat_clauses()

        if self.is_sat_clauses == self.problem.get_clauses_n():
            self.is_sat = True
        else:
            self.is_sat = False

    def count_sat_clauses(self):
        sat_clauses = 0
        for clause in self.problem.get_clauses():
            if clause.is_sat(self.evaluation):
                sat_clauses += 1
        return sat_clauses

    def get_eval(self):
        return self.evaluation

    def get_weights_sum(self):
        return self.weights_sum

    def get_fitness(self):
        return self.fitness

    def get_is_sat(self):
        return self.is_sat

    def get_is_sat_clauses(self):
        return self.is_sat_clauses


# ---------------------------------------------------------------
class SimAnnealSolver:

    def __init__(self, cooling_factor, take_rate, problem, end_temp_c=0.25, start_temp=None):
        self.cooling_factor = cooling_factor
        self.take_rate = take_rate
        self.problem = problem

        self.best_solution = Solution(problem)

        self.iters = -1
        self.end_temp_c = end_temp_c

        if start_temp:
            self.start_temp = start_temp
        else:self.set_start_temp()

        print(self.start_temp)

    # def better(self, new_solution, old_solution):
    #    return new_solution[0] > old_solution[0]

    def frozen(self, curr_temp):
        return curr_temp < self.start_temp * self.end_temp_c

    def better(self, new_solution, old_solution):
        old_sat = old_solution.get_is_sat()
        new_sat = new_solution.get_is_sat()

        if old_sat and not new_sat:
            return False

        if not old_sat and new_sat:
            return True

        if not old_sat and not new_sat:
            old_sat_n = old_solution.get_is_sat_clauses()
            new_sat_n = new_solution.get_is_sat_clauses()
            if old_sat_n != new_sat_n:
                return new_sat_n > old_sat_n

        return new_solution.get_weights_sum() > old_solution.get_weights_sum()

    def get_next(self, curr_solution):
        next_solution = copy.deepcopy(curr_solution)
        bit_to_flip = random.randint(0, self.problem.var_n - 1)

        next_eval = next_solution.get_eval()
        if next_eval[bit_to_flip] == 0:
            next_eval[bit_to_flip] = 1
        else:
            next_eval[bit_to_flip] = 0

        next_solution.change_eval(next_eval)
        return next_solution

    def relative_error(self, opt_weight_sum, sol_weights_sum):
        if opt_weight_sum == 0:
            return 0
        return abs((opt_weight_sum - sol_weights_sum) / opt_weight_sum)

    def optimize(self, opt, out=False):
        results = []
        curr_temp = self.start_temp
        curr_solution = copy.deepcopy(self.best_solution)
        total_iter = 0

        if out:
            print(f'total_iter {total_iter}')
            print(f'best_solution weight {self.best_solution.get_weights_sum()}')
            print(f'curr_solution weight {curr_solution.get_weights_sum()}')
            print()

        while not self.frozen(curr_temp):
            inner = 0
            sol_taken = 0

            while not self.problem.equilibrium(inner):

                results.append((total_iter,
                                self.best_solution.get_weights_sum(),
                                self.best_solution.get_is_sat_clauses(),
                                curr_solution.get_weights_sum(),
                                curr_solution.get_is_sat_clauses(),
                                opt,
                                self.relative_error(opt, self.best_solution.get_weights_sum()),
                                self.relative_error(opt, curr_solution.get_weights_sum()),
                                self.relative_error(self.problem.get_clauses_n(), self.best_solution.get_is_sat_clauses()),
                                self.relative_error(self.problem.get_clauses_n(), curr_solution.get_is_sat_clauses())
                                )
                               )

                new_solution = self.get_next(curr_solution)

                if self.better(new_solution, curr_solution):
                    if self.better(new_solution, self.best_solution):
                        self.best_solution = new_solution
                    curr_solution = new_solution
                    sol_taken += 1
                else:
                    if curr_solution.get_weights_sum() < new_solution.get_weights_sum():
                        delta = curr_solution.get_weights_sum() - new_solution.get_weights_sum()
                    else:
                        delta = new_solution.get_weights_sum() - curr_solution.get_weights_sum()
                    # print(f'delta {delta}')
                    # print(f'curr_temp {curr_temp}')

                    rnd = random.random()
                    # print(f'rnd {rnd}')
                    if rnd < math.e ** (delta / curr_temp):
                        curr_solution = new_solution
                inner += 1

                if out:
                    print(f'total_iter {total_iter}')
                    print(f'best_solution weight {self.best_solution.get_weights_sum()}')
                    print(f'curr_solution weight {curr_solution.get_weights_sum()}')
                    print()

                inner += 1
                total_iter += 1

            if sol_taken / inner < self.take_rate:
                print('take rate')
                break
            curr_temp = curr_temp * self.cooling_factor

        self.iters = total_iter
        return self.best_solution, results

    def get_best_solution(self):
        return self.best_solution

    def get_start_temp(self):
        return self.start_temp

    def set_start_temp(self, start_temp=None):
        if not start_temp:
            self.start_temp = self.problem.get_weights_sum() / self.problem.get_var_n()
        else:
            self.start_temp = start_temp

    def set_cooling_factor(self, cooling_factor):
        self.cooling_factor = cooling_factor

    def set_take_rate(self, take_rate):
        self.take_rate = take_rate

    def get_iters(self):
        return self.iters
