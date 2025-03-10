import os
import sys
import timeit
import csv
import pandas as pd

from Sat import *
from SimAnneal import *

from matplotlib import pyplot as plt
from functools import partial


def parser(dataset, file):
    with open(DATA_PATH + dataset + file) as f:
        for line in f.readlines():
            line = line.split()

            if line[0] == 'c':
                continue
            if line[0] == 'p':
                sat = SAT(int(line[2]), int(line[3]))
            if line[-1] == '0':
                if line[0] == 'w':
                    weights = line[1:-1]
                    sat.set_weights([int(i) for i in weights])

                    weights_sum = 0
                    for weight in weights:
                        weights_sum += int(weight)

                    sat.set_weights_sum(weights_sum)
                else:
                    clause = line[:-1]
                    x = int(clause[0])
                    y = int(clause[1])
                    z = int(clause[2])
                    sat.add_clause(x, y, z)
    return sat


def load_opt(path):
    opt = {}
    with open(path) as f:
        for line in f:
            line = line.split()
            # opt["w" + line[0] + '.mwcnf'] = (int(line[1]), [int(i) for i in line[2:-1]])
            opt[line[0] + '.mwcnf'] = (int(line[1]), [int(i) for i in line[2:-1]])
    return opt


def save_results(path, file_name, results, time):
    path_csv = f'{path}{file_name}-B{BOUND}-ST{TEMP}-ETC{END_TEMP_C}-CF{COOL_FACT}-TR{TAKE_RATE}.csv'
    path_time = f'{path}{file_name}-B{BOUND}-ST{TEMP}-ETC{END_TEMP_C}-CF{COOL_FACT}-TR{TAKE_RATE}_time'
    with open(path_csv, 'w') as f:
        csv_out = csv.writer(f)
        csv_out.writerow(['total_iter',
                          'weights_sum_best',
                          'is_sat_clauses_best',
                          'weights_sum_curr',
                          'is_sat_clauses_curr',
                          'opt',
                          'rel_err_weights_best',
                          'rel_err_weights_curr',
                          'rel_err_clauses_best',
                          'rel_err_clauses_curr'])

        for result in results:
            csv_out.writerow(result)

    with open(path_time, 'w') as f:
        f.write(str(time[0]))


def plot(results):
    df = pd.DataFrame(results)
    df.columns = ['iter', 'weights_sum', 'is_sat_clauses']
    df.index = df['iter']


def run(solver, results, opt, out_info):
    best_solution, res = solver.optimize(opt, out_info)
    results += res
    print(f'best solution {best_solution.get_weights_sum()}, {best_solution.get_eval()}')
    print(f'is satisfied {best_solution.get_is_sat()}')


def run_file(dataset_name, file_name, opt, repeats, out_info, res):
    sat = parser(dataset_name, file_name)

    bound = BOUND
    cool_fact = COOL_FACT
    take_rate = TAKE_RATE
    end_temp_c = END_TEMP_C
    start_temp = TEMP

    sat.set_eq_bound(bound)

    solver = SimAnnealSolver(cool_fact, take_rate, sat, end_temp_c)

    sum_res = 0
    for i in range(repeats):
        results = []
        print(f'opt {opt[file_name]}')
        time = timeit.Timer(partial(run, solver, results, opt[file_name][0], out_info)).repeat(1, 1)
        print(f'time {time}')
        sum_res += solver.best_solution.get_weights_sum()
        solver.best_solution.init_solution()
        save_results(RES_PATH + RES_DIR_PATH, file_name.split('.')[0], results, time)
        res.append((solver.relative_error(opt[file_name][0], solver.best_solution.get_weights_sum()),
                    solver.relative_error(solver.problem.get_clauses_n(), solver.best_solution.get_is_sat_clauses()),
                    time[0]
                    ))
    print(f'avg res {sum_res / repeats}')


def run_directory(dataset_name, opt_name, repeats, out_info):
    files = os.listdir(DATA_PATH + dataset_name)
    opt = load_opt(opt_name)
    res = []
    for file_name in files:
        print()
        print('------------------------------------------------')
        print(file_name)
        run_file(dataset_name, file_name, opt, repeats, out_info, res)
    save_res(RES_PATH + RES_DIR_PATH, res)


def save_res(path, res):
    path_csv = f'{path}results.csv'
    with open(path_csv, 'w') as f:
        csv_out = csv.writer(f)
        csv_out.writerow(['rel_err_weights',
                          'rel_err_clauses',
                          'time'])

        for result in res:
            csv_out.writerow(result)



BOUND = 250
TEMP = 1000
END_TEMP_C = 0.25
COOL_FACT = 0.95
TAKE_RATE = 0.02

DATA_PATH = '../data/'
RES_PATH = '../res/'
RES_DIR_PATH = ''

if __name__ == '__main__':
    args = sys.argv
    BOUND = float(args[1])
    TEMP = float(args[2])
    END_TEMP_C = float(args[3])
    COOL_FACT = float(args[4])
    TAKE_RATE = float(args[5])

    # dataset = 'wuf20-71/wuf20-71-M-s/'
    dir_path = 'whitebox/inst/'

    RES_DIR_PATH = f'{dir_path}B{BOUND}-ST{TEMP}-ETC{END_TEMP_C}-CF{COOL_FACT}-TR{TAKE_RATE}/'



    file = 'wuf20-010.mwcnf'
    # optimum cesta
    opt_path = DATA_PATH + 'whitebox/opt.dat'
    # je jeden konkretni file nebo vsechny ze zadane dir
    more = True
    # vypis
    out = False

    # vypocet na jednom vybranem souboru
    if not more:
        opt = load_opt(opt_path)
        run_file(dir_path, file, opt, 1, out)

    # pruchod skrz vsechny soubory
    else:
        RES_DIR_PATH = f'{dir_path}B{BOUND}-ST{TEMP}-ETC{END_TEMP_C}-CF{COOL_FACT}-TR{TAKE_RATE}/'
        if os.path.exists(RES_PATH + RES_DIR_PATH):
            RES_DIR_PATH = RES_DIR_PATH[0:-1] + '_1/'
        if not os.path.exists(RES_PATH + RES_DIR_PATH):
            os.mkdir(RES_PATH + RES_DIR_PATH)
        run_directory(dir_path, opt_path, 1, out)
