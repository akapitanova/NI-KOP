from Sat import Sat


# -----------------------------------------
def relative_error(ref_price, solution_price):
    if ref_price == 0:
        return 0
    return abs((ref_price - solution_price) / ref_price)


# -----------------------------------------
def load_data(path, file):
    clauses = []
    weights = []
    v = 0

    filename = file.split('.')

    with open(path + "/" + file) as f:
        for line in f:
            line = line.split()
            if line[0] == '%':
                break
            if line[0] == 'p':
                v = line[2]
                next(f)
            if line[-1] == '0':
                if line[0] == 'w':
                    weights = line[1:-1]
                else:
                    clause = line[:-1]
                    clauses.append([int(i) for i in clause])

    id = filename[0]
    if id[-2:] == "-A":
        id = id[:-2]
    print(id)
    return Sat(id, int(v), clauses, [int(i) for i in weights])


# -----------------------------------------
def load_ref(path, file):
    ref = {}
    with open(path + "/" + file) as f:
        for line in f:
            line = line.split()
            ref["w" + line[0]] = (int(line[1]), [int(i) for i in line[2:-1]])
    return ref


# -----------------------------------------
def save_data(path, file, data):
    with open(path + "/" + file, 'w') as f:
        for i in data:
            f.write(str(i).replace('.', ','))
            f.write('\n')
            
