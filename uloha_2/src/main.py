import sys
import timeit
import os
import pandas as pd

from matplotlib import pyplot as plt
from functools import partial
from Sat import SatState
from SimAnneal import SimAnneal
from Data import *

DATA_PATH = '../data'
RES_PATH = '../res'


# -----------------------------------------
def sa_plot(plot, id, t, c, i, ver, ylabel):
    test = pd.DataFrame(plot)
    test.columns = ['step', "best", "current", "optimum", 'best error', 'avg error']
    test = test[1:-1]
    test = test[::-1]
    test.index = test['step']
    test = test.drop('step', axis=1)
    pie = test.plot(y=["best", "current", "optimum"])
    # pie.invert_xaxis()
    pie.set_ylabel(ylabel)
    pie.set_xlabel("Krok algoritmu")
    fig = pie.get_figure()
    fig.savefig("../plot/" + str(id) + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + str(ver) + ".png")
    plt.close('all')


# -----------------------------------------
def solve(sat, ref, solutions, errors, cooling_coef, min_temp, init_temp, inner_loop):
    ref_price, ref_satisfied = ref[sat.id]
    print(ref_price)
    sa = SimAnneal(sat, cooling_coef, min_temp, init_temp, inner_loop)

    solution, plot, plot2 = sa.solve(ref_price, SatState(sat))
    # print(solution)
    solutions.append(solution)
    # errors.append((0, relative_error(sat.nc, solution.best.satisfied_nc)))
    print(solution.best.price)
    errors.append((relative_error(ref_price, solution.best.price), relative_error(sat.nc, solution.best.satisfied_nc)))

    sa_plot(plot, sat.id, init_temp, cooling_coef, inner_loop, "weight", "Váha řešení")
    sa_plot(plot2, sat.id, init_temp, cooling_coef, inner_loop, "clause", "Splněné klauzule")


# -----------------------------------------
def run(path, files, repeat):
    solutions = []
    times = []
    errors = []
    avg_err_0 = []
    avg_err_1 = []

    t = 1000
    c = 0.975
    i = 50

    ref = load_ref(DATA_PATH, path + "-opt.dat")

    for file in files:
        sat = load_data(DATA_PATH + '/' + path, file)
        if sat.id in ref:
            time = timeit.Timer(partial(solve, sat, ref, solutions, errors, c, 0.1, t, i)).repeat(repeat, 1)
            times.extend(time)
            # avg_err_0.append(sum([j[0] for j in errors])/len(errors))
            # avg_err_1.append(sum([j[1] for j in errors])/len(errors))
            # errors = []
            save_data(RES_PATH, path + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_err_0.txt", avg_err_0)
            save_data(RES_PATH, path + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_err_1.txt", avg_err_1)
    save_data(RES_PATH, path + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_err_1.txt", avg_err_1)
    save_data(RES_PATH, path + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_err.txt", (
        max([j[0] for j in errors]), max([j[1] for j in errors]), sum([j[0] for j in errors]) / len(errors),
        sum([j[1] for j in errors]) / len(errors)))
    save_data(RES_PATH, path + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_tim.txt",
              (max(times), sum(times) / len(times)))

    errors = []
    times = []


# -----------------------------------------
def run_one(path, file, repeat):
    solutions = []
    times = []
    errors = []
    avg_err_1 = []

    t = 1000
    c = 0.980
    i = 100

    ref = load_ref(DATA_PATH, path + "-opt.dat")
    # ref = None

    sat = load_data(DATA_PATH + '/' + path, file)
    # if sat.id in ref:
    time = timeit.Timer(partial(solve, sat, ref, solutions, errors, c, 0.1, t, i)).repeat(repeat, 1)
    times.extend(time)
    save_data(RES_PATH, path + "_" + file + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_err_1.txt",
              [j[1] for j in errors])
    save_data(RES_PATH, path + "-" + str(sat.id) + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_err.txt",
              (errors, sum([j[0] for j in errors]) / len(errors), sum([j[1] for j in errors]) / len(errors)))
    save_data(RES_PATH, path + "-" + str(sat.id) + "_t" + str(t) + "_c" + str(c) + "_i" + str(i) + "_tim.txt",
              (times, sum(times) / len(times)))
    errors = []
    times = []


# -----------------------------------------
def main():
    repeat = 1
    one = True
    dataset = sys.argv[1]

    if one:
        file = "wuf20-010.mwcnf"
        run_one(dataset, file, repeat)
    else:
        files = os.listdir(DATA_PATH + "/" + dataset)
        run(dataset, files, repeat)


# -----------------------------------------
if __name__ == "__main__":
    main()
